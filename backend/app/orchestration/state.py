import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.weather import WeatherCondition, GeoLocation
from backend.app.schemas.analysis import (
    StructuredPlan,
    RiskAssessmentResult,
    ActivityRecommendation,
    OptionComparison,
    EvidenceCitation,
    CriticReview,
    RiskItem,
)
from backend.app.core.config import settings


class WorkflowState(BaseModel):
    """Central shared state coordinating the five multi-agent components."""
    # User Request Input
    query: str
    location_name: str
    target_date: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Agent 1: Planner Agent output
    plan: Optional[StructuredPlan] = None

    # Agent 2: Data Agent output (Verified empirical telemetry)
    geo: Optional[GeoLocation] = None
    weather: Optional[WeatherCondition] = None

    # Agent 3: Risk/Analysis Agent output (Configurable transparent rules)
    risk_assessment: Optional[RiskAssessmentResult] = None
    outdoor_score: int = 70

    # Agent 4: Recommendation Agent output (Evidence-based decision + limitations)
    headline: str = ""
    verdict_badge: str = "Optimal"
    comfort_summary: str = ""
    activities: List[ActivityRecommendation] = Field(default_factory=list)
    options_comparison: List[OptionComparison] = Field(default_factory=list)
    evidence_citations: List[EvidenceCitation] = Field(default_factory=list)
    stated_limitations: List[str] = Field(default_factory=list)
    packing_checklist: List[str] = Field(default_factory=list)
    risk_alerts: List[RiskItem] = Field(default_factory=list)

    # Agent 5: Critic Agent reviews
    critic_reviews: List[CriticReview] = Field(default_factory=list)
    current_critic_review: Optional[CriticReview] = None
    active_correction_request: Optional[str] = None

    # Central Orchestrator Capping & Budget Tracking
    review_count: int = 0
    max_reviews: int = Field(default_factory=lambda: settings.MAX_CRITIC_REVIEWS)
    step_count: int = 0
    max_steps: int = Field(default_factory=lambda: settings.WORKFLOW_MAX_STEPS)
    start_time: float = Field(default_factory=time.perf_counter)
    time_budget_sec: float = Field(default_factory=lambda: settings.WORKFLOW_TIME_BUDGET_SEC)
    estimated_cost_usd: float = 0.001

    # Termination Status
    is_terminated: bool = False
    termination_reason: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)
