import time
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.tools.weather_api import weather_tool
from backend.app.tools.geo_service import geo_service
from backend.app.core.exceptions import WeatherServiceException


class DataAgent(BaseAgent):
    """Acquires verified empirical meteorological telemetry from real external APIs without data fabrication."""

    def __init__(self):
        super().__init__(
            name="DataAgent",
            role="Empirical Telemetry Specialist",
            description="Executes geocoding resolution and fetches real-world atmospheric measurements from live meteorological models."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        try:
            # Step 1: Resolve Coordinates
            state.geo = await geo_service.geocode(state.location_name)

            # Step 2: Fetch Live Forecast
            weather = await weather_tool.get_forecast(state.geo, state.target_date)
            state.weather = weather

            duration = (time.perf_counter() - start_time) * 1000

            reasoning = (
                f"Resolved '{state.location_name}' to coordinates ({state.geo.latitude}°, {state.geo.longitude}°). "
                f"Fetched live Open-Meteo telemetry: {weather.condition_text} at {weather.temp_c}°C, "
                f"relative humidity {weather.humidity}%, wind speed {weather.wind_kph} km/h ({weather.wind_direction}), "
                f"precipitation probability {weather.precipitation_prob}%. No synthetic fallback used."
            )

            tracer.record_step(
                agent_name=self.name,
                stage="Empirical Data Retrieval",
                action="ACQUIRE_VERIFIED_TELEMETRY",
                reasoning=reasoning,
                status="completed",
                duration_ms=duration,
                retries=0,
                summary=f"Captured verified live observation: {weather.condition_text} at {weather.temp_c}°C in {state.geo.name}.",
                inputs={"location": state.location_name, "date": state.target_date},
                outputs={
                    "name": state.geo.name,
                    "latitude": state.geo.latitude,
                    "longitude": state.geo.longitude,
                    "temp_c": weather.temp_c,
                    "humidity": weather.humidity,
                    "wind_kph": weather.wind_kph,
                    "condition": weather.condition_text,
                    "precipitation_prob": weather.precipitation_prob,
                    "source": weather.source,
                }
            )

            return state

        except WeatherServiceException as wse:
            duration = (time.perf_counter() - start_time) * 1000
            tracer.record_step(
                agent_name=self.name,
                stage="Empirical Data Retrieval",
                action="ACQUIRE_VERIFIED_TELEMETRY",
                reasoning=f"External meteorological service halted request with code {wse.error_code}. Bounded retries exhausted.",
                status="failed",
                duration_ms=duration,
                retries=wse.retries_attempted,
                summary=f"Failed to acquire live data: [{wse.error_code}] {wse.message}",
                inputs={"location": state.location_name, "date": state.target_date},
                outputs={
                    "error": True,
                    "error_code": wse.error_code,
                    "message": wse.message,
                    "detail": wse.detail,
                    "retries": wse.retries_attempted,
                }
            )
            raise
