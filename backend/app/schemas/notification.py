from typing import Optional
from pydantic import BaseModel, Field


class CreateNotificationRequest(BaseModel):
    category: str = Field(default="advisory", description="advisory, warning, alert, system")
    title: str
    message: str
    location: Optional[str] = None
    severity: str = Field(default="info", description="info, warning, danger, success")
    dedupe_key: Optional[str] = Field(default=None, description="Idempotency key for alert deduplication")
    plan_id: Optional[str] = Field(default=None, description="Linked plan ID if triggered by smart monitoring")


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
    created_at: str
