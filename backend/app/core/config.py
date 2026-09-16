"""Application settings, loaded from environment / .env.

Deploy-friendly: accepts a single plain ``DATABASE_URL`` as handed out by managed
hosts (``postgres://`` / ``postgresql://``, often with ``?sslmode=require``) and
derives the async (asyncpg) and sync (psycopg) SQLAlchemy URLs from it. Also
lets a ``FRONTEND_URL`` env be folded into the CORS allow-list.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    PROJECT_NAME: str = "FleetOS"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Database. DATABASE_URL is the single source of truth; it may be a plain
    # managed-host URL (postgres://...) or an explicit SQLAlchemy URL
    # (postgresql+asyncpg://...). DATABASE_URL_SYNC is optional; when unset it is
    # derived from DATABASE_URL for Alembic.
    DATABASE_URL: str = "postgresql+asyncpg://fleetos:fleetos@localhost:5432/fleetos"
    DATABASE_URL_SYNC: str | None = None
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    TELEMETRY_CHANNEL: str = "fleetos:telemetry"

    # CORS — comma-separated string in env, exposed as a list. FRONTEND_URL (a
    # single origin, e.g. from a deploy blueprint) is merged in below.
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    FRONTEND_URL: str | None = None

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ─── Derived DB URLs ──────────────────────────────────────────────────────
    @staticmethod
    def _split_scheme(url: str) -> tuple[str, str]:
        """Return (base_scheme, rest) where base_scheme drops any +driver."""
        scheme, _, rest = url.partition("://")
        base = scheme.split("+", 1)[0]
        return base, rest

    def _rebuild(self, driver_scheme: str, *, keep_sslmode: bool) -> str:
        base, rest = self._split_scheme(self.DATABASE_URL)
        # Normalise "postgres" -> "postgresql".
        if base == "postgres":
            base = "postgresql"
        parts = urlsplit(f"{base}://{rest}")
        query = parts.query
        if not keep_sslmode and query:
            # asyncpg rejects libpq's sslmode/channel_binding params; strip them
            # (TLS is enabled via connect_args instead — see db_connect_args).
            kept = [
                kv
                for kv in query.split("&")
                if kv and not kv.lower().startswith(("sslmode=", "channel_binding="))
            ]
            query = "&".join(kept)
        return urlunsplit((driver_scheme, parts.netloc, parts.path, query, parts.fragment))

    @property
    def sqlalchemy_async_url(self) -> str:
        return self._rebuild("postgresql+asyncpg", keep_sslmode=False)

    @property
    def sqlalchemy_sync_url(self) -> str:
        if self.DATABASE_URL_SYNC:
            return self.DATABASE_URL_SYNC
        # psycopg understands sslmode, so keep it.
        return self._rebuild("postgresql+psycopg", keep_sslmode=True)

    @property
    def db_requires_ssl(self) -> bool:
        return "sslmode=require" in self.DATABASE_URL.lower()

    @property
    def db_connect_args(self) -> dict:
        return {"ssl": True} if self.db_requires_ssl else {}

    @property
    def cors_origins(self) -> list[str]:
        origins = list(self.BACKEND_CORS_ORIGINS)
        if self.FRONTEND_URL:
            fe = self.FRONTEND_URL.strip().rstrip("/")
            # Blueprints often expose a bare host; normalise to an https origin.
            if fe and "://" not in fe:
                fe = f"https://{fe}"
            if fe and fe not in origins:
                origins.append(fe)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
