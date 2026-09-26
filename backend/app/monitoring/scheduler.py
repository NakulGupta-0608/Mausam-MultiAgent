import asyncio
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from backend.app.core.config import settings
from backend.app.storage.db import db
from backend.app.schemas.plan import SavedPlan, CheckPlanResponse, DetectedChange
from backend.app.schemas.weather import WeatherCondition, GeoLocation
from backend.app.schemas.notification import CreateNotificationRequest
from backend.app.schemas.analysis import StructuredPlan
from backend.app.tools.weather_api import weather_tool
from backend.app.tools.geo_service import geo_service
from backend.app.monitoring.change_detector import change_detector, ChangeEvaluation
from backend.app.monitoring.tracer import AgentExecutionTracer
from backend.app.monitoring.logger import logger
from backend.app.monitoring.push_service import push_service
from backend.app.agents.planner import PlannerAgent
from backend.app.agents.risk_analyst import RiskAnalysisAgent
from backend.app.agents.recommendation import RecommendationAgent
from backend.app.agents.critic import CriticAgent
from backend.app.orchestration.state import WorkflowState


class SmartMonitoringScheduler:
    """Background scheduler that periodically monitors active plans for meaningful weather shifts.
    
    Features:
    - Bounded polling with configurable interval to eliminate redundant API calls.
    - Automatic stopping condition when target date passes (transitions to 'expired').
    - Threshold-based meaningful change detection (filters minor fluctuations).
    - Multi-agent pipeline re-trigger (RiskAnalysis, Recommendation, and Critic agents).
    - Repeat notification deduplication using composite state hashes.
    """

    def __init__(self):
        self.poll_interval = settings.MONITORING_POLL_INTERVAL_SECONDS
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._last_plan_checks: Dict[str, float] = {}

        # Reusable agent instances
        self.planner = PlannerAgent()
        self.risk_analyst = RiskAnalysisAgent()
        self.recommender = RecommendationAgent()
        self.critic = CriticAgent()

    def start(self):
        """Starts the background monitoring task."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Smart Monitoring Scheduler started (polling every {self.poll_interval}s).")

    def stop(self):
        """Stops the background monitoring task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("Smart Monitoring Scheduler stopped.")

    async def _monitoring_loop(self):
        """Main periodic polling loop."""
        while self._is_running:
            try:
                await self.run_monitoring_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring cycle: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Executes a single monitoring pass over all active plans."""
        active_plans = db.list_plans(status="active")
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now_ts = time.time()

        checked_count = 0
        re_analyzed_count = 0
        expired_count = 0
        notifications_sent = 0

        # Group plans by (location, target_date) to minimize external API calls
        weather_cache: Dict[Tuple[str, str], Optional[WeatherCondition]] = {}

        for plan in active_plans:
            # 1. Stopping Condition: Check if target date has passed
            if plan.target_date < today_str:
                plan.status = "expired"
                plan.updated_at = datetime.now(timezone.utc).isoformat()
                db.update_plan(plan)
                expired_count += 1
                logger.info(f"Plan '{plan.subject}' ({plan.id}) marked EXPIRED: target date {plan.target_date} < {today_str}.")
                continue

            # 2. Rate limiting per plan
            last_checked = self._last_plan_checks.get(plan.id, 0.0)
            if (now_ts - last_checked) < settings.MONITORING_MIN_CHECK_INTERVAL_SECONDS:
                continue

            # 3. Retrieve or fetch weather telemetry
            cache_key = (plan.location.strip().lower(), plan.target_date)
            current_weather = weather_cache.get(cache_key)

            if current_weather is None and cache_key not in weather_cache:
                try:
                    geo = await geo_service.geocode(plan.location)
                    current_weather = await weather_tool.get_forecast(geo, plan.target_date)
                    weather_cache[cache_key] = current_weather
                except Exception as e:
                    logger.warning(f"Could not re-fetch weather for plan '{plan.subject}' in '{plan.location}': {e}")
                    weather_cache[cache_key] = None
                    continue

            if not current_weather:
                continue

            # 4. Process single plan with verified weather
            res = await self.check_plan_with_weather(plan, current_weather)
            self._last_plan_checks[plan.id] = now_ts
            checked_count += 1
            if res.re_analyzed:
                re_analyzed_count += 1
            if res.notification_emitted:
                notifications_sent += 1

        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_plans_total": len(active_plans),
            "checked_count": checked_count,
            "re_analyzed_count": re_analyzed_count,
            "expired_count": expired_count,
            "notifications_sent": notifications_sent,
        }
        logger.info(f"Monitoring cycle completed: {checked_count} checked, {re_analyzed_count} re-analyzed, {expired_count} expired.")
        return summary

    async def check_plan_by_id(
        self,
        plan_id: str,
        simulated_weather: Optional[WeatherCondition] = None,
        force: bool = False
    ) -> Optional[CheckPlanResponse]:
        """Manually checks a specific plan by ID, optionally taking simulated weather for testing."""
        plan = db.get_plan(plan_id)
        if not plan:
            return None

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if plan.target_date < today_str and not force:
            plan.status = "expired"
            db.update_plan(plan)
            return CheckPlanResponse(
                plan_id=plan.id,
                checked_at=datetime.now(timezone.utc).isoformat(),
                status="expired",
                significant_change_detected=False,
                re_analyzed=False,
                notification_emitted=False,
                plan=plan,
            )

        if simulated_weather:
            weather = simulated_weather
        else:
            geo = await geo_service.geocode(plan.location)
            weather = await weather_tool.get_forecast(geo, plan.target_date)

        return await self.check_plan_with_weather(plan, weather)

    async def check_plan_with_weather(
        self,
        plan: SavedPlan,
        current_weather: WeatherCondition
    ) -> CheckPlanResponse:
        """Compares current weather with snapshot and re-runs multi-agent pipeline if meaningful change occurred."""
        now = datetime.now(timezone.utc).isoformat()
        evaluation: ChangeEvaluation = change_detector.evaluate(
            current_weather=current_weather,
            snapshot=plan.original_data_snapshot,
            preferences=plan.notification_preferences,
        )

        plan.last_checked_at = now
        plan.check_count += 1
        re_analyzed = False
        notification_emitted = False

        if evaluation.is_significant:
            logger.info(f"Significant atmospheric shift detected for plan '{plan.subject}' ({plan.id}): {evaluation.summary}")

            # Re-run multi-agent pipeline: RiskAnalysis -> Recommendation -> Critic
            updated_recommendation = await self._re_run_agent_pipeline(plan, current_weather)

            # Record detected changes in plan history
            for change in evaluation.changes:
                plan.detected_changes.insert(0, change)
            # Cap change history to latest 20 items
            plan.detected_changes = plan.detected_changes[:20]

            old_score = plan.current_recommendation.get("outdoor_score", 50)
            old_verdict = plan.current_recommendation.get("verdict_badge", "Caution")
            new_score = updated_recommendation.get("outdoor_score", 50)
            new_verdict = updated_recommendation.get("verdict_badge", "Caution")

            # Update current recommendation & state
            plan.current_recommendation = updated_recommendation
            plan.last_changed_at = now
            plan.re_analysis_count += 1
            re_analyzed = True

            # Review-gated delivery: Only notify if Critic Agent approved the update
            critic_verdict = updated_recommendation.get("critic_verdict", "APPROVE")
            if critic_verdict != "APPROVE":
                logger.warning(
                    f"Notification suppressed for plan '{plan.subject}' ({plan.id}): "
                    f"Critic review verdict was '{critic_verdict}' (review-gated delivery enforced)."
                )
                notification_emitted = False
            else:
                notification_emitted = self._dispatch_deduped_notification(
                    plan=plan,
                    evaluation=evaluation,
                    old_verdict=old_verdict,
                    new_verdict=new_verdict,
                    old_score=old_score,
                    new_score=new_score,
                )

        # Save updated plan in SQLite database
        db.update_plan(plan)

        return CheckPlanResponse(
            plan_id=plan.id,
            checked_at=now,
            status=plan.status,
            significant_change_detected=evaluation.is_significant,
            changes=evaluation.changes,
            re_analyzed=re_analyzed,
            notification_emitted=notification_emitted,
            plan=plan,
        )

    async def _re_run_agent_pipeline(
        self,
        plan: SavedPlan,
        current_weather: WeatherCondition
    ) -> Dict[str, Any]:
        """Re-runs the RiskAnalysisAgent, RecommendationAgent, and CriticAgent on updated telemetry."""
        tracer = AgentExecutionTracer()

        # Build workflow state
        state = WorkflowState(
            query=plan.query or f"Evaluate outdoor feasibility for {plan.action} in {plan.location}",
            location_name=plan.location,
            target_date=plan.target_date,
            weather=current_weather,
            geo=current_weather.location,
        )

        # Formulate structured plan
        state = await self.planner.process(state, tracer)

        # 1. Re-run RiskAnalysisAgent
        state = await self.risk_analyst.process(state, tracer)

        # 2. Re-run RecommendationAgent
        state = await self.recommender.process(state, tracer)

        # 3. Re-run CriticAgent (adversarial review)
        state = await self.critic.process(state, tracer)

        review = state.current_critic_review

        # Build fresh recommendation dict
        updated_rec = {
            "verdict_badge": state.verdict_badge,
            "outdoor_score": state.outdoor_score,
            "headline": state.headline,
            "comfort_summary": state.comfort_summary,
            "packing_checklist": state.packing_checklist,
            "options_comparison": [opt.model_dump() for opt in state.options_comparison],
            "stated_limitations": state.stated_limitations,
            "critic_verdict": review.verdict if review else "APPROVE",
            "critique_score": review.critique_score if review else 90,
            "re_evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Pipeline re-run complete for '{plan.subject}': Score={state.outdoor_score}, "
            f"Verdict={state.verdict_badge}, Critic={updated_rec['critic_verdict']}"
        )
        return updated_rec

    def _dispatch_deduped_notification(
        self,
        plan: SavedPlan,
        evaluation: ChangeEvaluation,
        old_verdict: str,
        new_verdict: str,
        old_score: int,
        new_score: int,
    ) -> bool:
        """Dispatches an alert notification with strict state deduplication."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Metric shift signature
        shift_signature = "-".join(sorted([f"{c.metric}:{c.new_value}" for c in evaluation.changes]))
        hash_input = f"{plan.id}:{new_verdict}:{new_score // 5}:{shift_signature}:{today_str}"
        dedupe_key = f"alert:{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

        # Determine severity
        if new_verdict == "Severe" or any("Severe" in c.metric for c in evaluation.changes):
            severity = "danger"
            category = "alert"
        elif new_verdict in ["Caution", "Unfavorable"] or old_score - new_score >= 10:
            severity = "warning"
            category = "warning"
        else:
            severity = "info"
            category = "advisory"

        message = (
            f"Atmospheric shift in {plan.location} for '{plan.subject}': {evaluation.summary} "
            f"Outdoor suitability adjusted from {old_score} ({old_verdict}) to {new_score} ({new_verdict})."
        )

        prev_vals = [f"{c.metric}: {c.old_value}" for c in evaluation.changes]
        new_vals = [f"{c.metric}: {c.new_value}" for c in evaluation.changes]
        reasons = [c.significance_reason for c in evaluation.changes]

        previous_value_str = ", ".join(prev_vals) if prev_vals else f"Suitability Score {old_score} ({old_verdict})"
        new_value_str = ", ".join(new_vals) if new_vals else f"Suitability Score {new_score} ({new_verdict})"
        reason_str = "; ".join(reasons) if reasons else evaluation.summary

        req = CreateNotificationRequest(
            category=category,
            title=f"Plan Alert: Weather Shift for '{plan.subject}'",
            message=message,
            location=plan.location,
            severity=severity,
            dedupe_key=dedupe_key,
            plan_id=plan.id,
            link=f"/#plan-{plan.id}",
            previous_value=previous_value_str,
            new_value=new_value_str,
            reason=reason_str,
            is_simulated=False,
            critic_review_approved=True,
        )

        item, was_created = db.add_notification(req)
        if was_created:
            try:
                push_service.send_push_notification(item)
            except Exception as e:
                logger.error(f"Failed to broadcast push notification: {e}")
        return was_created


# Singleton monitoring scheduler
monitoring_scheduler = SmartMonitoringScheduler()
