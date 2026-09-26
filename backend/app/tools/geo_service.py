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


geo_service = GeoService()
