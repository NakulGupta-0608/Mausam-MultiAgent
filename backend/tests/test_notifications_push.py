import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pywebpush import WebPushException
from requests.exceptions import RequestException, ConnectTimeout

from backend.main import app
from backend.app.storage.db import db
from backend.app.schemas.notification import (
    CreateNotificationRequest,
    PushSubscriptionRequest,
    PushSubscriptionKeys,
    UserNotificationPreferences,
    SimulateNotificationRequest,
)
from backend.app.monitoring.push_service import push_service

client = TestClient(app)


def test_persistent_in_app_notification_diff_and_link():
    """Verify in-app notification persists previous vs new values, reason, and link to saved item."""
    uid = uuid.uuid4().hex[:8]
    req = CreateNotificationRequest(
        category="warning",
        title="Atmospheric Alert: Rapid Rain Influx",
        message="Precipitation probability jumped above threshold.",
        location="Manali, HP",
        severity="warning",
        dedupe_key=f"test-diff-{uid}",
        plan_id=f"plan-{uid}",
        link=f"/#plan-{uid}",
        previous_value="Precip: 10%, Rain: 0.0mm",
        new_value="Precip: 80%, Rain: 12.5mm",
        reason="Precipitation probability increased by 70%, exceeding 15% threshold",
        is_simulated=False,
        critic_review_approved=True,
    )

    item, was_created = db.add_notification(req)
    assert was_created is True
    assert item.previous_value == "Precip: 10%, Rain: 0.0mm"
    assert item.new_value == "Precip: 80%, Rain: 12.5mm"
    assert item.reason == "Precipitation probability increased by 70%, exceeding 15% threshold"
    assert item.link == f"/#plan-{uid}"
    assert item.is_simulated is False
    assert item.critic_review_approved is True
    assert item.read is False

    # Fetch from API
    response = client.get("/api/notifications")
    assert response.status_code == 200
    all_notifs = response.json()
    matched = next((n for n in all_notifs if n["id"] == item.id), None)
    assert matched is not None
    assert matched["previous_value"] == req.previous_value
    assert matched["new_value"] == req.new_value
    assert matched["reason"] == req.reason
    assert matched["link"] == req.link


def test_notification_deduplication():
    """Verify that duplicate notifications with identical dedupe_key are suppressed."""
    uid = uuid.uuid4().hex[:8]
    key = f"dedupe-unique-{uid}"
    req1 = CreateNotificationRequest(
        category="alert",
        title="High Wind Warning",
        message="Wind gust alert",
        location="Leh",
        severity="danger",
        dedupe_key=key,
        plan_id=f"plan-{uid}",
    )
    req2 = CreateNotificationRequest(
        category="alert",
        title="High Wind Warning Duplicate",
        message="Wind gust alert duplicate",
        location="Leh",
        severity="danger",
        dedupe_key=key,
        plan_id=f"plan-{uid}",
    )

    item1, was_created1 = db.add_notification(req1)
    item2, was_created2 = db.add_notification(req2)

    assert was_created1 is True
    assert was_created2 is False
    assert item1.id == item2.id


def test_notification_history_read_unread():
    """Verify marking notifications as read individually and in bulk."""
    uid = uuid.uuid4().hex[:8]
    req = CreateNotificationRequest(
        category="advisory",
        title="Clear Skies Ahead",
        message="Optimal weather conditions forecasted.",
        location="Goa",
        severity="info",
        dedupe_key=f"test-read-status-{uid}",
    )
    item, _ = db.add_notification(req)
    assert item.read is False

    # Mark as read
    res = client.patch(f"/api/notifications/{item.id}/read")
    assert res.status_code == 200
    assert res.json()["read"] is True

    # Mark all read
    res_all = client.post("/api/notifications/read-all")
    assert res_all.status_code == 200
    assert "marked_read" in res_all.json()


