import time
import asyncio
from datetime import datetime, timezone
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
from backend.app.monitoring.logger import logger


class WeatherIntelligencePipeline:
    """Central orchestrator coordinating the five agents with planning, execution, and critique loops.
    
    Enforces review attempt capping (max 2), step/time/cost budgets, and complete audit tracing.
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.data_agent = DataAgent()
        self.risk_analyst = RiskAnalysisAgent()
        self.recommender = RecommendationAgent()
        self.critic = CriticAgent()

    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        tracer = AgentExecutionTracer()
        start_wall_time = time.perf_counter()
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

        # -------------------------------------------------------------
        # Step 1: Planner Agent (Deconstructs intent into task plan)
        # -------------------------------------------------------------
        state.step_count += 1
        state = await self.planner.process(state, tracer)

        # Budget Check
        if self._is_budget_exceeded(state, tracer):
            stopped_early = True
            stop_reason = "Budget ceiling reached after planning stage"

        # -------------------------------------------------------------
        # Step 2: Data Agent (Fetches real empirical telemetry)
        # -------------------------------------------------------------
        if not stopped_early:
            state.step_count += 1
            state = await self.data_agent.process(state, tracer)

            if not state.weather:
                stopped_early = True
                stop_reason = "DataAgent could not verify real empirical telemetry"

        # -------------------------------------------------------------
        # Step 3: Risk/Analysis Agent (Configurable transparent rules)
        # -------------------------------------------------------------
        if not stopped_early:
            state.step_count += 1
            state = await self.risk_analyst.process(state, tracer)

        # -------------------------------------------------------------
        # Steps 4 & 5: Recommendation & Critic Iteration Loop
        # Cap review attempts at two (max_reviews = 2)
        # -------------------------------------------------------------
        while not stopped_early and state.review_count < state.max_reviews:
            # 4a: Recommendation Agent (Options, Evidence Citations, Limitations)
            state.step_count += 1
            state = await self.recommender.process(state, tracer)

            # Check budgets before critique
            if self._is_budget_exceeded(state, tracer):
                stopped_early = True
                stop_reason = "Time or step budget reached during recommendation phase"
                break

            # 4b: Critic Agent (Validates against source data)
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
                # Loop continues to recommender with active_correction_request

        total_ms = tracer.get_total_duration_ms()

        # Build final RecommendationCard
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

        response = AnalysisResponse(
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

        logger.info(
            f"=== Pipeline Completed in {total_ms}ms ({state.step_count} steps, "
            f"{state.review_count} reviews, Critic: {state.current_critic_review.verdict if state.current_critic_review else 'N/A'}) ==="
        )
        return response

    def _is_budget_exceeded(self, state: WorkflowState, tracer: AgentExecutionTracer) -> bool:
        """Enforces time budget and step count budget stopping conditions."""
        elapsed_sec = (time.perf_counter() - state.start_time)
        if elapsed_sec > state.time_budget_sec:
            logger.warning(f"Workflow exceeded time budget: {elapsed_sec:.2f}s > {state.time_budget_sec}s")
            return True
        if state.step_count >= state.max_steps:
            logger.warning(f"Workflow exceeded step budget: {state.step_count} >= {state.max_steps}")
            return True
        return False


pipeline = WeatherIntelligencePipeline()
