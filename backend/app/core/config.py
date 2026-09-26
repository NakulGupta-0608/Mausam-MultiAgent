from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MausamAI - Weather Intelligence Multi-Agent Engine"
    VERSION: str = "0.2.0"
    API_V1_STR: str = "/api"

    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Weather Provider
    WEATHER_PROVIDER: str = "open-meteo"
    WEATHER_API_KEY: str = ""

    # Multi-Agent Orchestration & Budget Controls
    MAX_CRITIC_REVIEWS: int = 2
    WORKFLOW_MAX_STEPS: int = 10
    WORKFLOW_TIME_BUDGET_SEC: float = 15.0
    WORKFLOW_COST_BUDGET_USD: float = 0.05

    # Database & Storage
    DATABASE_PATH: str = "backend/mausam.db"

    # Smart Monitoring & Periodic Polling
    MONITORING_POLL_INTERVAL_SECONDS: int = 60
    MONITORING_ENABLED: bool = True
    MONITORING_MIN_CHECK_INTERVAL_SECONDS: int = 30

    # Meaningful Change Detection Thresholds (Configurable)
    THRESHOLD_TEMP_DELTA_C: float = 3.0
    THRESHOLD_RAIN_PROB_DELTA_PCT: int = 15
    THRESHOLD_WIND_DELTA_KPH: float = 12.0
    THRESHOLD_UV_DELTA: float = 2.0
    THRESHOLD_SCORE_DROP_PTS: int = 12

    # Web Push Notifications (VAPID)
    VAPID_PUBLIC_KEY: str = "BFWkMKu0v2u6tVbNzW53rQRyvbzILeVXw4qWvQBABjArnoDH0C0N5ACE6TrwqP7FtppmJAOH6RifsB2oiGbErac"
    VAPID_PRIVATE_KEY: str = "GZ8lIMOWuwaJ1IuZT7GiEaMv3h5Bz6tuwSImCdC61A4"
    VAPID_CLAIM_EMAIL: str = "mailto:support@mausam.ai"

    # LLM Provider
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