def test_review_gated_delivery_rejection():
    """Verify that unapproved notifications (critic_review_approved=False) are rejected by the API."""
    req = {
        "category": "warning",
        "title": "Unverified Warning",
        "message": "This update failed critic verification.",
        "severity": "warning",
        "critic_review_approved": False,
    }
    response = client.post("/api/notifications", json=req)
    assert response.status_code == 400
    assert "Critic review has not approved" in response.json()["detail"]


def test_web_push_subscription_management():
    """Verify registering, listing, and deactivating Web Push subscriptions."""
    uid = uuid.uuid4().hex[:8]
    endpoint = f"https://fcm.googleapis.com/fcm/send/test-sub-{uid}"
    sub_req = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QT9t0A4If770M36k5b...",
            "auth": "tBHItJI5svbp5a10HR0Uaw==",
        },
        "user_agent": "Mozilla/5.0 Chrome/120.0",
    }

    # Register subscription
    res = client.post("/api/notifications/subscribe", json=sub_req)
    assert res.status_code == 200
    sub_data = res.json()
    assert sub_data["endpoint"] == endpoint
    assert sub_data["is_active"] is True

    # List subscriptions
    active_subs = db.get_active_push_subscriptions()
    assert any(s.endpoint == endpoint for s in active_subs)

    # Unsubscribe
    unsub_res = client.post("/api/notifications/unsubscribe", json={"endpoint": endpoint})
    assert unsub_res.status_code == 200
    assert unsub_res.json()["deactivated"] is True

    # Verify no longer active
    active_subs_after = db.get_active_push_subscriptions()
    assert not any(s.endpoint == endpoint for s in active_subs_after)


def test_push_delivery_failure_expired_subscription_410():
    """Failure Mode Test: Expired push subscription (HTTP 410 Gone) triggers automatic deactivation."""
    uid = uuid.uuid4().hex[:8]
    endpoint = f"https://updates.push.services.mozilla.com/wpush/v1/expired-{uid}"
    db.save_push_subscription(
        PushSubscriptionRequest(
            endpoint=endpoint,
            keys=PushSubscriptionKeys(p256dh="mock_p256dh", auth="mock_auth"),
            user_agent="Firefox Test",
        )
    )
    assert any(s.endpoint == endpoint for s in db.get_active_push_subscriptions())

    # Mock WebPushException with HTTP 410 (Gone / Expired)
    mock_response = MagicMock()
    mock_response.status_code = 410
    mock_ex = WebPushException("Push subscription has expired", response=mock_response)

    with patch("backend.app.monitoring.push_service.webpush", side_effect=mock_ex):
        item, _ = db.add_notification(
            CreateNotificationRequest(
                category="alert",
                title="Severe Rain Warning",
                message="Heavy rainfall incoming",
                severity="danger",
                dedupe_key=f"test-push-fail-410-{uid}",
            )
        )
        summary = push_service.send_push_notification(item)

    assert summary["expired"] >= 1
    # Verify the expired subscription was automatically deactivated
    active_after = db.get_active_push_subscriptions()
    assert not any(s.endpoint == endpoint for s in active_after)


def test_push_delivery_failure_unregistered_worker_404():
    """Failure Mode Test: Unregistered service worker (HTTP 404) triggers automatic deactivation."""
    uid = uuid.uuid4().hex[:8]
    endpoint = f"https://fcm.googleapis.com/fcm/send/unregistered-{uid}"
    db.save_push_subscription(
        PushSubscriptionRequest(
            endpoint=endpoint,
            keys=PushSubscriptionKeys(p256dh="mock_p256dh", auth="mock_auth"),
            user_agent="Chrome Test",
        )
    )

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_ex = WebPushException("Service worker is not registered", response=mock_response)

    with patch("backend.app.monitoring.push_service.webpush", side_effect=mock_ex):
        item, _ = db.add_notification(
            CreateNotificationRequest(
                category="warning",
                title="Temperature Surge",
                message="Heat spike",
                severity="warning",
                dedupe_key=f"test-push-fail-404-{uid}",
            )
        )
        summary = push_service.send_push_notification(item)

    assert summary["expired"] >= 1
    active_after = db.get_active_push_subscriptions()
    assert not any(s.endpoint == endpoint for s in active_after)


