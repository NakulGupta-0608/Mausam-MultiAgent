from .health import router as health_router
from .weather import router as weather_router
from .analysis import router as analysis_router
from .plans import router as plans_router
from .notifications import router as notifications_router

__all__ = [
    "health_router",
    "weather_router",
    "analysis_router",
    "plans_router",
    "notifications_router",
]
