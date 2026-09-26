from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WeatherSnapshot(BaseModel):
    """Snapshot of meteorological telemetry at time of plan saving or last check."""
    temp_c: float
    feels_like_c: float
    humidity: int
    wind_kph: float
    wind_direction: str = "NW"
    precipitation_prob: int
    precipitation_mm: float = 0.0
    uv_index: float = 0.0
    condition_text: str
    source: str = "open-meteo"
    captured_at: str


class RecommendationSnapshot(BaseModel):
    """Snapshot of recommendation state (verdict, score, summary, and limitations)."""
    verdict_badge: str  # Optimal, Caution, Unfavorable, Severe
    outdoor_score: int  # 0 to 100
    headline: str
    comfort_summary: str
    packing_checklist: List[str] = Field(default_factory=list)
    options_comparison: List[Dict[str, Any]] = Field(default_factory=list)
    stated_limitations: List[str] = Field(default_factory=list)
    critic_verdict: Optional[str] = "APPROVE"


class NotificationPreferences(BaseModel):
    """User-configured notification and sensitivity thresholds for smart monitoring."""
    notify_on_verdict_change: bool = True
    notify_on_score_drop: bool = True
    notify_on_severe_weather: bool = True
    temp_threshold_c: float = 3.0
    rain_threshold_pct: int = 15
    wind_threshold_kph: float = 12.0
    uv_threshold: float = 2.0
    score_drop_threshold_pts: int = 12


class DetectedChange(BaseModel):
    """Audit log item representing a detected meaningful change in weather telemetry or verdict."""
    id: str
    timestamp: str
    metric: str  # e.g., "Precipitation Probability", "Wind Speed", "Verdict Shift"
    old_value: str
    new_value: str
    delta: Optional[str] = None
    significance_reason: str


class CreatePlanRequest(BaseModel):
    """Payload to save an expedition/activity plan for smart monitoring."""
    subject: str = Field(..., description="Subject or title of the plan (e.g. 'Alpine Sunrise Hike')")
    location: str = Field(..., description="Target location name (e.g. 'Shimla')")
    action: str = Field(default="Outdoor Activity", description="Action or activity (e.g. 'Trekking', 'Cycling')")
    target_date: str = Field(..., description="Target date in YYYY-MM-DD format")
    query: Optional[str] = Field(default="", description="Original natural-language user query")
    original_data_snapshot: Dict[str, Any] = Field(..., description="Telemetry snapshot at save time")
    initial_recommendation: Dict[str, Any] = Field(..., description="Initial recommendation at save time")
    notification_preferences: Optional[NotificationPreferences] = Field(
        default_factory=NotificationPreferences,
        description="Notification and threshold preferences"
    )
    # Backwards compatibility fields
    title: Optional[str] = None
    verdict: Optional[str] = None
    outdoor_score: Optional[int] = None
    summary: Optional[str] = None
    packing_checklist: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class SavedPlan(BaseModel):
    """Persistent user plan with monitoring state and change history."""
    id: str
    subject: str
    location: str
    action: str
    target_date: str
    query: str = ""
    status: str = "active"  # "active", "paused", "expired", "completed"
    original_data_snapshot: Dict[str, Any]
    initial_recommendation: Dict[str, Any]
    current_recommendation: Dict[str, Any]
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences)
    detected_changes: List[DetectedChange] = Field(default_factory=list)
    check_count: int = 0
    re_analysis_count: int = 0
    last_checked_at: Optional[str] = None
    last_changed_at: Optional[str] = None
    created_at: str
    updated_at: str

    # Helper properties for backwards compatibility with previous components
    @property
    def title(self) -> str:
        return self.subject

    @property
    def verdict(self) -> str:
        return self.current_recommendation.get("verdict_badge", "Caution")

    @property
    def outdoor_score(self) -> int:
        return self.current_recommendation.get("outdoor_score", 50)

    @property
    def summary(self) -> str:
        return self.current_recommendation.get("comfort_summary", "")

    @property
    def packing_checklist(self) -> List[str]:
        return self.current_recommendation.get("packing_checklist", [])

    @property
    def tags(self) -> List[str]:
        return [self.action, self.verdict]


class CheckPlanResponse(BaseModel):
    """Response returned when a plan is checked (either manually or by scheduler)."""
    plan_id: str
    checked_at: str
    status: str
    significant_change_detected: bool
    changes: List[DetectedChange] = Field(default_factory=list)
    re_analyzed: bool = False
    notification_emitted: bool = False
    plan: SavedPlan
