from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from backend.app.schemas.notification import (
    NotificationItem,
    CreateNotificationRequest,
    PushSubscriptionRequest,
    PushSubscriptionItem,
    PushUnsubscribeRequest,
    UserNotificationPreferences,
    SimulateNotificationRequest,
)
from backend.app.storage.db import db
from backend.app.monitoring.push_service import push_service
from backend.app.monitoring.logger import logger

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationItem])
async def list_notifications(unread_only: bool = Query(default=False), limit: int = Query(default=100)):
    """Retrieves persistent notification history, optionally filtered by unread status."""
    return db.list_notifications(unread_only=unread_only, limit=limit)


@router.post("", response_model=NotificationItem)
async def create_notification(request: CreateNotificationRequest):
    """Creates a notification with review-gated enforcement and deduplication."""
    if not request.critic_review_approved:
        raise HTTPException(
            status_code=400,
            detail="Cannot dispatch notification: Critic review has not approved this update."
        )

    item, was_created = db.add_notification(request)
    if was_created:
        try:
            push_service.send_push_notification(item)
        except Exception as e:
            logger.error(f"Failed to broadcast push notification: {e}")
    return item


@router.patch("/{notif_id}/read", response_model=NotificationItem)
async def mark_read(notif_id: str):
    """Marks a single notification as read."""
    item = db.mark_notification_read(notif_id)
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found")
    return item


@router.post("/read-all")
async def mark_all_read():
    """Marks all notifications as read."""
    count = db.mark_all_notifications_read()
    return {"status": "success", "marked_read": count}


@router.delete("")
async def clear_all_notifications():
    """Clears all stored notifications."""
    count = db.clear_notifications()
    return {"status": "success", "deleted_count": count}


# =============================================================================
# Web Push Subscription Endpoints
# =============================================================================

@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Returns the VAPID public key required for browser push subscription."""
    return {"public_key": push_service.get_public_key()}


@router.post("/subscribe", response_model=PushSubscriptionItem)
async def subscribe_push(request: PushSubscriptionRequest):
    """Registers or re-activates a Web Push API browser subscription."""
    if not request.endpoint or not request.keys.p256dh or not request.keys.auth:
        raise HTTPException(status_code=400, detail="Invalid push subscription payload")
    sub = db.save_push_subscription(request)
    return sub


@router.post("/unsubscribe")
async def unsubscribe_push(request: PushUnsubscribeRequest):
    """Deactivates a browser Web Push subscription."""
    success = db.deactivate_push_subscription(request.endpoint)
    return {"status": "success", "deactivated": success}


@router.get("/subscriptions", response_model=List[PushSubscriptionItem])
async def list_active_subscriptions():
    """Lists all active browser push subscriptions."""
    return db.get_active_push_subscriptions()


# =============================================================================
# User Preferences Endpoints
# =============================================================================

@router.get("/preferences", response_model=UserNotificationPreferences)
async def get_preferences():
    """Returns user-configurable notification preferences."""
    return db.get_user_preferences()


@router.put("/preferences", response_model=UserNotificationPreferences)
async def update_preferences(prefs: UserNotificationPreferences):
    """Updates user-configurable notification preferences."""
    return db.update_user_preferences(prefs)


# =============================================================================
# Dev-Mode Simulation Endpoint
# =============================================================================

@router.post("/simulate")
async def simulate_change_notification(request: SimulateNotificationRequest):
    """Dev-mode endpoint to simulate an atmospheric shift and notification on demand.
    
    Clearly labels results with [SIMULATED], demonstrates review-gating (APPROVE vs REJECT),
    shows previous vs new telemetry, includes a link to the saved item, and triggers browser push.
    """
    plan = None
    if request.plan_id:
        plan = db.get_plan(request.plan_id)

    location_name = plan.location if plan else "Shimla, HP"
    plan_title = plan.subject if plan else "Alpine Mountain Trek"
    plan_id = plan.id if plan else "sim-plan-01"

    # 1. Review-gating verification
    if request.critic_verdict != "APPROVE":
        logger.warning(f"[SIMULATED] Notification blocked: Critic review verdict is '{request.critic_verdict}'")
        return {
            "status": "suppressed",
            "is_simulated": True,
            "critic_verdict": request.critic_verdict,
            "message": f"Notification delivery suppressed because Critic Agent returned '{request.critic_verdict}'. Review-gated delivery enforced.",
            "notification": None,
            "push_summary": {"attempted": 0, "sent": 0, "expired": 0, "failed": 0},
        }

    # 2. Build simulated notification
    title = request.title or f"[SIMULATED] Weather Alert for '{plan_title}'"
    message = (
        f"[SIMULATED] Meaningful change detected in {location_name}: {request.reason}. "
        f"Prior telemetry '{request.previous_value}' adjusted to current '{request.new_value}'."
    )

    now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    sim_dedupe_key = f"simulated:{plan_id}:{request.metric}:{now_str}"

    notif_req = CreateNotificationRequest(
        category="alert" if request.severity == "danger" else "warning",
        title=title,
        message=message,
        location=location_name,
        severity=request.severity,
        dedupe_key=sim_dedupe_key,
        plan_id=plan_id,
        link=f"/#plan-{plan_id}",
        previous_value=request.previous_value,
        new_value=request.new_value,
        reason=request.reason,
        is_simulated=True,
        critic_review_approved=True,
    )

    item, was_created = db.add_notification(notif_req)

    # 3. Trigger Web Push if requested
    push_summary = {"attempted": 0, "sent": 0, "expired": 0, "failed": 0}
    if request.send_push and was_created:
        try:
            push_summary = push_service.send_push_notification(item, extra_data={"simulated": True})
        except Exception as e:
            logger.error(f"[SIMULATED] Push delivery failed: {e}")

    return {
        "status": "success",
        "is_simulated": True,
        "critic_verdict": "APPROVE",
        "message": "Simulated change & review-approved notification dispatched successfully.",
        "notification": item,
        "push_summary": push_summary,
    }
