from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .weather import WeatherCondition


class AnalysisRequest(BaseModel):
    query: str = Field(..., description="User query or planned activity (e.g., 'Can I go hiking?', 'Outdoor wedding planning')")
    location: str = Field(..., description="Target city or location name (e.g., 'Shimla', 'San Francisco')")
    target_date: Optional[str] = Field(default=None, description="Target date in YYYY-MM-DD format. Defaults to today/tomorrow.")


class AgentTraceStep(BaseModel):
    id: str
    agent_name: str
    stage: str
    status: str  # "completed", "running", "failed"
    duration_ms: float
    timestamp: str
    summary: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)


class RiskItem(BaseModel):
    severity: str  # "low", "moderate", "high", "critical"
    title: str
    description: str
    mitigation: str


class ActivityRecommendation(BaseModel):
    activity: str
    verdict: str  # "Recommended", "Conditional", "Not Recommended"
    confidence_score: int  # 0 to 100
    reasoning: str
    ideal_time_window: str
    gear_required: List[str] = Field(default_factory=list)
    alternatives: List[str] = Field(default_factory=list)


class RecommendationCard(BaseModel):
    headline: str
    verdict_badge: str  # "Optimal", "Caution", "Unfavorable", "Severe"
    outdoor_score: int  # 0-100
    comfort_summary: str
    activities: List[ActivityRecommendation] = Field(default_factory=list)
    packing_checklist: List[str] = Field(default_factory=list)
    risk_alerts: List[RiskItem] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    query: str
    location: str
    target_date: str
    weather: WeatherCondition
    recommendation: RecommendationCard
    trace: List[AgentTraceStep] = Field(default_factory=list)
    total_execution_ms: float
    generated_at: str
