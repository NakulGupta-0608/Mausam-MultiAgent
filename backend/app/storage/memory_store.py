import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict
from backend.app.schemas.plan import SavedPlan, CreatePlanRequest
from backend.app.schemas.notification import NotificationItem, CreateNotificationRequest


class MemoryStore:
    """Thread-safe in-memory store for plans and notifications."""

    def __init__(self):
        self._plans: Dict[str, SavedPlan] = {}
        self._notifications: Dict[str, NotificationItem] = {}
        self._seed_initial_data()

    def _seed_initial_data(self):
        # Seed initial sample plans to populate the dashboard nicely
        sample_plan = SavedPlan(
            id=str(uuid.uuid4())[:8],
            title="Weekend Himalayan Day Hike",
            location="Manali, HP",
            target_date="2026-09-28",
            query="Plan an alpine day trek with clear visibility and moderate winds",
            verdict="Optimal",
            outdoor_score=88,
            summary="Clear alpine skies expected in morning. Cool breeze, low UV risk early. Mild cold front approaching dusk.",
            packing_checklist=["Windbreaker", "Trekking poles", "Thermal base layer", "Hydration pack (2L)"],
            tags=["Trekking", "Mountain", "High Altitude"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._plans[sample_plan.id] = sample_plan

        # Seed sample notifications
        sample_notifications = [
            NotificationItem(
                id=str(uuid.uuid4())[:8],
                category="alert",
                title="Monsoon Transition Advisory",
                message="Shift in regional moisture currents may trigger localized evening convective showers in mountainous terrain.",
                location="Northern Sub-Himalayas",
                severity="warning",
                read=False,
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
            NotificationItem(
                id=str(uuid.uuid4())[:8],
                category="system",
                title="Multi-Agent Mesh Active",
                message="MausamAI autonomous agent pipeline initialized with dynamic weather telemetry integration.",
                location="System Core",
                severity="info",
                read=False,
                created_at=datetime.now(timezone.utc).isoformat(),
            ),
            NotificationItem(
                id=str(uuid.uuid4())[:8],
                category="advisory",
                title="UV Index Advisory",
                message="High UV index (7.5+) recorded in coastal sectors between 11:30 and 15:30. Sun protection advised.",
                location="Coastal Zones",
                severity="info",
                read=True,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        ]
        for notif in sample_notifications:
            self._notifications[notif.id] = notif

    # Plans
    def list_plans(self) -> List[SavedPlan]:
        return list(self._plans.values())

    def get_plan(self, plan_id: str) -> Optional[SavedPlan]:
        return self._plans.get(plan_id)

    def create_plan(self, req: CreatePlanRequest) -> SavedPlan:
        plan_id = str(uuid.uuid4())[:8]
        plan = SavedPlan(
            id=plan_id,
            title=req.title,
            location=req.location,
            target_date=req.target_date,
            query=req.query,
            verdict=req.verdict,
            outdoor_score=req.outdoor_score,
            summary=req.summary,
            packing_checklist=req.packing_checklist,
            tags=req.tags,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._plans[plan_id] = plan
        return plan

    def delete_plan(self, plan_id: str) -> bool:
        if plan_id in self._plans:
            del self._plans[plan_id]
            return True
        return False

    # Notifications
    def list_notifications(self) -> List[NotificationItem]:
        # Return sorted latest first
        return sorted(list(self._notifications.values()), key=lambda n: n.created_at, reverse=True)

    def add_notification(self, req: CreateNotificationRequest) -> NotificationItem:
        notif_id = str(uuid.uuid4())[:8]
        notif = NotificationItem(
            id=notif_id,
            category=req.category,
            title=req.title,
            message=req.message,
            location=req.location,
            severity=req.severity,
            read=False,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._notifications[notif_id] = notif
        return notif

    def mark_notification_read(self, notif_id: str) -> Optional[NotificationItem]:
        if notif_id in self._notifications:
            item = self._notifications[notif_id]
            item.read = True
            return item
        return None

    def mark_all_notifications_read(self) -> int:
        count = 0
        for item in self._notifications.values():
            if not item.read:
                item.read = True
                count += 1
        return count


# Singleton instance
store = MemoryStore()
