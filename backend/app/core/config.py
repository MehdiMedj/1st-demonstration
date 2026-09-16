"""Application settings, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    PROJECT_NAME: str = "FleetOS"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fleetos:fleetos@localhost:5432/fleetos"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://fleetos:fleetos@localhost:5432/fleetos"
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    TELEMETRY_CHANNEL: str = "fleetos:telemetry"

    # CORS — comma-separated string in env, exposed as a list.
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
