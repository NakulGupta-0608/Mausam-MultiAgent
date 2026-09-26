from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.notification import NotificationItem, CreateNotificationRequest
from backend.app.storage.db import db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationItem])
async def list_notifications():
    return db.list_notifications()


@router.post("", response_model=NotificationItem)
async def create_notification(request: CreateNotificationRequest):
    item, _ = db.add_notification(request)
    return item


@router.patch("/{notif_id}/read", response_model=NotificationItem)
async def mark_read(notif_id: str):
    item = db.mark_notification_read(notif_id)
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item


@router.post("/read-all")
async def mark_all_read():
    count = db.mark_all_notifications_read()
    return {"status": "success", "marked_read": count}
