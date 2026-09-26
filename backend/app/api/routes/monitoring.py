from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
from backend.app.storage.db import db
from backend.app.monitoring.scheduler import monitoring_scheduler

router = APIRouter(prefix="/monitoring", tags=["Smart Monitoring"])


class UpdateIntervalRequest(BaseModel):
    interval_seconds: int = Field(..., ge=10, le=3600, description="Polling interval in seconds (10s to 3600s)")


@router.get("/status")
async def get_monitoring_status():
    """Returns the live status, active plans count, and configuration of the background monitoring scheduler."""
    active_plans = db.list_plans(status="active")
    all_plans = db.list_plans()

    return {
        "status": "running" if monitoring_scheduler._is_running else "stopped",
        "poll_interval_seconds": monitoring_scheduler.poll_interval,
        "active_plans_count": len(active_plans),
        "total_plans_count": len(all_plans),
        "min_check_interval_seconds": 30,
    }


@router.post("/trigger")
async def trigger_monitoring_cycle():
    """Manually triggers an immediate monitoring cycle across all active plans."""
    summary = await monitoring_scheduler.run_monitoring_cycle()
    return {
        "status": "success",
        "message": "Monitoring cycle completed",
        "details": summary,
    }


@router.post("/interval")
async def set_polling_interval(request: UpdateIntervalRequest):
    """Dynamically updates the periodic polling interval for smart plan monitoring."""
    monitoring_scheduler.poll_interval = request.interval_seconds
    return {
        "status": "success",
        "new_interval_seconds": monitoring_scheduler.poll_interval,
        "message": f"Monitoring interval updated to {request.interval_seconds} seconds."
    }
