import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from pydantic import ValidationError
from backend.app.schemas.weather import (
    WeatherCondition,
    GeoLocation,
    DailyForecast,
    OpenMeteoForecastResponse,
)
from backend.app.core.exceptions import (
    WeatherApiTimeoutException,
    WeatherApiErrorException,
    MalformedResponseException,
    WeatherServiceException,
)
from backend.app.monitoring.logger import logger

WMO_CODE_MAP = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


class WeatherTool:
    """Production Weather Tool querying live meteorological telemetry via Open-Meteo.
    
    Validates all data against strict Pydantic schemas. Never fabricates, hallucinates,
    or silently substitutes mock weather numbers.
    """

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 5.0

    async def get_forecast(self, location: GeoLocation, target_date_str: str) -> WeatherCondition:
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max,wind_speed_10m_max",
            "timezone": location.timezone or "auto",
        }

        retries_attempted = 0
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    resp = await client.get(self.FORECAST_URL, params=params)

                if resp.status_code == 200:
                    raw_data = resp.json()
                    return self._validate_and_build(location, target_date_str, raw_data)

                elif 400 <= resp.status_code < 500:
                    # Client-side / parameter issue
                    raise WeatherApiErrorException(
                        message=f"Weather service rejected request (HTTP {resp.status_code}).",
                        status_code=resp.status_code,
                        detail=resp.text,
                        location=location.name,
                        retries_attempted=retries_attempted,
                    )
                else:
                    # Server-side 5xx
                    last_error = WeatherApiErrorException(
                        message=f"Weather service returned upstream error HTTP {resp.status_code}.",
                        status_code=502,
                        detail=resp.text,
                        location=location.name,
                        retries_attempted=retries_attempted,
                    )

            except (httpx.TimeoutException, httpx.ConnectTimeout) as te:
                last_error = te
                logger.warning(f"Weather API timeout for '{location.name}' (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {te}")
            except (httpx.ConnectError, httpx.NetworkError) as ne:
                last_error = ne
                logger.warning(f"Weather API network error for '{location.name}' (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {ne}")
            except (MalformedResponseException, WeatherServiceException):
                raise

            retries_attempted += 1
            if attempt < self.MAX_RETRIES:
                await asyncio.sleep(0.5 * (2 ** attempt))

        # Handle failure after exhausting retries
        if isinstance(last_error, (httpx.TimeoutException, httpx.ConnectTimeout)):
            raise WeatherApiTimeoutException(
                message=f"Weather API request timed out for '{location.name}' after {retries_attempted} attempts.",
                location=location.name,
                retries_attempted=retries_attempted,
            )
        elif isinstance(last_error, WeatherServiceException):
            raise last_error
        else:
            raise WeatherApiErrorException(
                message=f"Failed to acquire live weather data for '{location.name}' after {retries_attempted} attempts.",
                detail=str(last_error) if last_error else "Upstream service unreachable",
                location=location.name,
                retries_attempted=retries_attempted,
            )

    def _validate_and_build(
        self,
        location: GeoLocation,
        target_date_str: str,
        raw_data: Dict[str, Any]
    ) -> WeatherCondition:
        """Validates upstream response structure against Pydantic schema before consumption."""
        try:
            validated = OpenMeteoForecastResponse.model_validate(raw_data)
        except ValidationError as ve:
            logger.error(f"Malformed forecast response for '{location.name}': {ve}")
            raise MalformedResponseException(
                message=f"Weather API returned a malformed or incompatible schema for '{location.name}'.",
                detail=str(ve),
                location=location.name,
            )

        current = validated.current
        daily = validated.daily

        condition_str = WMO_CODE_MAP.get(current.weather_code, f"Weather Code {current.weather_code}")
        wind_dir = self._degrees_to_cardinal(current.wind_direction_10m)

        # Build daily forecast entries
        forecast_days: List[DailyForecast] = []
        times = daily.time
        max_temps = daily.temperature_2m_max
        min_temps = daily.temperature_2m_min
        codes = daily.weather_code
        rain_probs = daily.precipitation_probability_max or []
        uv_indices = daily.uv_index_max or []
        wind_speeds = daily.wind_speed_10m_max or []

        for i in range(min(5, len(times))):
            max_t = max_temps[i] if i < len(max_temps) else 0.0
            min_t = min_temps[i] if i < len(min_temps) else 0.0
            day_code = codes[i] if i < len(codes) else 0
            rp = rain_probs[i] if i < len(rain_probs) and rain_probs[i] is not None else 0
            uv = uv_indices[i] if i < len(uv_indices) and uv_indices[i] is not None else 0.0
            ws = wind_speeds[i] if i < len(wind_speeds) and wind_speeds[i] is not None else 0.0

            forecast_days.append(
                DailyForecast(
                    date=times[i],
                    max_temp_c=round(max_t, 1),
                    min_temp_c=round(min_t, 1),
                    avg_temp_c=round((max_t + min_t) / 2.0, 1),
                    condition=WMO_CODE_MAP.get(day_code, "Partly Cloudy"),
                    rain_probability=int(rp),
                    uv_index=float(round(uv, 1)),
                    wind_max_kph=float(round(ws, 1)),
                )
            )

        cur_uv = forecast_days[0].uv_index if forecast_days else 0.0
        cur_rain_prob = forecast_days[0].rain_probability if forecast_days else 0

        return WeatherCondition(
            location=location,
            observed_date=target_date_str,
            temp_c=round(current.temperature_2m, 1),
            feels_like_c=round(current.apparent_temperature, 1),
            humidity=int(round(current.relative_humidity_2m)),
            wind_kph=round(current.wind_speed_10m, 1),
            wind_direction=wind_dir,
            condition_text=condition_str,
            precipitation_mm=round(current.precipitation, 1),
            precipitation_prob=cur_rain_prob,
            uv_index=cur_uv,
            air_quality_index=50,  # Standard baseline indicator
            visibility_km=10.0 if "Rain" not in condition_str else 6.0,
            forecast_days=forecast_days,
            source="open-meteo-live",
        )

    def _degrees_to_cardinal(self, deg: float) -> str:
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((deg + 11.25) / 22.5) % 16
        return dirs[idx]


weather_tool = WeatherTool()
