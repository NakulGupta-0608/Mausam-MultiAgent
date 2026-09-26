import sqlite3
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from backend.app.core.config import settings
from backend.app.schemas.plan import SavedPlan, CreatePlanRequest, NotificationPreferences, DetectedChange
from backend.app.schemas.notification import (
    NotificationItem,
    CreateNotificationRequest,
    PushSubscriptionRequest,
    PushSubscriptionItem,
    UserNotificationPreferences,
)
from backend.app.monitoring.logger import logger


class Database:
    """Thread-safe persistent SQLite storage for plans, notifications, push subscriptions, and preferences."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        # Ensure parent dir exists
        parent_dir = os.path.dirname(self.db_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    # Plans table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS plans (
                            id TEXT PRIMARY KEY,
                            subject TEXT NOT NULL,
                            location TEXT NOT NULL,
                            action TEXT NOT NULL,
                            target_date TEXT NOT NULL,
                            query TEXT,
                            status TEXT NOT NULL,
                            original_data_snapshot TEXT NOT NULL,
                            initial_recommendation TEXT NOT NULL,
                            current_recommendation TEXT NOT NULL,
                            notification_preferences TEXT NOT NULL,
                            detected_changes TEXT NOT NULL,
                            check_count INTEGER DEFAULT 0,
                            re_analysis_count INTEGER DEFAULT 0,
                            last_checked_at TEXT,
                            last_changed_at TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                    """)

                    # Notifications table with unique dedupe_key index
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS notifications (
                            id TEXT PRIMARY KEY,
                            category TEXT NOT NULL,
                            title TEXT NOT NULL,
                            message TEXT NOT NULL,
                            location TEXT,
                            severity TEXT NOT NULL,
                            read INTEGER DEFAULT 0,
                            dedupe_key TEXT UNIQUE,
                            plan_id TEXT,
                            link TEXT,
                            previous_value TEXT,
                            new_value TEXT,
                            reason TEXT,
                            is_simulated INTEGER DEFAULT 0,
                            critic_review_approved INTEGER DEFAULT 1,
                            created_at TEXT NOT NULL
                        );
                    """)

                    # Safe column migration for existing notification tables
                    cursor = conn.execute("PRAGMA table_info(notifications);")
                    existing_cols = {row["name"] for row in cursor.fetchall()}
                    migration_cols = [
                        ("link", "TEXT"),
                        ("previous_value", "TEXT"),
                        ("new_value", "TEXT"),
                        ("reason", "TEXT"),
                        ("is_simulated", "INTEGER DEFAULT 0"),
                        ("critic_review_approved", "INTEGER DEFAULT 1"),
                    ]
                    for col_name, col_type in migration_cols:
                        if col_name not in existing_cols:
                            conn.execute(f"ALTER TABLE notifications ADD COLUMN {col_name} {col_type};")

                    # Push Subscriptions table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS push_subscriptions (
                            id TEXT PRIMARY KEY,
                            endpoint TEXT UNIQUE NOT NULL,
                            p256dh TEXT NOT NULL,
                            auth TEXT NOT NULL,
                            user_agent TEXT,
                            is_active INTEGER DEFAULT 1,
                            failure_count INTEGER DEFAULT 0,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                    """)

                    # User Notification Preferences table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_notification_preferences (
                            id TEXT PRIMARY KEY,
                            in_app_enabled INTEGER DEFAULT 1,
                            browser_push_enabled INTEGER DEFAULT 1,
                            min_severity TEXT DEFAULT 'info',
                            notify_on_weather_change INTEGER DEFAULT 1,
                            notify_on_verdict_change INTEGER DEFAULT 1,
                            updated_at TEXT NOT NULL
                        );
                    """)

                    conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_status ON plans(status);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_plans_target_date ON plans(target_date);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_notif_created ON notifications(created_at);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_push_active ON push_subscriptions(is_active);")
            finally:
                conn.close()

    # =========================================================================
    # Plan Persistence Methods
    # =========================================================================

    def save_plan(self, req: CreatePlanRequest) -> SavedPlan:
        plan_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        prefs = req.notification_preferences or NotificationPreferences()

        # Handle backwards-compatible fields
        subject = req.subject or req.title or "Outdoor Expedition"
        action = req.action or "Outdoor Activity"
        orig_snapshot = req.original_data_snapshot or {}
        init_rec = req.initial_recommendation or {
            "verdict_badge": req.verdict or "Caution",
            "outdoor_score": req.outdoor_score or 50,
            "headline": subject,
            "comfort_summary": req.summary or "",
            "packing_checklist": req.packing_checklist or [],
        }

        plan = SavedPlan(
            id=plan_id,
            subject=subject,
            location=req.location,
            action=action,
            target_date=req.target_date,
            query=req.query or "",
            status="active",
            original_data_snapshot=orig_snapshot,
            initial_recommendation=init_rec,
            current_recommendation=init_rec,
            notification_preferences=prefs,
            detected_changes=[],
            check_count=0,
            re_analysis_count=0,
            last_checked_at=None,
            last_changed_at=None,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO plans (
                            id, subject, location, action, target_date, query, status,
                            original_data_snapshot, initial_recommendation, current_recommendation,
                            notification_preferences, detected_changes, check_count, re_analysis_count,
                            last_checked_at, last_changed_at, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        plan.id,
                        plan.subject,
                        plan.location,
                        plan.action,
                        plan.target_date,
                        plan.query,
                        plan.status,
                        json.dumps(plan.original_data_snapshot),
                        json.dumps(plan.initial_recommendation),
                        json.dumps(plan.current_recommendation),
                        json.dumps(plan.notification_preferences.model_dump()),
                        json.dumps([c.model_dump() for c in plan.detected_changes]),
                        plan.check_count,
                        plan.re_analysis_count,
                        plan.last_checked_at,
                        plan.last_changed_at,
                        plan.created_at,
                        plan.updated_at,
                    ))
                logger.info(f"Saved new plan '{plan.subject}' ({plan.id}) for location '{plan.location}' to SQLite database.")
                return plan
            finally:
                conn.close()

    def get_plan(self, plan_id: str) -> Optional[SavedPlan]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM plans WHERE id = ?;", (plan_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return self._row_to_plan(row)
            finally:
                conn.close()

    def list_plans(self, status: Optional[str] = None) -> List[SavedPlan]:
        with self._lock:
            conn = self._get_connection()
            try:
                if status:
                    cursor = conn.execute("SELECT * FROM plans WHERE status = ? ORDER BY created_at DESC;", (status,))
                else:
                    cursor = conn.execute("SELECT * FROM plans ORDER BY created_at DESC;")
                rows = cursor.fetchall()
                return [self._row_to_plan(row) for row in rows]
            finally:
                conn.close()

    def update_plan(self, plan: SavedPlan) -> SavedPlan:
        plan.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        UPDATE plans SET
                            subject = ?,
                            location = ?,
                            action = ?,
                            target_date = ?,
                            query = ?,
                            status = ?,
                            original_data_snapshot = ?,
                            initial_recommendation = ?,
                            current_recommendation = ?,
                            notification_preferences = ?,
                            detected_changes = ?,
                            check_count = ?,
                            re_analysis_count = ?,
                            last_checked_at = ?,
                            last_changed_at = ?,
                            updated_at = ?
                        WHERE id = ?;
                    """, (
                        plan.subject,
                        plan.location,
                        plan.action,
                        plan.target_date,
                        plan.query,
                        plan.status,
                        json.dumps(plan.original_data_snapshot),
                        json.dumps(plan.initial_recommendation),
                        json.dumps(plan.current_recommendation),
                        json.dumps(plan.notification_preferences.model_dump()),
                        json.dumps([c.model_dump() for c in plan.detected_changes]),
                        plan.check_count,
                        plan.re_analysis_count,
                        plan.last_checked_at,
                        plan.last_changed_at,
                        plan.updated_at,
                        plan.id,
                    ))
                return plan
            finally:
                conn.close()

    def delete_plan(self, plan_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("DELETE FROM plans WHERE id = ?;", (plan_id,))
                    return cursor.rowcount > 0
            finally:
                conn.close()

    def _row_to_plan(self, row: sqlite3.Row) -> SavedPlan:
        pref_dict = json.loads(row["notification_preferences"]) if row["notification_preferences"] else {}
        changes_list = json.loads(row["detected_changes"]) if row["detected_changes"] else []

        return SavedPlan(
            id=row["id"],
            subject=row["subject"],
            location=row["location"],
            action=row["action"],
            target_date=row["target_date"],
            query=row["query"] or "",
            status=row["status"],
            original_data_snapshot=json.loads(row["original_data_snapshot"]),
            initial_recommendation=json.loads(row["initial_recommendation"]),
            current_recommendation=json.loads(row["current_recommendation"]),
            notification_preferences=NotificationPreferences(**pref_dict),
            detected_changes=[DetectedChange(**c) for c in changes_list],
            check_count=row["check_count"],
            re_analysis_count=row["re_analysis_count"],
            last_checked_at=row["last_checked_at"],
            last_changed_at=row["last_changed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # =========================================================================
    # Notification & Deduplication Methods
    # =========================================================================

    def add_notification(self, req: CreateNotificationRequest) -> Tuple[NotificationItem, bool]:
        """Adds a notification with automatic deduplication using dedupe_key.
        
        Returns (notification, was_created). If dedupe_key matches an existing
        notification, was_created is False and no duplicate record is created.
        """
        now = datetime.now(timezone.utc).isoformat()
        notif_id = str(uuid.uuid4())[:8]
        link = req.link or (f"/plans/{req.plan_id}" if req.plan_id else None)

        with self._lock:
            conn = self._get_connection()
            try:
                # Check for duplicate if dedupe_key is provided
                if req.dedupe_key:
                    cursor = conn.execute("SELECT * FROM notifications WHERE dedupe_key = ?;", (req.dedupe_key,))
                    existing = cursor.fetchone()
                    if existing:
                        logger.info(f"Duplicate notification suppressed for dedupe_key: '{req.dedupe_key}'")
                        return self._row_to_notification(existing), False

                with conn:
                    conn.execute("""
                        INSERT INTO notifications (
                            id, category, title, message, location, severity, read, dedupe_key, plan_id,
                            link, previous_value, new_value, reason, is_simulated, critic_review_approved, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        notif_id,
                        req.category,
                        req.title,
                        req.message,
                        req.location,
                        req.severity,
                        req.dedupe_key,
                        req.plan_id,
                        link,
                        req.previous_value,
                        req.new_value,
                        req.reason,
                        1 if req.is_simulated else 0,
                        1 if req.critic_review_approved else 0,
                        now,
                    ))

                item = NotificationItem(
                    id=notif_id,
                    category=req.category,
                    title=req.title,
                    message=req.message,
                    location=req.location,
                    severity=req.severity,
                    read=False,
                    dedupe_key=req.dedupe_key,
                    plan_id=req.plan_id,
                    link=link,
                    previous_value=req.previous_value,
                    new_value=req.new_value,
                    reason=req.reason,
                    is_simulated=req.is_simulated,
                    critic_review_approved=req.critic_review_approved,
                    created_at=now,
                )
                logger.info(f"Dispatched notification [{req.severity.upper()}] '{req.title}' (simulated={req.is_simulated}, dedupe_key={req.dedupe_key})")
                return item, True
            finally:
                conn.close()

    def list_notifications(self, unread_only: bool = False, limit: int = 100) -> List[NotificationItem]:
        with self._lock:
            conn = self._get_connection()
            try:
                if unread_only:
                    cursor = conn.execute("SELECT * FROM notifications WHERE read = 0 ORDER BY created_at DESC LIMIT ?;", (limit,))
                else:
                    cursor = conn.execute("SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?;", (limit,))
                rows = cursor.fetchall()
                return [self._row_to_notification(row) for row in rows]
            finally:
                conn.close()

    def mark_notification_read(self, notif_id: str) -> Optional[NotificationItem]:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("UPDATE notifications SET read = 1 WHERE id = ?;", (notif_id,))
                cursor = conn.execute("SELECT * FROM notifications WHERE id = ?;", (notif_id,))
                row = cursor.fetchone()
                return self._row_to_notification(row) if row else None
            finally:
                conn.close()

    def mark_all_notifications_read(self) -> int:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("UPDATE notifications SET read = 1 WHERE read = 0;")
                    return cursor.rowcount
            finally:
                conn.close()

    def clear_notifications(self) -> int:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("DELETE FROM notifications;")
                    return cursor.rowcount
            finally:
                conn.close()

    def _row_to_notification(self, row: sqlite3.Row) -> NotificationItem:
        keys = row.keys()
        return NotificationItem(
            id=row["id"],
            category=row["category"],
            title=row["title"],
            message=row["message"],
            location=row["location"],
            severity=row["severity"],
            read=bool(row["read"]),
            dedupe_key=row["dedupe_key"],
            plan_id=row["plan_id"],
            link=row["link"] if "link" in keys else None,
            previous_value=row["previous_value"] if "previous_value" in keys else None,
            new_value=row["new_value"] if "new_value" in keys else None,
            reason=row["reason"] if "reason" in keys else None,
            is_simulated=bool(row["is_simulated"]) if "is_simulated" in keys and row["is_simulated"] is not None else False,
            critic_review_approved=bool(row["critic_review_approved"]) if "critic_review_approved" in keys and row["critic_review_approved"] is not None else True,
            created_at=row["created_at"],
        )

    # =========================================================================
    # Web Push Subscriptions Methods
    # =========================================================================

    def save_push_subscription(self, req: PushSubscriptionRequest) -> PushSubscriptionItem:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM push_subscriptions WHERE endpoint = ?;", (req.endpoint,))
                existing = cursor.fetchone()
                if existing:
                    sub_id = existing["id"]
                    with conn:
                        conn.execute("""
                            UPDATE push_subscriptions SET
                                p256dh = ?,
                                auth = ?,
                                user_agent = ?,
                                is_active = 1,
                                failure_count = 0,
                                updated_at = ?
                            WHERE id = ?;
                        """, (req.keys.p256dh, req.keys.auth, req.user_agent, now, sub_id))
                    logger.info(f"Re-activated push subscription {sub_id} for endpoint: {req.endpoint[:35]}...")
                else:
                    sub_id = str(uuid.uuid4())[:8]
                    with conn:
                        conn.execute("""
                            INSERT INTO push_subscriptions (
                                id, endpoint, p256dh, auth, user_agent, is_active, failure_count, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?);
                        """, (sub_id, req.endpoint, req.keys.p256dh, req.keys.auth, req.user_agent, now, now))
                    logger.info(f"Registered new push subscription {sub_id} for endpoint: {req.endpoint[:35]}...")

                return PushSubscriptionItem(
                    id=sub_id,
                    endpoint=req.endpoint,
                    p256dh=req.keys.p256dh,
                    auth=req.keys.auth,
                    user_agent=req.user_agent,
                    is_active=True,
                    failure_count=0,
                    created_at=now,
                )
            finally:
                conn.close()

    def get_active_push_subscriptions(self) -> List[PushSubscriptionItem]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM push_subscriptions WHERE is_active = 1 ORDER BY created_at DESC;")
                rows = cursor.fetchall()
                return [
                    PushSubscriptionItem(
                        id=row["id"],
                        endpoint=row["endpoint"],
                        p256dh=row["p256dh"],
                        auth=row["auth"],
                        user_agent=row["user_agent"],
                        is_active=bool(row["is_active"]),
                        failure_count=row["failure_count"],
                        created_at=row["created_at"],
                    )
                    for row in rows
                ]
            finally:
                conn.close()

    def deactivate_push_subscription(self, endpoint: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute(
                        "UPDATE push_subscriptions SET is_active = 0, updated_at = ? WHERE endpoint = ?;",
                        (now, endpoint)
                    )
                    return cursor.rowcount > 0
            finally:
                conn.close()

    def record_push_failure(self, endpoint: str, status_code: Optional[int] = None):
        """Records a push failure. If 404/410 (unregistered or expired), immediately deactivates."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    if status_code in (404, 410):
                        conn.execute(
                            "UPDATE push_subscriptions SET is_active = 0, failure_count = failure_count + 1, updated_at = ? WHERE endpoint = ?;",
                            (now, endpoint)
                        )
                        logger.warning(f"Push subscription deactivated (status {status_code}) for endpoint: {endpoint[:35]}...")
                    else:
                        conn.execute(
                            """
                            UPDATE push_subscriptions SET
                                failure_count = failure_count + 1,
                                is_active = CASE WHEN failure_count + 1 >= 5 THEN 0 ELSE is_active END,
                                updated_at = ?
                            WHERE endpoint = ?;
                            """,
                            (now, endpoint)
                        )
            finally:
                conn.close()

    def delete_push_subscription(self, endpoint: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("DELETE FROM push_subscriptions WHERE endpoint = ?;", (endpoint,))
                    return cursor.rowcount > 0
            finally:
                conn.close()

    # =========================================================================
    # User Notification Preferences Methods
    # =========================================================================

    def get_user_preferences(self) -> UserNotificationPreferences:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM user_notification_preferences WHERE id = 'default';")
                row = cursor.fetchone()
                if not row:
                    return UserNotificationPreferences()
                return UserNotificationPreferences(
                    in_app_enabled=bool(row["in_app_enabled"]),
                    browser_push_enabled=bool(row["browser_push_enabled"]),
                    min_severity=row["min_severity"],
                    notify_on_weather_change=bool(row["notify_on_weather_change"]),
                    notify_on_verdict_change=bool(row["notify_on_verdict_change"]),
                )
            finally:
                conn.close()

    def update_user_preferences(self, prefs: UserNotificationPreferences) -> UserNotificationPreferences:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        INSERT INTO user_notification_preferences (
                            id, in_app_enabled, browser_push_enabled, min_severity,
                            notify_on_weather_change, notify_on_verdict_change, updated_at
                        ) VALUES ('default', ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            in_app_enabled = excluded.in_app_enabled,
                            browser_push_enabled = excluded.browser_push_enabled,
                            min_severity = excluded.min_severity,
                            notify_on_weather_change = excluded.notify_on_weather_change,
                            notify_on_verdict_change = excluded.notify_on_verdict_change,
                            updated_at = excluded.updated_at;
                    """, (
                        1 if prefs.in_app_enabled else 0,
                        1 if prefs.browser_push_enabled else 0,
                        prefs.min_severity,
                        1 if prefs.notify_on_weather_change else 0,
                        1 if prefs.notify_on_verdict_change else 0,
                        now,
                    ))
                return prefs
            finally:
                conn.close()


# Singleton instance
db = Database()

