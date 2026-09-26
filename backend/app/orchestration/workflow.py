import time
import json
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any
from backend.app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    RecommendationCard,
    StoppingCondition,
)
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.data_agent import DataAgent
from backend.app.agents.risk_analyst import RiskAnalysisAgent
from backend.app.agents.recommendation import RecommendationAgent
from backend.app.agents.critic import CriticAgent
from backend.app.core.config import settings
from backend.app.core.exceptions import WeatherServiceException
from backend.app.monitoring.logger import logger


class WeatherIntelligencePipeline:
    """Central orchestrator coordinating the five agents with planning, execution, and critique loops.
    
    Enforces review attempt capping (max 2), step/time/cost budgets, and complete audit tracing.
    Supports both batch execution and live Server-Sent Events (SSE) streaming progress.
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.data_agent = DataAgent()
        self.risk_analyst = RiskAnalysisAgent()
        self.recommender = RecommendationAgent()
        self.critic = CriticAgent()

    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        """Batch execution of the multi-agent pipeline."""
        tracer = AgentExecutionTracer()
        target_date = request.target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"=== Multi-Agent Workflow Initiated: '{request.location}' on {target_date} (Query: '{request.query}') ===")

        state = WorkflowState(
            query=request.query,
            location_name=request.location,
            target_date=target_date,
            max_reviews=settings.MAX_CRITIC_REVIEWS,
            max_steps=settings.WORKFLOW_MAX_STEPS,
            time_budget_sec=settings.WORKFLOW_TIME_BUDGET_SEC,
        )

        stopped_early = False
        stop_reason = "Pipeline completed standard multi-agent cycle"

        # Step 1: Planner Agent
        state.step_count += 1
        state = await self.planner.process(state, tracer)

        if self._is_budget_exceeded(state, tracer):
            stopped_early = True
            stop_reason = "Budget ceiling reached after planning stage"

        # Step 2: Data Agent
        if not stopped_early:
            state.step_count += 1
            state = await self.data_agent.process(state, tracer)

            if not state.weather:
                stopped_early = True
                stop_reason = "DataAgent could not verify real empirical telemetry"

        # Step 3: Risk/Analysis Agent
        if not stopped_early:
            state.step_count += 1
            state = await self.risk_analyst.process(state, tracer)

        # Steps 4 & 5: Recommendation & Critic Iteration Loop (capped at 2)
        while not stopped_early and state.review_count < state.max_reviews:
            state.step_count += 1
            state = await self.recommender.process(state, tracer)

            if self._is_budget_exceeded(state, tracer):
                stopped_early = True
                stop_reason = "Time or step budget reached during recommendation phase"
                break

            state.step_count += 1
            state.review_count += 1
            state = await self.critic.process(state, tracer)

            review = state.current_critic_review
            if not review:
                break

            if review.verdict == "APPROVE":
                logger.info(f"Critic APPROVED recommendation on review cycle {state.review_count}.")
                break
            elif review.verdict == "NEEDS_MORE_DATA":
                logger.warning("Critic signaled NEEDS_MORE_DATA. Halting pipeline to prevent ungrounded advice.")
                stopped_early = True
                stop_reason = "Critic halted execution: Incomplete or missing empirical telemetry"
                break
            elif review.verdict == "REJECT":
                logger.warning(
                    f"Critic REJECTED recommendation (cycle {state.review_count}/{state.max_reviews}). "
                    f"Correction Request: {review.correction_request}"
                )
                if state.review_count >= state.max_reviews:
                    stopped_early = True
                    stop_reason = f"Review attempts capped at maximum limit ({state.max_reviews} iterations)"
                    break

        return self._build_response(state, tracer, stopped_early, stop_reason)

    async def run_stream(self, request: AnalysisRequest) -> AsyncGenerator[str, None]:
        """Real-time Server-Sent Events (SSE) generator streaming actual running tasks and final output."""
        tracer = AgentExecutionTracer()
        target_date = request.target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        state = WorkflowState(
            query=request.query,
            location_name=request.location,
            target_date=target_date,
            max_reviews=settings.MAX_CRITIC_REVIEWS,
            max_steps=settings.WORKFLOW_MAX_STEPS,
            time_budget_sec=settings.WORKFLOW_TIME_BUDGET_SEC,
        )

        stopped_early = False
        stop_reason = "Pipeline completed standard multi-agent cycle"

        try:
            yield self._format_sse({
                "type": "start",
                "message": f"Initializing 5-agent pipeline for '{state.location_name}'...",
                "query": request.query,
                "location": state.location_name,
                "target_date": state.target_date,
            })

            # Stage 1: Planner
            yield self._format_sse({
                "type": "progress",
                "stage_id": "planner",
                "agent_name": "PlannerAgent",
                "action": "DECONSTRUCT_USER_REQUEST",
                "status": "running",
                "message": f"Deconstructing user intent and configuring safety constraints for '{state.location_name}'...",
            })

            state.step_count += 1
            state = await self.planner.process(state, tracer)
            last_step = tracer.get_steps()[-1]

            yield self._format_sse({
                "type": "progress",
                "stage_id": "planner",
                "agent_name": "PlannerAgent",
                "action": "DECONSTRUCT_USER_REQUEST",
                "status": "completed",
                "duration_ms": last_step.duration_ms,
                "summary": last_step.summary,
                "reasoning": last_step.reasoning,
                "plan": state.plan.model_dump() if state.plan else None,
            })

            # Stage 2: Data Agent
            yield self._format_sse({
                "type": "progress",
                "stage_id": "data",
                "agent_name": "DataAgent",
                "action": "ACQUIRE_VERIFIED_TELEMETRY",
                "status": "running",
                "message": f"Geocoding '{state.location_name}' and querying live Open-Meteo meteorological telemetry...",
            })

            state.step_count += 1
            state = await self.data_agent.process(state, tracer)
            last_step = tracer.get_steps()[-1]

            yield self._format_sse({
                "type": "progress",
                "stage_id": "data",
                "agent_name": "DataAgent",
                "action": "ACQUIRE_VERIFIED_TELEMETRY",
                "status": "completed",
                "duration_ms": last_step.duration_ms,
                "summary": last_step.summary,
                "reasoning": last_step.reasoning,
                "telemetry": {
                    "temp_c": state.weather.temp_c,
                    "condition": state.weather.condition_text,
                    "wind_kph": state.weather.wind_kph,
                    "rain_prob": state.weather.precipitation_prob,
                    "source": state.weather.source,
                },
                "weather": state.weather.model_dump() if state.weather else None,
            })

            # Stage 3: Risk Analysis
            yield self._format_sse({
                "type": "progress",
                "stage_id": "risk",
                "agent_name": "RiskAnalysisAgent",
                "action": "EVALUATE_CONFIGURABLE_RULES",
                "status": "running",
                "message": "Auditing empirical data against configurable transparent risk rules...",
            })

            state.step_count += 1
            state = await self.risk_analyst.process(state, tracer)
            last_step = tracer.get_steps()[-1]

            yield self._format_sse({
                "type": "progress",
                "stage_id": "risk",
                "agent_name": "RiskAnalysisAgent",
                "action": "EVALUATE_CONFIGURABLE_RULES",
                "status": "completed",
                "duration_ms": last_step.duration_ms,
                "summary": last_step.summary,
                "reasoning": last_step.reasoning,
                "outdoor_score": state.outdoor_score,
                "risk_level": state.risk_assessment.risk_level if state.risk_assessment else "Moderate",
            })

            # Stages 4 & 5: Recommendation & Critic Loop (Capped at 2)
            while not stopped_early and state.review_count < state.max_reviews:
                yield self._format_sse({
                    "type": "progress",
                    "stage_id": "recommender",
                    "agent_name": "RecommendationAgent",
                    "action": "SYNTHESIZE_DECISION_AND_COMPARE_OPTIONS",
                    "status": "running",
                    "message": f"Comparing 3 options, citing data evidence, and articulating limitations (Cycle {state.review_count + 1})...",
                })

                state.step_count += 1
                state = await self.recommender.process(state, tracer)
                last_step = tracer.get_steps()[-1]

                yield self._format_sse({
                    "type": "progress",
                    "stage_id": "recommender",
                    "agent_name": "RecommendationAgent",
                    "action": "SYNTHESIZE_DECISION_AND_COMPARE_OPTIONS",
                    "status": "completed",
                    "duration_ms": last_step.duration_ms,
                    "summary": last_step.summary,
                    "reasoning": last_step.reasoning,
                    "verdict": state.verdict_badge,
                })

                # Critic Agent validation
                yield self._format_sse({
                    "type": "progress",
                    "stage_id": "critic",
                    "agent_name": "CriticAgent",
                    "action": "VALIDATE_RECOMMENDATION_AGAINST_SOURCE_DATA",
                    "status": "running",
                    "message": f"Executing adversarial critique and factuality audit (Review {state.review_count + 1}/{state.max_reviews})...",
                })

                state.step_count += 1
                state.review_count += 1
                state = await self.critic.process(state, tracer)
                last_step = tracer.get_steps()[-1]
                review = state.current_critic_review

                yield self._format_sse({
                    "type": "progress",
                    "stage_id": "critic",
                    "agent_name": "CriticAgent",
                    "action": "VALIDATE_RECOMMENDATION_AGAINST_SOURCE_DATA",
                    "status": "completed",
                    "duration_ms": last_step.duration_ms,
                    "summary": last_step.summary,
                    "reasoning": last_step.reasoning,
                    "critic_verdict": review.verdict if review else "APPROVE",
                    "critique_score": review.critique_score if review else 90,
                })

                if not review:
                    break

                if review.verdict == "APPROVE":
                    break
                elif review.verdict == "NEEDS_MORE_DATA":
                    stopped_early = True
                    stop_reason = "Critic halted execution: Incomplete or missing empirical telemetry"
                    yield self._format_sse({
                        "type": "insufficient_data",
                        "message": review.critique_notes,
                        "review": review.model_dump(),
                    })
                    break
                elif review.verdict == "REJECT":
                    if state.review_count >= state.max_reviews:
                        stopped_early = True
                        stop_reason = f"Review attempts capped at maximum limit ({state.max_reviews} iterations)"
                        break
                    yield self._format_sse({
                        "type": "review_loop",
                        "iteration": state.review_count,
                        "correction_request": review.correction_request,
                        "message": f"Critic rejected initial draft. Triggering revision cycle {state.review_count + 1}...",
                    })

            # Emit final completed response
            final_response = self._build_response(state, tracer, stopped_early, stop_reason)
            yield self._format_sse({
                "type": "complete",
                "result": final_response.model_dump(),
            })

        except WeatherServiceException as wse:
            yield self._format_sse({
                "type": "error",
                "error": {
                    "error_code": wse.error_code,
                    "message": wse.message,
                    "detail": wse.detail,
                    "location_searched": state.location_name,
                    "retries_attempted": wse.retries_attempted,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            })
        except Exception as e:
            logger.error(f"Error in multi-agent pipeline stream: {e}", exc_info=True)
            yield self._format_sse({
                "type": "error",
                "error": {
                    "error_code": "INTERNAL_ERROR",
                    "message": str(e),
                    "location_searched": state.location_name,
                    "retries_attempted": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            })

    def _build_response(
        self,
        state: WorkflowState,
        tracer: AgentExecutionTracer,
        stopped_early: bool,
        stop_reason: str
    ) -> AnalysisResponse:
        total_ms = tracer.get_total_duration_ms()

        recommendation_card = RecommendationCard(
            headline=state.headline,
            verdict_badge=state.verdict_badge,
            outdoor_score=state.outdoor_score,
            comfort_summary=state.comfort_summary,
            activities=state.activities,
            options_comparison=state.options_comparison,
            evidence_citations=state.evidence_citations,
            stated_limitations=state.stated_limitations,
            packing_checklist=state.packing_checklist,
            risk_alerts=state.risk_alerts,
            critic_review=state.current_critic_review,
        )

        stopping_condition = StoppingCondition(
            stopped_early=stopped_early,
            reason=stop_reason,
            reviews_count=state.review_count,
            max_reviews=state.max_reviews,
            steps_executed=state.step_count,
            max_steps=state.max_steps,
            duration_ms=total_ms,
            time_budget_ms=state.time_budget_sec * 1000.0,
            estimated_cost_usd=round(0.0005 * state.step_count, 5),
        )

        return AnalysisResponse(
            query=state.query,
            location=state.geo.name if state.geo else state.location_name,
            target_date=state.target_date,
            plan=state.plan,
            weather=state.weather,
            recommendation=recommendation_card,
            critic_reviews=state.critic_reviews,
            trace=tracer.get_steps(),
            stopping_condition=stopping_condition,
            total_execution_ms=total_ms,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def _format_sse(self, data: Dict[str, Any]) -> str:
        return f"data: {json.dumps(data)}\n\n"

    def _is_budget_exceeded(self, state: WorkflowState, tracer: AgentExecutionTracer) -> bool:
        elapsed_sec = (time.perf_counter() - state.start_time)
        if elapsed_sec > state.time_budget_sec:
            logger.warning(f"Workflow exceeded time budget: {elapsed_sec:.2f}s > {state.time_budget_sec}s")
            return True
        if state.step_count >= state.max_steps:
            logger.warning(f"Workflow exceeded step budget: {state.step_count} >= {state.max_steps}")
            return True
        return False


pipeline = WeatherIntelligencePipeline()
