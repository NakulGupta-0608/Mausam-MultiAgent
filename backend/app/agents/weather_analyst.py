import time
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.tools.weather_api import weather_tool
from backend.app.tools.geo_service import geo_service


class WeatherAnalystAgent(BaseAgent):
    """Responsible for geocoding, retrieving atmospheric data, and synthesizing weather index."""

    def __init__(self):
        super().__init__(
            name="WeatherAnalyst",
            role="Atmospheric Intelligence Specialist",
            description="Acquires live meteorological models, calculates comfort indexes, and analyzes atmospheric trends."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        # Step 1: Geocode location
        state.geo = await geo_service.geocode(state.location_name)

        # Step 2: Fetch dynamic forecast
        weather = await weather_tool.get_forecast(state.geo, state.target_date)
        state.weather = weather

        # Calculate outdoor score dynamically
        score = 85
        # Temperature penalty if too cold or too hot
        if weather.temp_c < 10:
            score -= int((10 - weather.temp_c) * 2)
        elif weather.temp_c > 32:
            score -= int((weather.temp_c - 32) * 3)

        # Rain penalty
        if weather.precipitation_prob > 30:
            score -= int((weather.precipitation_prob - 30) * 0.6)

        # Wind penalty
        if weather.wind_kph > 25:
            score -= int((weather.wind_kph - 25) * 1.2)

        # UV penalty
        if weather.uv_index > 8:
            score -= 10

        score = max(15, min(98, score))
        state.outdoor_score = score

        duration = (time.perf_counter() - start_time) * 1000

        tracer.record_step(
            agent_name=self.name,
            stage="Atmospheric Telemetry & Synthesis",
            status="completed",
            duration_ms=duration,
            summary=f"Resolved coordinates ({state.geo.latitude}, {state.geo.longitude}) and captured {weather.condition_text} at {weather.temp_c}°C with outdoor index {score}/100.",
            inputs={"location": state.location_name, "target_date": state.target_date},
            outputs={
                "temp_c": weather.temp_c,
                "humidity": weather.humidity,
                "wind_kph": weather.wind_kph,
                "condition": weather.condition_text,
                "outdoor_score": score,
                "provider": weather.source,
            }
        )

        return state
