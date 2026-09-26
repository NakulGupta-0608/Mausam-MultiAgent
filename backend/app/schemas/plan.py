from typing import List, Optional
from pydantic import BaseModel, Field


class CreatePlanRequest(BaseModel):
    title: str
    location: str
    target_date: str
    query: str
    verdict: str
    outdoor_score: int
    summary: str
    packing_checklist: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class SavedPlan(BaseModel):
    id: str
    title: str
    location: str
    target_date: str
    query: str
    verdict: str
    outdoor_score: int
    summary: str
    packing_checklist: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: str
