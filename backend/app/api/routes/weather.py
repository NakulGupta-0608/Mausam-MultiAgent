from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.schemas.weather import WeatherCondition, WeatherErrorResponse, GeoLocation
from backend.app.tools.geo_service import geo_service
from backend.app.tools.weather_api import weather_tool
from backend.app.core.exceptions import WeatherServiceException
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get(
    "/reverse-geocode",
    response_model=GeoLocation,
    responses={
        404: {"model": WeatherErrorResponse, "description": "Coordinates could not be resolved"},
        504: {"model": WeatherErrorResponse, "description": "Reverse geocoding timed out"},
        502: {"model": WeatherErrorResponse, "description": "Upstream service error"},
    }
)
async def reverse_geocode_coordinates(
    latitude: float = Query(..., description="GPS latitude [-90, 90]", ge=-90.0, le=90.0),
    longitude: float = Query(..., description="GPS longitude [-180, 180]", ge=-180.0, le=180.0),
):
    """Converts GPS latitude and longitude into a readable location name.
    
    Used for automatic live location detection from the browser Geolocation API.
    """
    try:
        geo = await geo_service.reverse_geocode(latitude, longitude)
        return geo
    except WeatherServiceException as exc:
        logger.warning(f"Reverse geocode failed for ({latitude}, {longitude}): [{exc.error_code}] {exc.message}")
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail,
                "location_searched": f"({latitude}, {longitude})",
                "retries_attempted": exc.retries_attempted,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in reverse_geocode for ({latitude}, {longitude}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"Unexpected error during reverse geocoding: {str(e)}",
                "location_searched": f"({latitude}, {longitude})",
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )


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
    location: Optional[str] = Query(None, description="Target location name or city"),
    latitude: Optional[float] = Query(None, description="GPS latitude [-90, 90]", ge=-90.0, le=90.0),
    longitude: Optional[float] = Query(None, description="GPS longitude [-180, 180]", ge=-180.0, le=180.0),
    date: Optional[str] = Query(None, description="Target date in YYYY-MM-DD")
):
    """Fetches real meteorological forecast data for a specified location name or GPS coordinates.
    
    Supports:
    1. Direct live GPS coordinates: latitude + longitude (auto-detected via browser Geolocation API).
    2. City or regional search: location string.
    Never returns fabricated or hallucinated values.
    """
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Validate inputs
    has_coords = (latitude is not None and longitude is not None)
    clean_location = location.strip() if location else ""

    if not has_coords and not clean_location:
        raise HTTPException(
            status_code=400,
            detail={
                "error": True,
                "error_code": "INVALID_INPUT",
                "message": "Either 'location' or both 'latitude' and 'longitude' must be provided.",
                "location_searched": "<empty>",
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    search_label = clean_location or f"({latitude:.4f}°, {longitude:.4f}°)"

    try:
        # Step 1: Resolve location (via coordinates or forward geocode)
        if has_coords:
            geo = await geo_service.reverse_geocode(
                latitude=latitude,
                longitude=longitude,
                fallback_name=clean_location or None
            )
        else:
            geo = await geo_service.geocode(clean_location)

        # Step 2: Fetch forecast from Open-Meteo
        forecast = await weather_tool.get_forecast(geo, target_date)
        return forecast

    except WeatherServiceException as exc:
        logger.warning(f"Weather query failed for '{search_label}': [{exc.error_code}] {exc.message}")
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": True,
                "error_code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail,
                "location_searched": search_label,
                "retries_attempted": exc.retries_attempted,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_forecast for '{search_label}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "error_code": "INTERNAL_ERROR",
                "message": f"An unexpected error occurred while retrieving weather: {str(e)}",
                "location_searched": search_label,
                "retries_attempted": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
