from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.schemas.plan import SavedPlan, CreatePlanRequest
from backend.app.storage.memory_store import store

router = APIRouter(prefix="/plans", tags=["Saved Plans"])


@router.get("", response_model=List[SavedPlan])
async def get_saved_plans():
    return store.list_plans()


@router.post("", response_model=SavedPlan)
async def save_new_plan(request: CreatePlanRequest):
    return store.create_plan(request)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str):
    success = store.delete_plan(plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"status": "deleted", "id": plan_id}
