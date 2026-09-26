from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def get_health():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "weather_provider": settings.WEATHER_PROVIDER,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "agents_available": [
            "WeatherAnalystAgent",
            "ActivityPlannerAgent",
            "RiskAssessorAgent"
        ]
    }
