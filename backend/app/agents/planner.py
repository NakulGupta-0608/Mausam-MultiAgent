import time
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.schemas.analysis import StructuredPlan
from backend.app.core.llm import llm_service


class PlannerAgent(BaseAgent):
    """Interprets the user's natural language request into a structured task plan with entities, sub-goals, and constraints."""

    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            role="Strategic Task Decomposition Specialist",
            description="Analyzes user intent to formulate entities, execution sub-goals, and atmospheric constraint thresholds."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()
        query_lower = state.query.lower()

        # Step 1: Extract entities
        activity_category = "General Outdoor Activity"
        gear_sensitivity = "Standard"
        duration_hours = 4

        if any(w in query_lower for w in ["hike", "trek", "summit", "trail", "alpine"]):
            activity_category = "High-Altitude Hiking & Trekking"
            gear_sensitivity = "High (Technical Footwear, Gore-Tex, Navigation)"
            duration_hours = 6
        elif any(w in query_lower for w in ["bike", "cycle", "ride", "marathon", "run"]):
            activity_category = "Endurance Cycling & Running"
            gear_sensitivity = "High (Aerodynamic, Wind protection, Hydration)"
            duration_hours = 3
        elif any(w in query_lower for w in ["wedding", "party", "dinner", "picnic", "reception"]):
            activity_category = "Outdoor Event & Gathering"
            gear_sensitivity = "Moderate (Canopy, Formal Attire, Guest Comfort)"
            duration_hours = 5
        elif any(w in query_lower for w in ["photo", "shoot", "film", "sightseeing"]):
            activity_category = "Photography & Sightseeing"
            gear_sensitivity = "Moderate (Lens protection, Tripods, Batteries)"
            duration_hours = 3

        entities = {
            "location_name": state.location_name,
            "target_date": state.target_date,
            "activity_category": activity_category,
            "estimated_duration_hours": duration_hours,
            "gear_sensitivity": gear_sensitivity,
            "raw_query": state.query,
        }

        # Step 2: Define strict operational constraints based on activity sensitivity
        if "Hiking" in activity_category:
            constraints = {
                "max_rain_probability": 40,
                "max_wind_kph": 25.0,
                "min_temp_c": 8.0,
                "max_temp_c": 30.0,
                "max_uv_index": 8.0,
                "severe_weather_intolerant": True,
                "requires_shelter_backup": True,
            }
        elif "Event" in activity_category:
            constraints = {
                "max_rain_probability": 20,
                "max_wind_kph": 20.0,
                "min_temp_c": 16.0,
                "max_temp_c": 32.0,
                "max_uv_index": 7.0,
                "severe_weather_intolerant": True,
                "requires_shelter_backup": True,
            }
        elif "Cycling" in activity_category:
            constraints = {
                "max_rain_probability": 30,
                "max_wind_kph": 22.0,
                "min_temp_c": 10.0,
                "max_temp_c": 32.0,
                "max_uv_index": 8.0,
                "severe_weather_intolerant": True,
                "requires_shelter_backup": False,
            }
        else:
            constraints = {
                "max_rain_probability": 50,
                "max_wind_kph": 28.0,
                "min_temp_c": 12.0,
                "max_temp_c": 33.0,
                "max_uv_index": 8.0,
                "severe_weather_intolerant": True,
                "requires_shelter_backup": False,
            }

        # Step 3: Define sub-goals
        sub_goals = [
            "1. Geocode location and retrieve empirical coordinates",
            "2. Fetch verified meteorological telemetry and multi-day outlook",
            "3. Assess telemetry against configurable risk rules and planner constraints",
            "4. Compare operational options and synthesize evidence-backed recommendation",
            "5. Execute Critic Agent validation against raw source data and stated limitations",
        ]

        plan = StructuredPlan(
            entities=entities,
            sub_goals=sub_goals,
            constraints=constraints,
        )

        state.plan = plan
        duration = (time.perf_counter() - start_time) * 1000

        reasoning = (
            f"Deconstructed user intent into '{activity_category}'. Formulated {len(sub_goals)} sub-goals "
            f"and established constraint boundaries: max rain {constraints['max_rain_probability']}%, "
            f"max wind {constraints['max_wind_kph']} km/h, thermal comfort range "
            f"{constraints['min_temp_c']}°C - {constraints['max_temp_c']}°C."
        )

        tracer.record_step(
            agent_name=self.name,
            stage="Task Planning & Constraint Definition",
            action="DECONSTRUCT_USER_REQUEST",
            reasoning=reasoning,
            status="completed",
            duration_ms=duration,
            summary=f"Structured task plan formulated for '{activity_category}' with {len(constraints)} constraint rules.",
            inputs={"query": state.query, "location": state.location_name, "date": state.target_date},
            outputs={"entities": entities, "constraints": constraints, "sub_goals": sub_goals},
        )

        return state
