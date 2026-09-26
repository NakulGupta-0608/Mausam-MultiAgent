import time
from typing import List
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.schemas.analysis import (
    OptionComparison,
    EvidenceCitation,
    ActivityRecommendation,
    RecommendationCard,
)
from backend.app.core.llm import llm_service


class RecommendationAgent(BaseAgent):
    """Compares options and produces an evidence-based decision with stated limitations.
    
    Dynamically adjusts advice when the Critic Agent requests corrections.
    """

    def __init__(self):
        super().__init__(
            name="RecommendationAgent",
            role="Decision Synthesis & Comparative Strategy Specialist",
            description="Evaluates operational trade-offs, cites empirical telemetry evidence, articulates forecast limitations, and refines decisions upon critique."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        weather = state.weather
        plan = state.plan
        outdoor_score = state.outdoor_score
        correction = state.active_correction_request

        activity_name = plan.entities.get("activity_category", "Outdoor Excursion") if plan else "Outdoor Excursion"

        # Step 1: Formulate Evidence Citations strictly from verified DataAgent telemetry
        citations = [
            EvidenceCitation(
                metric="Ambient Temperature",
                observed_value=f"{weather.temp_c}°C (Feels like {weather.feels_like_c}°C)",
                implication="Thermal energy dictates clothing layer requirements and hydration demand."
            ),
            EvidenceCitation(
                metric="Precipitation Probability",
                observed_value=f"{weather.precipitation_prob}% ({weather.precipitation_mm}mm volume)",
                implication="Determines moisture barrier necessity and surface traction degradation."
            ),
            EvidenceCitation(
                metric="Sustained Wind Speed",
                observed_value=f"{weather.wind_kph} km/h (Direction: {weather.wind_direction})",
                implication="Affects wind-chill factor, balance on exposed slopes, and equipment stability."
            ),
            EvidenceCitation(
                metric="Solar UV Index",
                observed_value=f"{weather.uv_index}",
                implication="Establishes safe unshaded duration and dermal radiation protection protocol."
            ),
        ]

        # Step 2: Determine Verdict and Headline (incorporating critic correction if present)
        if correction:
            # Critic demanded correction due to over-optimism or rule breach
            if "reject" in correction.lower() or "downgrade" in correction.lower() or outdoor_score < 75:
                verdict_badge = "Caution" if outdoor_score >= 50 else "Unfavorable"
                headline = f"Conditional Approval with Mandatory Precautions for {state.location_name}"
                comfort_summary = (
                    f"Revised after Critic validation: While {activity_name} is feasible, "
                    f"elevated meteorological risks ({weather.precipitation_prob}% rain, {weather.wind_kph} km/h wind) "
                    f"require morning-only execution and strict abort criteria."
                )
            else:
                verdict_badge = "Optimal"
                headline = f"Prime Weather Windows Confirmed for {state.location_name}"
                comfort_summary = f"Atmospheric stability verified across temperature ({weather.temp_c}°C) and wind ({weather.wind_kph} km/h)."
        else:
            if outdoor_score >= 80:
                verdict_badge = "Optimal"
                headline = f"Prime outdoor conditions for {state.location_name}"
                comfort_summary = f"High atmospheric stability observed. Balanced thermal comfort ({weather.temp_c}°C) and safe wind velocity."
            elif outdoor_score >= 60:
                verdict_badge = "Caution"
                headline = f"Proceed with selective planning in {state.location_name}"
                comfort_summary = f"Moderate variability present. {weather.precipitation_prob}% precipitation risk requires dedicated preparation."
            elif outdoor_score >= 40:
                verdict_badge = "Unfavorable"
                headline = f"Adverse weather conditions for {state.location_name}"
                comfort_summary = f"Challenging weather metrics ({weather.condition_text}). Strongly recommend indoor or sheltered alternatives."
            else:
                verdict_badge = "Severe"
                headline = f"Severe weather warning active for {state.location_name}"
                comfort_summary = "Significant atmospheric hazards active. Outdoor expeditions are hazardous and not advised."

        # Step 3: Comparative Option Analysis
        opt_primary_score = outdoor_score
        opt_morning_score = min(95, outdoor_score + 10) if outdoor_score < 85 else outdoor_score
        opt_indoor_score = 92

        options = [
            OptionComparison(
                option_name=f"Primary Route ({activity_name})",
                suitability_score=opt_primary_score,
                verdict="Recommended" if opt_primary_score >= 75 else ("Conditional" if opt_primary_score >= 50 else "Not Recommended"),
                pros=[f"Directly accomplishes user objective", f"Temperature stable at {weather.temp_c}°C"],
                cons=[f"{weather.precipitation_prob}% rain risk", f"Wind gusts up to {weather.wind_kph} km/h"],
            ),
            OptionComparison(
                option_name="Early Dawn Window (06:30 - 10:30)",
                suitability_score=opt_morning_score,
                verdict="Optimal" if opt_morning_score >= 80 else "Viable",
                pros=["Precedes peak solar diurnal heating", "Lower likelihood of afternoon convective showers", "Calm wind envelope"],
                cons=["Colder early morning ground temperatures", "Limited natural light before sunrise"],
            ),
            OptionComparison(
                option_name="Sheltered / Indoor Contingency",
                suitability_score=opt_indoor_score,
                verdict="Sheltered Backup",
                pros=["Zero atmospheric precipitation exposure", "Guaranteed climate control", "Zero equipment weather degradation"],
                cons=["Does not fulfill outdoor mountain/trail experience"],
            )
        ]

        # Step 4: Stated Limitations
        limitations = [
            "Microclimate Variance: Topographical elevation gradients (valleys vs ridges) can alter local wind velocity and precipitation by up to ±35% from grid coordinates.",
            "Temporal Horizon: Numerical forecast skill degrades after 48 hours; empirical observations must be cross-checked morning of activity.",
            "Convective Squalls: Localized convective cloud bursts can form rapidly in mountainous or coastal sectors with less than 90 minutes lead time.",
            "Personal Acclimatization: Individual biological tolerance to wind chill, heat exhaustion, and altitude varies significantly beyond baseline index.",
        ]

        # Step 5: Gear Checklist
        gear = ["2L Hydration System", "Mobile Communication & Backup Power Bank"]
        if weather.temp_c < 16:
            gear.extend(["Moisture-wicking Thermal Underlayer", "Wind-resistant Technical Jacket", "Fleece Gloves"])
        elif weather.temp_c > 26:
            gear.extend(["Wide-brim Solar Sun Hat", "Electrolyte Replacement Tablets", "SPF 50+ Sunscreen"])

        if weather.precipitation_prob > 30 or weather.precipitation_mm > 0:
            gear.extend(["Seam-sealed Waterproof Rain Jacket", "High-visibility Pack Rain Cover", "Waterproof Footwear"])

        if weather.wind_kph > 20:
            gear.append("Eye Protection / Tactical Wind Eyewear")

        # Step 6: Activity Breakdown
        activity_rec = ActivityRecommendation(
            activity=activity_name,
            verdict="Recommended" if outdoor_score >= 75 else ("Conditional" if outdoor_score >= 50 else "Not Recommended"),
            confidence_score=max(60, min(95, 60 + outdoor_score // 3)),
            reasoning=f"Empirical evaluation shows {weather.condition_text} at {weather.temp_c}°C with {weather.precipitation_prob}% rain risk. {comfort_summary}",
            ideal_time_window="06:30 - 11:00 (Prime atmospheric stability window)",
            gear_required=gear,
            alternatives=["Indoor Climbing / Athletic Center", "Regional Cultural Museum Tour", "Covered Botanical Pavilion"],
        )

        state.activities = [activity_rec]
        state.options_comparison = options
        state.evidence_citations = citations
        state.stated_limitations = limitations
        state.packing_checklist = gear
        state.verdict_badge = verdict_badge
        state.headline = headline
        state.comfort_summary = comfort_summary

        duration = (time.perf_counter() - start_time) * 1000

        reasoning = (
            f"Synthesized evidence-based recommendation citing {len(citations)} empirical metrics. "
            f"Compared 3 strategic operational options. Formulated verdict '{verdict_badge}' with "
            f"{len(limitations)} stated forecasting limitations. "
            f"{'Incorporated Critic correction feedback.' if correction else 'Initial synthesis.'}"
        )

        tracer.record_step(
            agent_name=self.name,
            stage="Comparative Decision Synthesis",
            action="SYNTHESIZE_DECISION_AND_COMPARE_OPTIONS",
            reasoning=reasoning,
            status="completed",
            duration_ms=duration,
            summary=f"Synthesized comparative recommendation: verdict '{verdict_badge}' ({outdoor_score}/100) with 3 options and 4 stated limitations.",
            inputs={"outdoor_score": outdoor_score, "weather_source": weather.source, "correction_active": bool(correction)},
            outputs={
                "verdict_badge": verdict_badge,
                "headline": headline,
                "options_compared": len(options),
                "citations_count": len(citations),
                "limitations_count": len(limitations),
            }
        )

        return state
