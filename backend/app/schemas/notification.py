from typing import Optional
from pydantic import BaseModel, Field


class CreateNotificationRequest(BaseModel):
    category: str = Field(default="advisory", description="advisory, warning, alert, system")
    title: str
    message: str
    location: Optional[str] = None
    severity: str = Field(default="info", description="info, warning, danger, success")


class NotificationItem(BaseModel):
    id: str
    category: str
    title: str
    message: str
    location: Optional[str] = None
    severity: str
    read: bool = False
    created_at: str
