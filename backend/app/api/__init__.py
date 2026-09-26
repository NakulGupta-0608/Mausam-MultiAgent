from fastapi import APIRouter
from backend.app.api.routes import (
    health_router,
    weather_router,
    analysis_router,
    plans_router,
    notifications_router,
)

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(weather_router)
api_router.include_router(analysis_router)
api_router.include_router(plans_router)
api_router.include_router(notifications_router)
