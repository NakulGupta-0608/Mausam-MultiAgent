from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.schemas.plan import SavedPlan, CreatePlanRequest, CheckPlanResponse, NotificationPreferences
from backend.app.schemas.weather import WeatherCondition
from backend.app.storage.db import db
from backend.app.monitoring.scheduler import monitoring_scheduler

router = APIRouter(prefix="/plans", tags=["Saved Plans"])


class CheckPlanRequestBody(BaseModel):
    simulated_weather: Optional[Dict[str, Any]] = None
    force: bool = False


class UpdatePlanStatusBody(BaseModel):
    status: str  # active, paused, completed


@router.get("", response_model=List[SavedPlan])
async def get_saved_plans(status: Optional[str] = None):
    return db.list_plans(status=status)


@router.post("", response_model=SavedPlan)
async def save_new_plan(request: CreatePlanRequest):
    return db.save_plan(request)


@router.get("/{plan_id}", response_model=SavedPlan)
async def get_plan_by_id(plan_id: str):
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str):
    success = db.delete_plan(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "deleted", "id": plan_id}


@router.post("/{plan_id}/check", response_model=CheckPlanResponse)
async def trigger_plan_check(plan_id: str, body: Optional[CheckPlanRequestBody] = None):
    """Checks an individual plan for meaningful weather shifts.
    
    Accepts optional simulated_weather payload to test and demonstrate significant
    change detection, agent re-triggering, and deduplicated alert generation.
    """
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    sim_weather = None
    if body and body.simulated_weather:
        try:
            sim_weather = WeatherCondition(**body.simulated_weather)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid simulated weather payload: {e}")

    force = body.force if body else False
    result = await monitoring_scheduler.check_plan_by_id(
        plan_id=plan_id,
        simulated_weather=sim_weather,
        force=force
    )
    if not result:
        raise HTTPException(status_code=404, detail="Plan check could not be completed.")
    return result


@router.patch("/{plan_id}/status", response_model=SavedPlan)
async def update_plan_status(plan_id: str, body: UpdatePlanStatusBody):
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if body.status not in ["active", "paused", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status. Allowed: 'active', 'paused', 'completed'")
    plan.status = body.status
    return db.update_plan(plan)


@router.patch("/{plan_id}/preferences", response_model=SavedPlan)
async def update_plan_preferences(plan_id: str, prefs: NotificationPreferences):
    plan = db.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan.notification_preferences = prefs
    return db.update_plan(plan)
