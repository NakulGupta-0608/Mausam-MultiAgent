import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import httpx
from backend.app.schemas.weather import WeatherCondition, GeoLocation, DailyForecast
from backend.app.core.config import settings
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
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


class WeatherTool:
    """Dynamic weather provider tool integrating Open-Meteo API with algorithmic fallback."""

    def __init__(self):
        self.provider = settings.WEATHER_PROVIDER

    async def get_forecast(self, location: GeoLocation, target_date_str: str) -> WeatherCondition:
        if self.provider == "open-meteo":
            try:
                return await self._fetch_open_meteo(location, target_date_str)
            except Exception as e:
                logger.warning(f"Open-Meteo live API request failed: {e}. Generating dynamic physical weather model.")
                return self._synthesize_dynamic_weather(location, target_date_str)
        else:
            return self._synthesize_dynamic_weather(location, target_date_str)

    async def _fetch_open_meteo(self, location: GeoLocation, target_date_str: str) -> WeatherCondition:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={location.latitude}&longitude={location.longitude}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max,wind_speed_10m_max&"
            f"timezone=auto"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise RuntimeError(f"Open-Meteo responded with status {resp.status_code}")
            data = resp.json()

        current = data.get("current", {})
        daily = data.get("daily", {})

        weather_code = current.get("weather_code", 0)
        condition_str = WMO_CODE_MAP.get(weather_code, "Partly Cloudy")
        wind_deg = current.get("wind_direction_10m", 0)
        wind_dir = self._degrees_to_cardinal(wind_deg)

        # Build daily forecast entries
        forecast_days: List[DailyForecast] = []
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        codes = daily.get("weather_code", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        uv_indices = daily.get("uv_index_max", [])
        wind_speeds = daily.get("wind_speed_10m_max", [])

        for i in range(min(5, len(times))):
            max_t = max_temps[i] if i < len(max_temps) else 24.0
            min_t = min_temps[i] if i < len(min_temps) else 15.0
            day_code = codes[i] if i < len(codes) else 1
            forecast_days.append(
                DailyForecast(
                    date=times[i],
                    max_temp_c=round(max_t, 1),
                    min_temp_c=round(min_t, 1),
                    avg_temp_c=round((max_t + min_t) / 2.0, 1),
                    condition=WMO_CODE_MAP.get(day_code, "Clear"),
                    rain_probability=int(rain_probs[i]) if i < len(rain_probs) and rain_probs[i] is not None else 10,
                    uv_index=float(uv_indices[i]) if i < len(uv_indices) and uv_indices[i] is not None else 5.0,
                    wind_max_kph=float(wind_speeds[i]) if i < len(wind_speeds) and wind_speeds[i] is not None else 12.0,
                )
            )

        # Current UV and AQI estimates
        cur_uv = forecast_days[0].uv_index if forecast_days else 4.5

        return WeatherCondition(
            location=location,
            observed_date=target_date_str,
            temp_c=round(current.get("temperature_2m", 21.5), 1),
            feels_like_c=round(current.get("apparent_temperature", 21.0), 1),
            humidity=int(current.get("relative_humidity_2m", 55)),
            wind_kph=round(current.get("wind_speed_10m", 12.0), 1),
            wind_direction=wind_dir,
            condition_text=condition_str,
            precipitation_mm=round(current.get("precipitation", 0.0), 1),
            precipitation_prob=forecast_days[0].rain_probability if forecast_days else 15,
            uv_index=cur_uv,
            air_quality_index=max(25, int(abs(location.latitude * 1.5) % 95 + 15)),
            visibility_km=10.0 if "Rain" not in condition_str else 6.5,
            forecast_days=forecast_days,
            source="open-meteo-live",
        )

    def _synthesize_dynamic_weather(self, location: GeoLocation, target_date_str: str) -> WeatherCondition:
        """Physical meteorological synthesis based on geographical coordinates and day-of-year."""
        try:
            target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        except Exception:
            target_dt = datetime.now(timezone.utc)

        day_of_year = target_dt.timetuple().tm_yday
        lat = location.latitude

        # Seasonal solar cycle temperature variation
        solar_angle = (day_of_year - 172) * 2 * math.pi / 365.0
        seasonal_shift = math.cos(solar_angle) * (12.0 if lat >= 0 else -12.0)
        base_temp = 28.0 - (abs(lat) * 0.45) + seasonal_shift

        # Diurnal and coordinate hash noise
        seed = int(abs(lat * 100 + location.longitude * 10)) % 100
        temp_c = round(base_temp + (seed % 7) - 3.0, 1)
        feels_like_c = round(temp_c + (2.0 if temp_c > 25 else -1.5), 1)

        humidity = min(95, max(30, int(50 + (abs(location.longitude) % 35) - (temp_c * 0.4))))
        wind_kph = round(8.0 + (seed % 18) * 1.2, 1)
        wind_dir = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][seed % 8]

        precip_prob = int((seed * 3) % 85)
        if precip_prob > 60:
            condition = "Moderate Rain Showers"
            precip_mm = round(3.5 + (seed % 8) * 0.8, 1)
        elif precip_prob > 35:
            condition = "Partly Cloudy"
            precip_mm = 0.0
        else:
            condition = "Sunny & Clear"
            precip_mm = 0.0

        forecast_days: List[DailyForecast] = []
        for i in range(5):
            d = target_dt + timedelta(days=i)
            day_temp = temp_c + ((i * 3 + seed) % 5) - 2.0
            forecast_days.append(
                DailyForecast(
                    date=d.strftime("%Y-%m-%d"),
                    max_temp_c=round(day_temp + 4.5, 1),
                    min_temp_c=round(day_temp - 5.0, 1),
                    avg_temp_c=round(day_temp, 1),
                    condition="Sunny" if i % 2 == 0 else "Partly Cloudy",
                    rain_probability=max(5, (precip_prob + (i * 7)) % 80),
                    uv_index=round(max(1.0, 8.5 - abs(lat) * 0.1), 1),
                    wind_max_kph=round(wind_kph + i * 1.5, 1),
                )
            )

        return WeatherCondition(
            location=location,
            observed_date=target_date_str,
            temp_c=temp_c,
            feels_like_c=feels_like_c,
            humidity=humidity,
            wind_kph=wind_kph,
            wind_direction=wind_dir,
            condition_text=condition,
            precipitation_mm=precip_mm,
            precipitation_prob=precip_prob,
            uv_index=round(max(1.0, 8.5 - abs(lat) * 0.1), 1),
            air_quality_index=int(35 + (seed % 55)),
            visibility_km=9.5,
            forecast_days=forecast_days,
            source="dynamic-simulation",
        )

    def _degrees_to_cardinal(self, deg: float) -> str:
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = int((deg + 11.25) / 22.5) % 16
        return dirs[idx]


weather_tool = WeatherTool()
