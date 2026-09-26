from typing import List, Optional, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Domain Weather Models
# ---------------------------------------------------------

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
    air_quality_index: int = Field(default=50, description="US AQI estimate")
    visibility_km: float = 10.0
    forecast_days: List[DailyForecast] = []
    source: str = "open-meteo-live"


class WeatherErrorResponse(BaseModel):
    error: bool = True
    error_code: str = Field(..., description="Distinct machine-readable error code")
    message: str = Field(..., description="Human-readable explanation of failure")
    detail: Optional[str] = None
    location_searched: Optional[str] = None
    retries_attempted: int = 0
    timestamp: str


# ---------------------------------------------------------
# Raw Upstream Open-Meteo API Schemas (Used for strict validation)
# ---------------------------------------------------------

class OpenMeteoGeoResult(BaseModel):
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin1: Optional[str] = None
    timezone: Optional[str] = "UTC"


class OpenMeteoGeoSearchResponse(BaseModel):
    results: Optional[List[OpenMeteoGeoResult]] = None
    generationtime_ms: Optional[float] = None


class OpenMeteoCurrent(BaseModel):
    time: str
    temperature_2m: float
    relative_humidity_2m: float
    apparent_temperature: float
    precipitation: float
    weather_code: int
    wind_speed_10m: float
    wind_direction_10m: float


class OpenMeteoDaily(BaseModel):
    time: List[str]
    weather_code: List[int]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    precipitation_probability_max: Optional[List[Optional[int]]] = None
    uv_index_max: Optional[List[Optional[float]]] = None
    wind_speed_10m_max: Optional[List[Optional[float]]] = None


class OpenMeteoForecastResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: Optional[str] = "UTC"
    current: OpenMeteoCurrent
    daily: OpenMeteoDaily
