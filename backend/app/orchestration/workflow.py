import asyncio
from datetime import datetime, timezone
from backend.app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    RecommendationCard,
)
from backend.app.orchestration.state import WorkflowState
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.agents.weather_analyst import WeatherAnalystAgent
from backend.app.agents.activity_planner import ActivityPlannerAgent
from backend.app.agents.risk_assessor import RiskAssessorAgent
from backend.app.monitoring.logger import logger


class WeatherIntelligencePipeline:
    """Orchestrates multi-agent analysis for weather intelligence."""

    def __init__(self):
        self.weather_agent = WeatherAnalystAgent()
        self.planner_agent = ActivityPlannerAgent()
        self.risk_agent = RiskAssessorAgent()

    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        tracer = AgentExecutionTracer()
        target_date = request.target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        logger.info(f"Starting Multi-Agent Workflow for '{request.location}' on {target_date} (Query: '{request.query}')")

        state = WorkflowState(
            query=request.query,
            location_name=request.location,
            target_date=target_date,
        )

        # Agent 1: Weather Analyst
        state = await self.weather_agent.process(state, tracer)

        # Agent 2: Activity Planner
        state = await self.planner_agent.process(state, tracer)

        # Agent 3: Risk Assessor
        state = await self.risk_agent.process(state, tracer)

        total_ms = tracer.get_total_duration_ms()

        recommendation = RecommendationCard(
            headline=state.headline,
            verdict_badge=state.verdict_badge,
            outdoor_score=state.outdoor_score,
            comfort_summary=state.comfort_summary,
            activities=state.activities,
            packing_checklist=state.packing_checklist,
            risk_alerts=state.risk_alerts,
        )

        response = AnalysisResponse(
            query=state.query,
            location=state.geo.name if state.geo else state.location_name,
            target_date=state.target_date,
            weather=state.weather,
            recommendation=recommendation,
            trace=tracer.get_steps(),
            total_execution_ms=total_ms,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(f"Pipeline finished successfully in {total_ms}ms with verdict {state.verdict_badge}")
        return response


pipeline = WeatherIntelligencePipeline()
