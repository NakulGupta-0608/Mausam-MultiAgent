import uvicorn
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api import api_router
from backend.app.monitoring.logger import logger
from backend.app.core.exceptions import WeatherServiceException
from backend.app.monitoring.scheduler import monitoring_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    if settings.MONITORING_ENABLED:
        monitoring_scheduler.start()
    yield
    if settings.MONITORING_ENABLED:
        monitoring_scheduler.stop()
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-Agent Autonomous Weather Intelligence and Decision Support Engine",
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WeatherServiceException)
async def weather_service_exception_handler(request: Request, exc: WeatherServiceException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
            "location_searched": exc.location,
            "retries_attempted": exc.retries_attempted,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


# Register main API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