def test_push_delivery_failure_network_error_graceful_handling():
    """Failure Mode Test: Network failure/timeout during push does not crash and logs error."""
    uid = uuid.uuid4().hex[:8]
    endpoint = f"https://push.example.com/network-timeout-{uid}"
    db.save_push_subscription(
        PushSubscriptionRequest(
            endpoint=endpoint,
            keys=PushSubscriptionKeys(p256dh="mock_p256dh", auth="mock_auth"),
            user_agent="Network Test",
        )
    )

    with patch("backend.app.monitoring.push_service.webpush", side_effect=ConnectTimeout("Push gateway unreachable")):
        item, _ = db.add_notification(
            CreateNotificationRequest(
                category="advisory",
                title="UV Advisory",
                message="High UV index",
                severity="info",
                dedupe_key=f"test-push-network-err-{uid}",
            )
        )
        summary = push_service.send_push_notification(item)

    assert summary["failed"] >= 1


def test_dev_mode_simulation_endpoint():
    """Verify dev-mode simulation endpoint on demand: [SIMULATED] labeling, diff values, and review gating."""
    # 1. Test Review Gating with REJECT verdict
    reject_sim = {
        "metric": "Precipitation Probability",
        "previous_value": "Precip: 10%",
        "new_value": "Precip: 90%",
        "reason": "Sudden cloudburst probability spike",
        "severity": "danger",
        "critic_verdict": "REJECT",
        "send_push": False,
    }
    reject_res = client.post("/api/notifications/simulate", json=reject_sim)
    assert reject_res.status_code == 200
    reject_data = reject_res.json()
    assert reject_data["status"] == "suppressed"
    assert reject_data["notification"] is None
    assert "review-gated delivery enforced" in reject_data["message"].lower()

    # 2. Test Review Gating with APPROVE verdict
    approve_sim = {
        "metric": "Wind Speed",
        "previous_value": "Wind: 12 km/h",
        "new_value": "Wind: 48 km/h",
        "reason": "Gale-force gusts detected exceeding safe threshold (15 km/h)",
        "severity": "danger",
        "critic_verdict": "APPROVE",
        "send_push": False,
    }
    approve_res = client.post("/api/notifications/simulate", json=approve_sim)
    assert approve_res.status_code == 200
    approve_data = approve_res.json()
    assert approve_data["status"] == "success"
    assert approve_data["is_simulated"] is True
    notif = approve_data["notification"]
    assert "[SIMULATED]" in notif["title"]
    assert notif["is_simulated"] is True
    assert notif["previous_value"] == "Wind: 12 km/h"
    assert notif["new_value"] == "Wind: 48 km/h"
    assert notif["critic_review_approved"] is True
    assert notif["link"] is not None


def test_user_notification_preferences_get_and_put():
    """Verify user configurable notification preferences."""
    # Fetch default preferences
    get_res = client.get("/api/notifications/preferences")
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert "browser_push_enabled" in prefs
    assert "min_severity" in prefs

    # Update preferences
    updated_prefs = {
        "in_app_enabled": True,
        "browser_push_enabled": False,
        "min_severity": "warning",
        "notify_on_weather_change": True,
        "notify_on_verdict_change": True,
    }
    put_res = client.put("/api/notifications/preferences", json=updated_prefs)
    assert put_res.status_code == 200
    assert put_res.json()["browser_push_enabled"] is False
    assert put_res.json()["min_severity"] == "warning"

    # Reset
    client.put(
        "/api/notifications/preferences",
        json={
            "in_app_enabled": True,
            "browser_push_enabled": True,
            "min_severity": "info",
            "notify_on_weather_change": True,
            "notify_on_verdict_change": True,
        },
    )
