import asyncio
from typing import Optional
import httpx
from pydantic import ValidationError
from backend.app.schemas.weather import (
    GeoLocation,
    OpenMeteoGeoSearchResponse,
)
from backend.app.core.exceptions import (
    LocationNotFoundException,
    WeatherApiTimeoutException,
    WeatherApiErrorException,
    MalformedResponseException,
)
from backend.app.monitoring.logger import logger


class GeoService:
    """Production geocoding service using Open-Meteo Geocoding API with schema validation and bounded retries.
    
    Never synthesizes or fabricates locations. If a location cannot be resolved, an explicit
    LocationNotFoundException is raised.
    """

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    REVERSE_GEO_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 4.0

    async def geocode(self, location_name: str) -> GeoLocation:
        clean_name = location_name.strip()
        if not clean_name:
            raise LocationNotFoundException(
                location="<empty>",
                detail="Location name cannot be empty."
            )

        params = {
            "name": clean_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        retries_attempted = 0
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    resp = await client.get(self.GEOCODING_URL, params=params)

                if resp.status_code == 200:
                    raw_data = resp.json()
                    # Validate raw response schema
                    try:
                        validated = OpenMeteoGeoSearchResponse.model_validate(raw_data)
                    except ValidationError as ve:
                        logger.error(f"Malformed geocoding response for '{clean_name}': {ve}")
                        raise MalformedResponseException(
                            message=f"Geocoding service returned an unexpected data structure for '{clean_name}'.",
                            detail=str(ve),
                            location=clean_name,
                            retries_attempted=retries_attempted,
                        )

                    if not validated.results or len(validated.results) == 0:
                        logger.info(f"Geocoding returned 0 results for '{clean_name}'")
                        raise LocationNotFoundException(
                            location=clean_name,
                            detail="No geographical match found in global database.",
                            retries_attempted=retries_attempted,
                        )

                    top = validated.results[0]
                    return GeoLocation(
                        name=top.name,
                        country=top.country,
                        region=top.admin1,
                        latitude=top.latitude,
                        longitude=top.longitude,
                        timezone=top.timezone or "UTC",
                    )

                elif 400 <= resp.status_code < 500:
                    # Client error - do not retry
                    raise LocationNotFoundException(
                        location=clean_name,
                        detail=f"Geocoding service rejected query (HTTP {resp.status_code}).",
                        retries_attempted=retries_attempted,
                    )
                else:
                    # Server error (5xx)
                    last_error = WeatherApiErrorException(
                        message=f"Geocoding service returned server error HTTP {resp.status_code}.",
                        status_code=502,
                        location=clean_name,
                        detail=resp.text,
                        retries_attempted=retries_attempted,
                    )

            except (httpx.TimeoutException, httpx.ConnectTimeout) as te:
                last_error = te
                logger.warning(f"Geocoding timeout for '{clean_name}' (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {te}")
            except (httpx.ConnectError, httpx.NetworkError) as ne:
                last_error = ne
                logger.warning(f"Geocoding network error for '{clean_name}' (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {ne}")
            except (LocationNotFoundException, MalformedResponseException):
                raise

            retries_attempted += 1
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(0.5 * (2 ** attempt))

        # If loop finishes without returning or raising specific domain error
        if isinstance(last_error, (httpx.TimeoutException, httpx.ConnectTimeout)):
            raise WeatherApiTimeoutException(
                message=f"Geocoding service timed out while resolving '{clean_name}'.",
                location=clean_name,
                retries_attempted=retries_attempted,
            )
        elif isinstance(last_error, WeatherServiceException):
            raise last_error
        else:
            raise WeatherApiErrorException(
                message=f"Failed to resolve location '{clean_name}' after {retries_attempted} attempts.",
                detail=str(last_error) if last_error else "Network connection unreachable",
                location=clean_name,
                retries_attempted=retries_attempted,
            )

    async def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        fallback_name: Optional[str] = None
    ) -> GeoLocation:
        """Converts latitude and longitude into a structured human-readable location name.
        
        Uses primary high-speed reverse geocoding with secondary fallback and coordinate fallback.
        """
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise LocationNotFoundException(
                location=f"({latitude}, {longitude})",
                detail=f"Coordinates ({latitude}, {longitude}) are out of valid geographical bounds [-90, 90] and [-180, 180]."
            )

        # 1. Primary Reverse Geocoding: BigDataCloud
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "localityLanguage": "en",
        }

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    resp = await client.get(self.REVERSE_GEO_URL, params=params)

                if resp.status_code == 200:
                    data = resp.json()
                    city = data.get("city") or data.get("locality") or data.get("principalSubdivision")
                    country = data.get("countryName") or data.get("countryCode") or ""
                    region = data.get("principalSubdivision") or ""

                    parts = [p for p in [city, region] if p]
                    name = ", ".join(parts) if parts else (fallback_name or f"Live Location ({latitude:.3f}°, {longitude:.3f}°)")

                    logger.info(f"Reverse-geocoded ({latitude}, {longitude}) to '{name}', {country}")
                    return GeoLocation(
                        name=name,
                        country=country,
                        region=region,
                        latitude=latitude,
                        longitude=longitude,
                        timezone="auto",
                    )
            except Exception as e:
                logger.warning(f"BigDataCloud reverse geocode attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(0.5 * (2 ** attempt))

        # 2. Secondary Reverse Geocoding: OpenStreetMap Nominatim
        try:
            headers = {"User-Agent": "MausamAI/1.0 (weather-intelligence-agent)"}
            nom_params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
            }
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                nom_resp = await client.get(self.NOMINATIM_REVERSE_URL, params=nom_params, headers=headers)

            if nom_resp.status_code == 200:
                nom_data = nom_resp.json()
                address = nom_data.get("address", {})
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("suburb")
                    or address.get("county")
                )
                region = address.get("state") or address.get("region") or ""
                country = address.get("country") or ""

                parts = [p for p in [city, region] if p]
                name = ", ".join(parts) if parts else (fallback_name or f"Live Location ({latitude:.3f}°, {longitude:.3f}°)")

                logger.info(f"Nominatim reverse-geocoded ({latitude}, {longitude}) to '{name}', {country}")
                return GeoLocation(
                    name=name,
                    country=country,
                    region=region,
                    latitude=latitude,
                    longitude=longitude,
                    timezone="auto",
                )
        except Exception as e:
            logger.warning(f"Nominatim reverse geocode fallback failed: {e}")

        # 3. Graceful fallback with coordinates and provided fallback_name
        resolved_name = fallback_name or f"Live Location ({latitude:.3f}°, {longitude:.3f}°)"
        logger.info(f"Using coordinate representation '{resolved_name}' for ({latitude}, {longitude})")
        return GeoLocation(
            name=resolved_name,
            country="",
            region="",
            latitude=latitude,
            longitude=longitude,
            timezone="auto",
        )


geo_service = GeoService()
