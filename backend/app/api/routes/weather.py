from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Response
from backend.app.schemas.weather import WeatherCondition, WeatherErrorResponse
from backend.app.tools.geo_service import geo_service
from backend.app.tools.weather_api import weather_tool
from backend.app.core.exceptions import WeatherServiceException
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "",
    response_model=WeatherCondition,
    responses={
        404: {"model": WeatherErrorResponse, "description": "Location could not be resolved"},
        504: {"model": WeatherErrorResponse, "description": "Weather API timed out"},
        502: {"model": WeatherErrorResponse, "description": "Upstream Weather API error"},
        422: {"model": WeatherErrorResponse, "description": "Malformed response schema"},
    }
)
@router.get(
    "/current",
    response_model=WeatherCondition,
    responses={
        404: {"model": WeatherErrorResponse, "description": "Location could not be resolved"},
        504: {"model": WeatherErrorResponse, "description": "Weather API timed out"},
        502: {"model": WeatherErrorResponse, "description": "Upstream Weather API error"},
        422: {"model": WeatherErrorResponse, "description": "Malformed response schema"},
    }
)
async def get_weather_forecast(
    location: str = Query(..., description="Target location name or city", min_length=1),
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD")
):
    """Fetches real meteorological forecast data for a specified location and date.
    
    Returns structured WeatherCondition on success, or a distinct structured error
    if the location cannot be geocoded or the meteorological provider fails.
    Never returns fabricated or hallucinated values.
    """
    clean_location = location.strip()
    if not clean_location:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "error_code": "INVALID_INPUT",
                "message": "Location parameter cannot be empty.",
                "location_searched": location,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    try:
        # Step 1: Geocode location
        geo = await geo_service.geocode(clean_location)

        # Step 2: Fetch forecast
        forecast = await weather_tool.get_forecast(geo, target_date)
        return forecast

    except WeatherServiceException as exc:
        logger.warning(f"Weather query failed for '{clean_location}': [{exc.error_code}] {exc.message}")
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail,
                "location_searched": clean_location,
                "retries_attempted": exc.retries_attempted,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_forecast for '{clean_location}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred while retrieving weather: {str(e)}",
                "location_searched": clean_location,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
