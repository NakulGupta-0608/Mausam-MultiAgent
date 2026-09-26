import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.tools.geo_service import geo_service
from backend.app.schemas.weather import GeoLocation, WeatherCondition
from backend.app.schemas.analysis import AnalysisRequest
from backend.app.agents.data_agent import DataAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.core.exceptions import LocationNotFoundException

client = TestClient(app)


@pytest.mark.asyncio
async def test_geo_service_reverse_geocode_real():
    """Verify reverse geocoding returns valid structured GeoLocation from real API."""
    # Delhi coordinates: 28.6139, 77.2090
    geo = await geo_service.reverse_geocode(28.6139, 77.2090)
    assert isinstance(geo, GeoLocation)
    assert geo.latitude == 28.6139
    assert geo.longitude == 77.2090
    assert len(geo.name) > 0
    assert "Delhi" in geo.name or "India" in geo.country


@pytest.mark.asyncio
async def test_geo_service_reverse_geocode_bounds_validation():
    """Verify out-of-bounds coordinates raise LocationNotFoundException."""
    with pytest.raises(LocationNotFoundException):
        await geo_service.reverse_geocode(120.0, 77.0)  # Latitude > 90


def test_api_reverse_geocode_endpoint():
    """Verify GET /api/weather/reverse-geocode endpoint."""
    res = client.get("/api/weather/reverse-geocode?latitude=28.6139&longitude=77.2090")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert data["latitude"] == 28.6139
    assert data["longitude"] == 77.2090


def test_api_weather_with_coordinates_happy_path():
    """Verify GET /api/weather accepts latitude and longitude without a location string."""
    res = client.get("/api/weather?latitude=28.6139&longitude=77.2090")
    assert res.status_code == 200
    data = res.json()
    assert "temp_c" in data
    assert "humidity" in data
    assert "wind_kph" in data
    assert "precipitation_prob" in data
    assert data["location"]["latitude"] == 28.6139
    assert data["location"]["longitude"] == 77.2090


def test_api_weather_missing_parameters_400():
    """Verify GET /api/weather returns 400 if neither location nor coordinates are supplied."""
    res = client.get("/api/weather")
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["error_code"] == "INVALID_INPUT"
    assert "Either 'location' or both 'latitude' and 'longitude'" in detail["message"]


def test_api_weather_invalid_coordinate_bounds():
    """Verify GET /api/weather rejects out-of-bounds coordinates."""
    res = client.get("/api/weather?latitude=95.0&longitude=77.2090")
    assert res.status_code == 422  # FastAPI validation error for ge/le constraints


@pytest.mark.asyncio
async def test_data_agent_uses_live_coordinates():
    """Verify DataAgent prioritizes latitude/longitude coordinates over name geocoding."""
    agent = DataAgent()
    tracer = AgentExecutionTracer()
    state = WorkflowState(
        query="Can I jog outside?",
        location_name="Current Device Location",
        target_date="2026-09-26",
        latitude=28.6139,
        longitude=77.2090,
    )

    updated_state = await agent.process(state, tracer)
    assert updated_state.geo is not None
    assert updated_state.geo.latitude == 28.6139
    assert updated_state.geo.longitude == 77.2090
    assert updated_state.weather is not None
    assert "live GPS coordinates" in tracer.get_steps()[-1].reasoning


def test_multi_agent_analysis_with_live_coordinates():
    """Verify multi-agent workflow receives and runs with live GPS coordinates."""
    req_payload = {
        "query": "Is it safe to go for a trail run today?",
        "location": "Live Device Location",
        "target_date": "2026-09-26",
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    res = client.post("/api/analysis", json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommendation" in data
    assert "verdict_badge" in data["recommendation"]
    assert "outdoor_score" in data["recommendation"]
    assert "trace" in data
    # Verify DataAgent trace cited live coordinates
    data_step = next((s for s in data["trace"] if s["agent_name"] == "DataAgent"), None)
    assert data_step is not None
    assert "live GPS coordinates" in data_step["reasoning"]
