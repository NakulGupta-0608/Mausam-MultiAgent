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
