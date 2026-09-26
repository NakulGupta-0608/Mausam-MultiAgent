from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.weather import WeatherCondition, GeoLocation
from backend.app.schemas.analysis import ActivityRecommendation, RiskItem


class WorkflowState(BaseModel):
    query: str
    location_name: str
    target_date: str

    geo: Optional[GeoLocation] = None
    weather: Optional[WeatherCondition] = None

    outdoor_score: int = 70
    headline: str = ""
    verdict_badge: str = "Optimal"
    comfort_summary: str = ""

    activities: List[ActivityRecommendation] = Field(default_factory=list)
    packing_checklist: List[str] = Field(default_factory=list)
    risk_alerts: List[RiskItem] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)
