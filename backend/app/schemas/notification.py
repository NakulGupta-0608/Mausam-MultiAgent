from typing import Optional
from pydantic import BaseModel, Field


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = None


class PushSubscriptionItem(BaseModel):
    id: str
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None
    is_active: bool = True
    failure_count: int = 0
    created_at: str


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


class UserNotificationPreferences(BaseModel):
    in_app_enabled: bool = True
    browser_push_enabled: bool = True
    min_severity: str = Field(default="info", description="info, warning, danger")
    notify_on_weather_change: bool = True
    notify_on_verdict_change: bool = True


class CreateNotificationRequest(BaseModel):
    category: str = Field(default="advisory", description="advisory, warning, alert, system")
    title: str
    message: str
    location: Optional[str] = None
    severity: str = Field(default="info", description="info, warning, danger, success")
    dedupe_key: Optional[str] = Field(default=None, description="Idempotency key for alert deduplication")
    plan_id: Optional[str] = Field(default=None, description="Linked plan ID if triggered by smart monitoring")
    link: Optional[str] = Field(default=None, description="Navigation link to saved item / plan")
    previous_value: Optional[str] = Field(default=None, description="Human-readable previous value")
    new_value: Optional[str] = Field(default=None, description="Human-readable new value")
    reason: Optional[str] = Field(default=None, description="Reason for the atmospheric or recommendation shift")
    is_simulated: bool = Field(default=False, description="Flag indicating simulated notification (dev mode)")
    critic_review_approved: bool = Field(default=True, description="True if passed Critic Agent review")


class NotificationItem(BaseModel):
    id: str
    category: str
    title: str
    message: str
    location: Optional[str] = None
    severity: str
    read: bool = False
    dedupe_key: Optional[str] = None
    plan_id: Optional[str] = None
    link: Optional[str] = None
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None
    is_simulated: bool = False
    critic_review_approved: bool = True
    created_at: str


class SimulateNotificationRequest(BaseModel):
    plan_id: Optional[str] = None
    title: Optional[str] = None
    metric: str = Field(default="Precipitation Probability", description="Metric being changed")
    previous_value: Optional[str] = "Precipitation: 10% (0.0mm)"
    new_value: Optional[str] = "Precipitation: 85% (14.2mm)"
    reason: Optional[str] = "Precipitation probability jumped +75% (threshold: 15%)"
    severity: str = Field(default="warning", description="info, warning, danger")
    critic_verdict: str = Field(default="APPROVE", description="APPROVE to send notification, REJECT to test review-gating suppression")
    send_push: bool = Field(default=True, description="Whether to trigger Web Push API delivery to browser")
