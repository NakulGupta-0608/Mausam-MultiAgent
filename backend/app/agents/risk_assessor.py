import time
from typing import List
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.schemas.analysis import RiskItem


class RiskAssessorAgent(BaseAgent):
    """Evaluates atmospheric hazards, air quality, UV exposure, and computes final risk verdicts."""

    def __init__(self):
        super().__init__(
            name="RiskAssessor",
            role="Hazard Evaluation & Mitigation Agent",
            description="Performs risk modeling against severe wind, precipitation, UV radiation, and atmospheric anomalies."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        weather = state.weather
        alerts: List[RiskItem] = []

        # Check Precipitation
        if weather.precipitation_prob >= 60:
            alerts.append(RiskItem(
                severity="high",
                title="Elevated Rain / Convective Activity",
                description=f"{weather.precipitation_prob}% probability of rainfall ({weather.precipitation_mm}mm expected).",
                mitigation="Carry waterproof outer layers and avoid exposed ridges during squall periods."
            ))
        elif weather.precipitation_prob >= 35:
            alerts.append(RiskItem(
                severity="moderate",
                title="Isolated Passing Showers",
                description="Scattered precipitation expected in localized sectors.",
                mitigation="Keep compact rainwear accessible."
            ))

        # Check Wind
        if weather.wind_kph > 35:
            alerts.append(RiskItem(
                severity="high",
                title="High Wind Speeds",
                description=f"Sustained winds up to {weather.wind_kph} km/h from {weather.wind_direction}.",
                mitigation="Secure loose equipment and exercise caution near cliff edges or exposed structures."
            ))
        elif weather.wind_kph > 22:
            alerts.append(RiskItem(
                severity="moderate",
                title="Breezy Conditions",
                description=f"Wind gusts up to {weather.wind_kph} km/h.",
                mitigation="Dress in wind-resistant layers."
            ))

        # Check UV Index
        if weather.uv_index >= 8.0:
            alerts.append(RiskItem(
                severity="high",
                title="Very High UV Radiation",
                description=f"Peak UV index reaches {weather.uv_index}.",
                mitigation="Apply broad-spectrum sunscreen every 2 hours and wear polarized UV eyewear."
            ))
        elif weather.uv_index >= 6.0:
            alerts.append(RiskItem(
                severity="moderate",
                title="Moderate UV Exposure",
                description=f"UV index around {weather.uv_index}.",
                mitigation="Wear head covering and sun protection."
            ))

        # Check Air Quality
        if weather.air_quality_index > 120:
            alerts.append(RiskItem(
                severity="moderate",
                title="Moderate Air Quality Alert",
                description=f"AQI index measured at {weather.air_quality_index} (Sensitive groups advisory).",
                mitigation="Reduce prolonged high-intensity cardiovascular exertion outdoors."
            ))

        # If no severe alerts
        if not alerts:
            alerts.append(RiskItem(
                severity="low",
                title="Stable Atmospheric Envelope",
                description="No severe meteorological hazards or extreme parameters identified.",
                mitigation="Standard outdoor preparation sufficient."
            ))

        state.risk_alerts = alerts

        # Verdict Badge & Summary
        if state.outdoor_score >= 80:
            state.verdict_badge = "Optimal"
            state.headline = f"Prime outdoor conditions for {state.location_name}"
            state.comfort_summary = "Atmospheric stability is high. Excellent balance of thermal comfort, mild breezes, and minimal precipitation hazard."
        elif state.outdoor_score >= 60:
            state.verdict_badge = "Caution"
            state.headline = f"Feasible with selective planning in {state.location_name}"
            state.comfort_summary = "Moderate weather variability observed. Early morning windows offer the most stable conditions."
        elif state.outdoor_score >= 40:
            state.verdict_badge = "Unfavorable"
            state.headline = f"Challenging weather conditions in {state.location_name}"
            state.comfort_summary = "Unfavorable meteorological indices detected. Consider sheltered or indoor alternatives."
        else:
            state.verdict_badge = "Severe"
            state.headline = f"Hazardous weather warning for {state.location_name}"
            state.comfort_summary = "High risk parameters active. Outdoor expeditions are not recommended."

        duration = (time.perf_counter() - start_time) * 1000

        tracer.record_step(
            agent_name=self.name,
            stage="Risk Profiling & Hazard Assessment",
            status="completed",
            duration_ms=duration,
            summary=f"Identified {len(alerts)} risk factor(s). Overall verdict: '{state.verdict_badge}'.",
            inputs={"outdoor_score": state.outdoor_score, "weather_condition": weather.condition_text},
            outputs={
                "verdict_badge": state.verdict_badge,
                "alerts_count": len(alerts),
                "headline": state.headline,
            }
        )

        return state
