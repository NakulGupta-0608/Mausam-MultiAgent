import pytest
from datetime import datetime, timezone, timedelta
from backend.app.storage.db import Database
from backend.app.schemas.plan import CreatePlanRequest, NotificationPreferences
from backend.app.schemas.weather import WeatherCondition, GeoLocation, DailyForecast
from backend.app.monitoring.change_detector import change_detector
from backend.app.monitoring.scheduler import SmartMonitoringScheduler


@pytest.fixture
def temp_db(tmp_path):
    """Provides a fresh isolated SQLite database instance for testing."""
    db_file = str(tmp_path / "test_mausam.db")
    return Database(db_path=db_file)


# ============================================================================
# 1. DATABASE PERSISTENCE TESTS
# ============================================================================

def test_database_plan_persistence_and_retrieval(temp_db):
    """Verifies that user plans, snapshots, and preferences persist in SQLite."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    req = CreatePlanRequest(
        subject="Alpine Ridge Traverse",
        location="Manali",
        action="Trekking",
        target_date=now_str,
        query="High elevation trek",
        original_data_snapshot={
            "temp_c": 18.0,
            "humidity": 55,
            "wind_kph": 14.0,
            "precipitation_prob": 10,
            "uv_index": 5.0,
            "condition_text": "Mainly Clear",
            "source": "open-meteo",
        },
        initial_recommendation={
            "verdict_badge": "Optimal",
            "outdoor_score": 88,
            "headline": "Prime alpine conditions",
            "comfort_summary": "Dry trails and mild winds",
            "packing_checklist": ["Windbreaker", "Trekking poles"],
        },
        notification_preferences=NotificationPreferences(
            temp_threshold_c=3.0,
            rain_threshold_pct=15,
            wind_threshold_kph=10.0,
        ),
    )

    saved = temp_db.save_plan(req)
    assert saved.id is not None
    assert saved.subject == "Alpine Ridge Traverse"
    assert saved.status == "active"
    assert saved.original_data_snapshot["precipitation_prob"] == 10
    assert saved.notification_preferences.rain_threshold_pct == 15

    # Re-fetch from DB
    retrieved = temp_db.get_plan(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.location == "Manali"
    assert retrieved.action == "Trekking"
    assert retrieved.outdoor_score == 88


# ============================================================================
# 2. CONFIGURABLE THRESHOLD CHANGE DETECTION TESTS
# ============================================================================

def test_minor_fluctuations_not_flagged_as_significant():
    """Verifies that minor jitter (0.3°C temp, 2% rain, 1 km/h wind) is ignored."""
    snapshot = {
        "temp_c": 20.0,
        "wind_kph": 12.0,
        "precipitation_prob": 15,
        "uv_index": 5.0,
        "condition_text": "Partly Cloudy",
    }

    current = WeatherCondition(
        location=GeoLocation(name="Manali", latitude=32.2, longitude=77.1),
        observed_date="2026-09-27",
        temp_c=20.3,           # +0.3°C jitter (< 3.0°C threshold)
        feels_like_c=20.0,
        humidity=58,
        wind_kph=13.0,          # +1.0 km/h jitter (< 12 km/h threshold)
        wind_direction="NW",
        condition_text="Partly Cloudy",
        precipitation_mm=0.0,
        precipitation_prob=17,  # +2% jitter (< 15% threshold)
        uv_index=5.2,           # +0.2 jitter (< 2.0 threshold)
        forecast_days=[],
        source="open-meteo-live"
    )

    eval_result = change_detector.evaluate(current, snapshot)
    assert eval_result.is_significant is False
    assert len(eval_result.changes) == 0


def test_meaningful_rain_and_wind_shift_flagged_as_significant():
    """Verifies that significant shifts (+45% rain probability and +20 km/h wind) are flagged."""
    snapshot = {
        "temp_c": 22.0,
        "wind_kph": 10.0,
        "precipitation_prob": 10,
        "uv_index": 4.0,
        "condition_text": "Clear",
    }

    # Weather shifts significantly
    current = WeatherCondition(
        location=GeoLocation(name="Shimla", latitude=31.1, longitude=77.1),
        observed_date="2026-09-27",
        temp_c=16.0,           # -6°C drop
        feels_like_c=14.0,
        humidity=92,
        wind_kph=32.0,          # +22 km/h gusty wind
        wind_direction="NW",
        condition_text="Heavy Rain Showers",
        precipitation_mm=14.0,
        precipitation_prob=75,  # +65% jump
        uv_index=2.0,
        forecast_days=[],
        source="open-meteo-live"
    )

    eval_result = change_detector.evaluate(current, snapshot)
    assert eval_result.is_significant is True
    assert len(eval_result.changes) >= 2
    metrics = [c.metric for c in eval_result.changes]
    assert "Precipitation Probability" in metrics
    assert "Wind Velocity" in metrics


# ============================================================================
# 3. PIPELINE RE-TRIGGER & NOTIFICATION DEDUPLICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_scheduler_re_triggers_agents_on_significant_change(monkeypatch, temp_db):
    """Verifies that on significant change, RiskAnalysis, Recommendation, and Critic agents re-run."""
    monkeypatch.setattr("backend.app.monitoring.scheduler.db", temp_db)

    scheduler = SmartMonitoringScheduler()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    req = CreatePlanRequest(
        subject="Valley Hike",
        location="Shimla",
        action="Hiking",
        target_date=today_str,
        original_data_snapshot={
            "temp_c": 21.0,
            "humidity": 45,
            "wind_kph": 10.0,
            "precipitation_prob": 5,
            "uv_index": 4.0,
            "condition_text": "Sunny",
        },
        initial_recommendation={
            "verdict_badge": "Optimal",
            "outdoor_score": 90,
            "headline": "Superb conditions",
            "comfort_summary": "Sunny and clear",
            "packing_checklist": ["Sun hat"],
        }
    )
    plan = temp_db.save_plan(req)

    # Simulated sudden severe storm approach
    storm_weather = WeatherCondition(
        location=GeoLocation(name="Shimla", latitude=31.1, longitude=77.1),
        observed_date=today_str,
        temp_c=10.0,
        feels_like_c=6.0,
        humidity=96,
        wind_kph=40.0,
        wind_direction="NW",
        condition_text="Thunderstorm with Heavy Rain",
        precipitation_mm=22.0,
        precipitation_prob=90,
        uv_index=1.0,
        forecast_days=[
            DailyForecast(
                date=today_str,
                max_temp_c=12.0,
                min_temp_c=6.0,
                avg_temp_c=9.0,
                condition="Thunderstorm",
                rain_probability=90,
                uv_index=1.0,
                wind_max_kph=40.0,
            )
        ],
        source="open-meteo-live"
    )

    # Check plan with simulated storm
    res = await scheduler.check_plan_with_weather(plan, storm_weather)

    assert res.significant_change_detected is True
    assert res.re_analyzed is True
    assert res.notification_emitted is True

    # Plan should have updated recommendation
    updated_plan = temp_db.get_plan(plan.id)
    assert updated_plan.re_analysis_count == 1
    assert updated_plan.current_recommendation["verdict_badge"] in ["Caution", "Unfavorable", "Severe"]
    assert updated_plan.current_recommendation["outdoor_score"] < 90
    assert len(updated_plan.detected_changes) >= 1

    # Notification should have been stored
    notifs = temp_db.list_notifications()
    assert len(notifs) >= 1
    assert notifs[0].plan_id == plan.id
    assert notifs[0].severity in ["warning", "danger"]

    # 4. Verify Notification Deduplication: Second check with same storm should NOT emit duplicate alert
    res2 = await scheduler.check_plan_with_weather(updated_plan, storm_weather)
    assert res2.notification_emitted is False
    notifs2 = temp_db.list_notifications()
    assert len(notifs2) == len(notifs)  # Zero duplicates added


# ============================================================================
# 4. TARGET DATE STOPPING CONDITION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_scheduler_stops_monitoring_past_target_date(monkeypatch, temp_db):
    """Verifies that plans whose target date has passed are marked expired and excluded."""
    monkeypatch.setattr("backend.app.monitoring.scheduler.db", temp_db)

    scheduler = SmartMonitoringScheduler()
    # Plan date 2 days in the past
    past_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")

    req = CreatePlanRequest(
        subject="Past Weekend Expedition",
        location="Shimla",
        action="Trail Run",
        target_date=past_date,
        original_data_snapshot={"temp_c": 15.0, "precipitation_prob": 10},
        initial_recommendation={"verdict_badge": "Optimal", "outdoor_score": 85},
    )
    plan = temp_db.save_plan(req)
    assert plan.status == "active"

    # Run monitoring cycle
    summary = await scheduler.run_monitoring_cycle()
    assert summary["expired_count"] >= 1

    # Plan status must now be expired
    expired_plan = temp_db.get_plan(plan.id)
    assert expired_plan.status == "expired"


# ============================================================================
# 5. REAL OPEN-METEO WEATHER LIVE CHECK TEST
# ============================================================================

@pytest.mark.asyncio
async def test_real_weather_live_plan_check(monkeypatch, temp_db):
    """Verifies that an active plan can be checked against live Open-Meteo telemetry."""
    monkeypatch.setattr("backend.app.monitoring.scheduler.db", temp_db)

    scheduler = SmartMonitoringScheduler()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    req = CreatePlanRequest(
        subject="Live City Walk",
        location="Shimla",
        action="Sightseeing",
        target_date=today_str,
        original_data_snapshot={
            "temp_c": 18.0,
            "humidity": 50,
            "wind_kph": 12.0,
            "precipitation_prob": 15,
            "uv_index": 4.0,
            "condition_text": "Clear",
        },
        initial_recommendation={"verdict_badge": "Optimal", "outdoor_score": 80},
    )
    plan = temp_db.save_plan(req)

    # Perform real live check
    res = await scheduler.check_plan_by_id(plan.id)
    assert res is not None
    assert res.plan_id == plan.id
    assert res.status == "active"
    assert res.plan.check_count >= 1
    assert res.plan.last_checked_at is not None
