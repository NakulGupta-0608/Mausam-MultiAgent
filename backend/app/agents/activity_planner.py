import time
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.schemas.analysis import ActivityRecommendation


class ActivityPlannerAgent(BaseAgent):
    """Evaluates planned activities, calculates feasibility windows, and recommends gear."""

    def __init__(self):
        super().__init__(
            name="ActivityPlanner",
            role="Operational Planning & Feasibility Agent",
            description="Analyzes user intent and queries against microclimatic forecasts to generate schedule windows and gear requirements."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        weather = state.weather
        query_lower = state.query.lower()

        # Identify primary activity focus
        activity_type = "Outdoor Excursion"
        if any(w in query_lower for w in ["hike", "trek", "trail", "mountain"]):
            activity_type = "Hiking & Trekking"
        elif any(w in query_lower for w in ["run", "jog", "marathon", "cycle", "bike"]):
            activity_type = "Endurance & Cycling"
        elif any(w in query_lower for w in ["wedding", "party", "dinner", "picnic", "event"]):
            activity_type = "Outdoor Gathering & Event"
        elif any(w in query_lower for w in ["photo", "shoot", "sightseeing", "tour"]):
            activity_type = "Sightseeing & Photography"
        elif any(w in query_lower for w in ["travel", "drive", "road trip", "flight"]):
            activity_type = "Travel & Transit"

        # Determine verdict based on outdoor score
        if state.outdoor_score >= 75:
            verdict = "Recommended"
            confidence = 92
            time_window = "07:30 - 16:30 (Optimal atmospheric window)"
            reasoning = f"Favorable conditions with {weather.condition_text} and comfortable ambient warmth ({weather.temp_c}°C)."
        elif state.outdoor_score >= 50:
            verdict = "Conditional"
            confidence = 74
            time_window = "07:00 - 11:30 (Morning window recommended before afternoon fluctuations)"
            reasoning = f"Feasible with precautions: {weather.precipitation_prob}% rain risk and {weather.wind_kph} km/h wind speeds."
        else:
            verdict = "Not Recommended"
            confidence = 88
            time_window = "Postpone to dry window or relocate to sheltered indoor venues"
            reasoning = f"Unfavorable conditions detected ({weather.condition_text}, high risk factors)."

        # Dynamic gear recommendations
        gear = ["Refillable Water Bottle", "Mobile Power Bank"]
        if weather.temp_c < 16:
            gear.extend(["Insulated Windproof Jacket", "Thermal Gloves"])
        elif weather.temp_c > 27:
            gear.extend(["Wide-brim UV Sun Hat", "Electrolyte Hydration", "SPF 50+ Sunscreen"])

        if weather.precipitation_prob > 35 or weather.precipitation_mm > 0:
            gear.extend(["Waterproof Gore-Tex Shell", "Rain Cover for Gear"])

        if weather.wind_kph > 20:
            gear.append("Eye Protection / Wind Goggles")

        alternatives = []
        if verdict != "Recommended":
            alternatives = ["Museum / Gallery Exploration", "Indoor Bouldering / Gym Session", "Covered Cafe / Culinary Tour"]
        else:
            alternatives = ["Sunset Ridge Walk", "Scenic Photography Loop", "Open-air Botanical Gardens"]

        rec = ActivityRecommendation(
            activity=activity_type,
            verdict=verdict,
            confidence_score=confidence,
            reasoning=reasoning,
            ideal_time_window=time_window,
            gear_required=gear,
            alternatives=alternatives,
        )

        state.activities = [rec]
        state.packing_checklist = gear

        duration = (time.perf_counter() - start_time) * 1000

        tracer.record_step(
            agent_name=self.name,
            stage="Activity Feasibility & Route Advisory",
            status="completed",
            duration_ms=duration,
            summary=f"Synthesized activity plan for '{activity_type}': {verdict} ({confidence}% confidence).",
            inputs={"query": state.query, "outdoor_score": state.outdoor_score},
            outputs={
                "activity": activity_type,
                "verdict": verdict,
                "ideal_time_window": time_window,
                "gear_count": len(gear),
            }
        )

        return state
