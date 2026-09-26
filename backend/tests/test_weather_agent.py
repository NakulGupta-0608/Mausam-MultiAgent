import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.app.tools.geo_service import geo_service
from backend.app.tools.weather_api import weather_tool
from backend.app.schemas.weather import GeoLocation, WeatherCondition
from backend.app.core.exceptions import (
    LocationNotFoundException,
    WeatherApiTimeoutException,
    WeatherApiErrorException,
    MalformedResponseException,
)

client = TestClient(app)


# ============================================================================
# 1. HAPPY PATH TESTS (Real Meteorological Telemetry)
# ============================================================================

@pytest.mark.asyncio
async def test_geocode_happy_path_real():
    """Happy path: Resolve real geographical coordinates via Open-Meteo Geocoding."""
    geo = await geo_service.geocode("Shimla")
    assert geo.name == "Shimla"
    assert geo.country == "India"
    assert 30.0 <= geo.latitude <= 32.0
    assert 76.0 <= geo.longitude <= 78.0
    assert geo.timezone is not None


@pytest.mark.asyncio
async def test_weather_forecast_happy_path_real():
    """Happy path: Fetch live real forecast and validate fields without fabrication."""
    geo = GeoLocation(
        name="London",
        country="United Kingdom",
        latitude=51.5074,
        longitude=-0.1278,
        timezone="Europe/London"
    )
    weather = await weather_tool.get_forecast(geo, "2026-09-26")

    assert isinstance(weather, WeatherCondition)
    assert weather.location.name == "London"
    assert weather.source == "open-meteo-live"
    assert isinstance(weather.temp_c, float)
    assert -50.0 <= weather.temp_c <= 60.0
    assert 0 <= weather.humidity <= 100
    assert weather.wind_kph >= 0.0
    assert len(weather.condition_text) > 0
    assert len(weather.forecast_days) >= 5
    for day in weather.forecast_days:
        assert day.date is not None
        assert day.max_temp_c >= day.min_temp_c
        assert 0 <= day.rain_probability <= 100


def test_api_endpoint_weather_happy_path():
    """Happy path: GET /api/weather returns 200 with structured forecast data."""
    response = client.get("/api/weather?location=Bengaluru")
    assert response.status_code == 200
    data = response.json()
    assert data["location"]["name"] == "Bengaluru"
    assert data["source"] == "open-meteo-live"
    assert "temp_c" in data
    assert "humidity" in data
    assert "forecast_days" in data
    assert len(data["forecast_days"]) > 0


# ============================================================================
# 2. FAILURE MODE 1: INVALID LOCATION
# ============================================================================

@pytest.mark.asyncio
async def test_geocode_invalid_location_failure():
    """Failure mode 1: Invalid location name raises LocationNotFoundException."""
    invalid_query = "xyz_nonexistent_city_9999999"
    with pytest.raises(LocationNotFoundException) as exc_info:
        await geo_service.geocode(invalid_query)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "LOCATION_NOT_FOUND"
    assert invalid_query in exc_info.value.message


def test_api_endpoint_invalid_location_404():
    """Failure mode 1: GET /api/weather returns 404 with structured error schema."""
    response = client.get("/api/weather?location=invalid_place_abc_123456")
    assert response.status_code == 404
    err = response.json()["detail"]
    assert err["error"] is True
    assert err["error_code"] == "LOCATION_NOT_FOUND"
    assert "could not be resolved" in err["message"]
    assert err["location_searched"] == "invalid_place_abc_123456"
    assert "timestamp" in err


# ============================================================================
# 3. FAILURE MODE 2: API TIMEOUT WITH BOUNDED RETRIES
# ============================================================================

@pytest.mark.asyncio
async def test_weather_api_timeout_bounded_retries():
    """Failure mode 2: Upstream API timeout triggers bounded retries then raises WeatherApiTimeoutException."""
    geo = GeoLocation(
        name="TestCity",
        latitude=10.0,
        longitude=10.0,
        timezone="UTC"
    )

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(WeatherApiTimeoutException) as exc_info:
            await weather_tool.get_forecast(geo, "2026-09-26")

        # Verify bounded retries: 1 initial attempt + 2 retries = 3 attempts total
        assert mock_client.get.call_count == 3
        assert exc_info.value.status_code == 504
        assert exc_info.value.error_code == "WEATHER_API_TIMEOUT"
        assert exc_info.value.retries_attempted == 3


# ============================================================================
# 4. FAILURE MODE 3: UPSTREAM SERVER ERROR (502 / 500)
# ============================================================================

@pytest.mark.asyncio
async def test_weather_api_server_error_502():
    """Failure mode 3: Upstream 500 error raises WeatherApiErrorException."""
    geo = GeoLocation(
        name="TestCity",
        latitude=10.0,
        longitude=10.0,
        timezone="UTC"
    )

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error in upstream cluster"

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(WeatherApiErrorException) as exc_info:
            await weather_tool.get_forecast(geo, "2026-09-26")

        assert exc_info.value.status_code == 502
        assert exc_info.value.error_code == "WEATHER_API_ERROR"


# ============================================================================
# 5. FAILURE MODE 4: MALFORMED RESPONSE SCHEMA VALIDATION
# ============================================================================

@pytest.mark.asyncio
async def test_weather_api_malformed_response():
    """Failure mode 4: Malformed response missing mandatory fields raises MalformedResponseException."""
    geo = GeoLocation(
        name="TestCity",
        latitude=10.0,
        longitude=10.0,
        timezone="UTC"
    )

    # Missing 'current' and 'daily' blocks
    malformed_json = {
        "latitude": 10.0,
        "longitude": 10.0,
        "timezone": "UTC",
        "corrupt_field": True
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = malformed_json

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(MalformedResponseException) as exc_info:
            await weather_tool.get_forecast(geo, "2026-09-26")

        assert exc_info.value.status_code == 422
        assert exc_info.value.error_code == "MALFORMED_RESPONSE"
