"""Shared async Redis client (used for telemetry pub/sub)."""
from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings

# decode_responses=True → we publish/consume JSON strings.
redis_client: redis.Redis = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def close_redis() -> None:
    await redis_client.aclose()
