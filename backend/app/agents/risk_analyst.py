import time
from typing import List
from backend.app.agents.base import BaseAgent
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.schemas.analysis import (
    RuleEvaluation,
    RiskAssessmentResult,
    RiskItem,
)


class RiskAnalysisAgent(BaseAgent):
    """Assesses empirical meteorological data against configurable, transparent rules and planner constraints."""

    def __init__(self):
        super().__init__(
            name="RiskAnalysisAgent",
            role="Configurable Risk Rule Evaluator",
            description="Applies deterministic, transparent atmospheric safety rules against empirical data and user constraints."
        )

    async def process(self, state: WorkflowState, tracer: AgentExecutionTracer) -> WorkflowState:
        start_time = time.perf_counter()

        weather = state.weather
        if not weather:
            raise RuntimeError("Cannot execute RiskAnalysisAgent without valid weather telemetry from DataAgent.")

        constraints = state.plan.constraints if state.plan else {}
        max_rain_limit = constraints.get("max_rain_probability", 40)
        max_wind_limit = constraints.get("max_wind_kph", 25.0)
        min_temp_limit = constraints.get("min_temp_c", 10.0)
        max_temp_limit = constraints.get("max_temp_c", 32.0)
        max_uv_limit = constraints.get("max_uv_index", 7.5)

        evaluations: List[RuleEvaluation] = []
        alerts: List[RiskItem] = []
        total_penalty = 0

        # Rule 1: Precipitation Probability vs Planner Constraint
        rain_triggered = weather.precipitation_prob > max_rain_limit
        if rain_triggered:
            diff = weather.precipitation_prob - max_rain_limit
            sev = "critical" if diff > 30 else ("high" if diff > 15 else "moderate")
            pen = 15 + min(25, diff)
            total_penalty += pen
            evaluations.append(RuleEvaluation(
                rule_id="RULE_PRECIP_THRESHOLD",
                description="Rain probability exceeds planned activity threshold",
                condition_evaluated=f"precipitation_prob ({weather.precipitation_prob}%) > limit ({max_rain_limit}%)",
                triggered=True,
                severity=sev,
                penalty=pen,
                mitigation=f"Carry full waterproof Gore-Tex outer shell ({weather.precipitation_mm}mm volume expected). Avoid exposed ridges."
            ))
            alerts.append(RiskItem(
                severity=sev,
                title="Rain Probability Exceeds Planned Tolerance",
                description=f"Precipitation probability is {weather.precipitation_prob}%, which breaches the {max_rain_limit}% planning ceiling.",
                mitigation="Carry waterproof gear and identify covered waypoints."
            ))
        else:
            evaluations.append(RuleEvaluation(
                rule_id="RULE_PRECIP_THRESHOLD",
                description="Rain probability within tolerance threshold",
                condition_evaluated=f"precipitation_prob ({weather.precipitation_prob}%) <= limit ({max_rain_limit}%)",
                triggered=False,
                severity="none",
                penalty=0,
                mitigation="No rain mitigation required."
            ))

        # Rule 2: Wind Velocity vs Planner Constraint
        wind_triggered = weather.wind_kph > max_wind_limit
        if wind_triggered:
            diff = weather.wind_kph - max_wind_limit
            sev = "high" if diff > 12 else "moderate"
            pen = 10 + min(20, int(diff * 1.2))
            total_penalty += pen
            evaluations.append(RuleEvaluation(
                rule_id="RULE_WIND_THRESHOLD",
                description="Wind velocity exceeds activity safety envelope",
                condition_evaluated=f"wind_kph ({weather.wind_kph} km/h) > limit ({max_wind_limit} km/h)",
                triggered=True,
                severity=sev,
                penalty=pen,
                mitigation=f"Secure loose equipment. Wind direction {weather.wind_direction}. Exercise caution on open terrain."
            ))
            alerts.append(RiskItem(
                severity=sev,
                title="Elevated Wind Velocity",
                description=f"Sustained wind speed is {weather.wind_kph} km/h from {weather.wind_direction} (limit {max_wind_limit} km/h).",
                mitigation="Dress in windproof technical shell; avoid clifflines."
            ))
        else:
            evaluations.append(RuleEvaluation(
                rule_id="RULE_WIND_THRESHOLD",
                description="Wind velocity within activity envelope",
                condition_evaluated=f"wind_kph ({weather.wind_kph} km/h) <= limit ({max_wind_limit} km/h)",
                triggered=False,
                severity="none",
                penalty=0,
                mitigation="Standard wind preparedness."
            ))

        # Rule 3: Thermal Comfort Boundaries
        temp_cold_triggered = weather.temp_c < min_temp_limit
        temp_hot_triggered = weather.temp_c > max_temp_limit

        if temp_cold_triggered:
            diff = min_temp_limit - weather.temp_c
            pen = min(20, int(diff * 2))
            total_penalty += pen
            evaluations.append(RuleEvaluation(
                rule_id="RULE_THERMAL_COLD",
                description="Ambient temperature below minimum comfortable threshold",
                condition_evaluated=f"temp_c ({weather.temp_c}°C) < min_limit ({min_temp_limit}°C)",
                triggered=True,
                severity="moderate",
                penalty=pen,
                mitigation="Deploy moisture-wicking thermal base layers and fleece insulation."
            ))
            alerts.append(RiskItem(
                severity="moderate",
                title="Low Ambient Temperature",
                description=f"Recorded temperature is {weather.temp_c}°C (feels like {weather.feels_like_c}°C).",
                mitigation="Wear insulated windproof layers."
            ))
        elif temp_hot_triggered:
            diff = weather.temp_c - max_temp_limit
            pen = min(25, int(diff * 2.5))
            total_penalty += pen
            evaluations.append(RuleEvaluation(
                rule_id="RULE_THERMAL_HEAT",
                description="Ambient temperature above maximum comfortable threshold",
                condition_evaluated=f"temp_c ({weather.temp_c}°C) > max_limit ({max_temp_limit}°C)",
                triggered=True,
                severity="high" if diff > 4 else "moderate",
                penalty=pen,
                mitigation="Maintain aggressive hydration (1L/hour), electrolytes, and shade access."
            ))
            alerts.append(RiskItem(
                severity="moderate",
                title="Elevated Heat Index",
                description=f"Recorded temperature is {weather.temp_c}°C (feels like {weather.feels_like_c}°C).",
                mitigation="Drink electrolyte water frequently and schedule rest in shade."
            ))
        else:
            evaluations.append(RuleEvaluation(
                rule_id="RULE_THERMAL_COMFORT",
                description="Ambient temperature in prime comfort range",
                condition_evaluated=f"{min_temp_limit}°C <= temp_c ({weather.temp_c}°C) <= {max_temp_limit}°C",
                triggered=False,
                severity="none",
                penalty=0,
                mitigation="Standard outdoor garments."
            ))

        # Rule 4: UV Radiation Risk
        uv_triggered = weather.uv_index > max_uv_limit
        if uv_triggered:
            pen = 10 if weather.uv_index > 8 else 5
            total_penalty += pen
            evaluations.append(RuleEvaluation(
                rule_id="RULE_UV_RADIATION",
                description="UV solar radiation exceeds safe direct exposure threshold",
                condition_evaluated=f"uv_index ({weather.uv_index}) > limit ({max_uv_limit})",
                triggered=True,
                severity="high" if weather.uv_index >= 8.0 else "moderate",
                penalty=pen,
                mitigation="Apply SPF 50+ broad-spectrum sunscreen and wear polarized UV400 eyewear."
            ))
            alerts.append(RiskItem(
                severity="moderate" if weather.uv_index < 8.0 else "high",
                title="Elevated Solar UV Radiation",
                description=f"UV index is {weather.uv_index}.",
                mitigation="Reapply sunscreen every 2 hours and wear wide-brim hat."
            ))
        else:
            evaluations.append(RuleEvaluation(
                rule_id="RULE_UV_RADIATION",
                description="UV radiation level is safe / moderate",
                condition_evaluated=f"uv_index ({weather.uv_index}) <= limit ({max_uv_limit})",
                triggered=False,
                severity="none",
                penalty=0,
                mitigation="Normal sun awareness."
            ))

        # Rule 5: Severe Atmospheric Phenomena (Thunderstorm / Violent Squalls)
        cond_lower = weather.condition_text.lower()
        severe_triggered = any(s in cond_lower for s in ["thunderstorm", "hail", "violent", "dense fog", "heavy rain"])
        if severe_triggered:
            total_penalty += 35
            evaluations.append(RuleEvaluation(
                rule_id="RULE_SEVERE_CONVECTIVE",
                description="Severe convective atmospheric activity detected",
                condition_evaluated=f"condition_text ('{weather.condition_text}') contains severe storm keyword",
                triggered=True,
                severity="critical",
                penalty=35,
                mitigation="Immediately seek permanent lightning shelter. Cease high-altitude exposure."
            ))
            alerts.append(RiskItem(
                severity="critical",
                title="Severe Convective Hazard Active",
                description=f"Active meteorological condition reports '{weather.condition_text}'.",
                mitigation="Postpone outdoor activities or relocate to hardened shelter."
            ))

        # Calculate final outdoor suitability score
        outdoor_score = max(15, min(98, 100 - total_penalty))
        state.outdoor_score = outdoor_score

        # Determine aggregate risk level
        if outdoor_score >= 80:
            risk_level = "Low"
        elif outdoor_score >= 60:
            risk_level = "Moderate"
        elif outdoor_score >= 40:
            risk_level = "High"
        else:
            risk_level = "Critical"

        triggered_count = sum(1 for e in evaluations if e.triggered)
        summary = (
            f"Evaluated {len(evaluations)} transparent rules against real telemetry. "
            f"{triggered_count} rule(s) triggered with total penalty of {total_penalty} points, "
            f"resulting in outdoor score {outdoor_score}/100 (Risk Level: {risk_level})."
        )

        state.risk_assessment = RiskAssessmentResult(
            outdoor_score=outdoor_score,
            risk_level=risk_level,
            summary=summary,
            rules_evaluated=evaluations,
        )
        state.risk_alerts = alerts

        duration = (time.perf_counter() - start_time) * 1000

        reasoning = (
            f"Transparent rule evaluation completed. Evaluated precipitation ({weather.precipitation_prob}% vs limit {max_rain_limit}%), "
            f"wind ({weather.wind_kph} km/h vs limit {max_wind_limit} km/h), temp ({weather.temp_c}°C), "
            f"and UV ({weather.uv_index}). Deducted {total_penalty} penalty points from base 100."
        )

        tracer.record_step(
            agent_name=self.name,
            stage="Configurable Risk Assessment",
            action="EVALUATE_CONFIGURABLE_RULES",
            reasoning=reasoning,
            status="completed",
            duration_ms=duration,
            summary=summary,
            inputs={"weather": {"temp_c": weather.temp_c, "precipitation_prob": weather.precipitation_prob, "wind_kph": weather.wind_kph}, "constraints": constraints},
            outputs={"outdoor_score": outdoor_score, "risk_level": risk_level, "triggered_rules": [e.rule_id for e in evaluations if e.triggered]},
        )

        return state
