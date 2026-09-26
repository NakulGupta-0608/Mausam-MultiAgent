from typing import List, Optional
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    name: str
    country: Optional[str] = None
    region: Optional[str] = None
    latitude: float
    longitude: float
    timezone: Optional[str] = "UTC"


class DailyForecast(BaseModel):
    date: str
    max_temp_c: float
    min_temp_c: float
    avg_temp_c: float
    condition: str
    rain_probability: int
    uv_index: float
    wind_max_kph: float


class WeatherCondition(BaseModel):
    location: GeoLocation
    observed_date: str
    temp_c: float
    feels_like_c: float
    humidity: int
    wind_kph: float
    wind_direction: str
    condition_text: str
    precipitation_mm: float
    precipitation_prob: int
    uv_index: float
    air_quality_index: int = Field(default=50, description="US AQI standard")
    visibility_km: float = 10.0
    forecast_days: List[DailyForecast] = []
    source: str = "open-meteo"
