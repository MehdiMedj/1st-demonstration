"""FastAPI application factory + lifespan (Redis<->WebSocket bridge)."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis import close_redis
from app.services.broadcast import redis_subscriber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fleetos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the background Redis subscriber that fans telemetry out to WS clients.
    subscriber_task = asyncio.create_task(redis_subscriber())
    logger.info("FleetOS API started (env=%s)", settings.ENVIRONMENT)
    try:
        yield
    finally:
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
        await close_redis()
        logger.info("FleetOS API shut down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Fleet Management & Logistics Operating System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": settings.PROJECT_NAME, "docs": "/docs"}
