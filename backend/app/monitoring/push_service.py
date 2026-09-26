import json
from typing import Dict, Any, List, Optional
from pywebpush import webpush, WebPushException
from requests.exceptions import RequestException

from backend.app.core.config import settings
from backend.app.storage.db import db
from backend.app.schemas.notification import NotificationItem
from backend.app.monitoring.logger import logger


class PushNotificationService:
    """Manages browser push notifications via Web Push API and VAPID.
    
    Ensures secure, review-gated delivery and robust error handling
    (expired subscriptions, unregistered workers, network errors).
    """

    def __init__(self):
        self.public_key = settings.VAPID_PUBLIC_KEY
        self.private_key = settings.VAPID_PRIVATE_KEY
        self.claim_email = settings.VAPID_CLAIM_EMAIL

    def get_public_key(self) -> str:
        """Returns the public VAPID key for frontend Service Worker subscription."""
        return self.public_key

    def send_push_notification(
        self,
        notification: NotificationItem,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, int]:
        """Broadcasts a push notification to all active browser subscriptions.
        
        Handles:
        - 404 / 410: Expired or unregistered subscription -> automatically deactivates
        - Network failures / timeouts -> recorded without crashing
        """
        active_subs = db.get_active_push_subscriptions()
        if not active_subs:
            logger.info("No active browser push subscriptions to deliver to.")
            return {"attempted": 0, "sent": 0, "expired": 0, "failed": 0}

        # Check user preference: browser push enabled?
        prefs = db.get_user_preferences()
        if not prefs.browser_push_enabled:
            logger.info("Browser push notifications are disabled in user preferences.")
            return {"attempted": 0, "sent": 0, "expired": 0, "failed": 0}

        # Build payload
        target_url = notification.link or f"/#plan-{notification.plan_id}" if notification.plan_id else "/"
        payload_data = {
            "title": notification.title,
            "body": notification.message,
            "icon": "/vite.svg",
            "badge": "/vite.svg",
            "tag": notification.dedupe_key or f"mausam-{notification.id}",
            "data": {
                "url": target_url,
                "notification_id": notification.id,
                "plan_id": notification.plan_id,
                "severity": notification.severity,
                "previous_value": notification.previous_value,
                "new_value": notification.new_value,
                "reason": notification.reason,
                **(extra_data or {}),
            },
        }
        payload_json = json.dumps(payload_data)

        sent_count = 0
        expired_count = 0
        failed_count = 0

        for sub in active_subs:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth,
                },
            }
            try:
                webpush(
                    subscription_info=sub_info,
                    data=payload_json,
                    vapid_private_key=self.private_key,
                    vapid_claims={"sub": self.claim_email},
                    ttl=86400,
                )
                sent_count += 1
                logger.info(f"Web Push sent to {sub.endpoint[:40]}... for alert '{notification.title}'")
            except WebPushException as ex:
                status_code = getattr(getattr(ex, "response", None), "status_code", None)
                if status_code in (404, 410):
                    # Subscription expired or service worker unregistered
                    expired_count += 1
                    db.record_push_failure(sub.endpoint, status_code=status_code)
                    logger.warning(f"Push subscription expired/unregistered (status {status_code}): {sub.endpoint[:40]}...")
                else:
                    failed_count += 1
                    db.record_push_failure(sub.endpoint, status_code=status_code)
                    logger.error(f"WebPush error (status {status_code}) sending to {sub.endpoint[:40]}...: {ex}")
            except (RequestException, Exception) as e:
                failed_count += 1
                db.record_push_failure(sub.endpoint, status_code=None)
                logger.error(f"Network or connection failure delivering push to {sub.endpoint[:40]}...: {e}")

        summary = {
            "attempted": len(active_subs),
            "sent": sent_count,
            "expired": expired_count,
            "failed": failed_count,
        }
        logger.info(f"Push broadcast summary for '{notification.title}': {summary}")
        return summary


push_service = PushNotificationService()
