from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.schemas.weather import WeatherCondition
from backend.app.tools.geo_service import geo_service
from backend.app.tools.weather_api import weather_tool
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/current", response_model=WeatherCondition)
async def get_current_weather(
    location: str = Query(..., description="Target location name or coordinates"),
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD")
):
    try:
        target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        geo = await geo_service.geocode(location)
        forecast = await weather_tool.get_forecast(geo, target_date)
        return forecast
    except Exception as e:
        logger.error(f"Error fetching weather for '{location}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")
