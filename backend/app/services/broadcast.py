"""Realtime broadcast bus.

Bridges Redis Pub/Sub to connected WebSocket dispatcher clients:

    telemetry endpoint --publish--> Redis channel --consume--> ConnectionManager
                                                                    |
                                                               fan-out to
                                                             WS clients (per org)

Every API worker runs one Redis subscriber (started in the app lifespan) and
keeps its own set of local WebSocket connections. This means the system scales
horizontally: a ping received by worker A is delivered to dashboard clients
connected to worker B, because both subscribe to the same Redis channel.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict

from fastapi import WebSocket

from app.core.config import settings
from app.core.redis import redis_client
from app.schemas.telemetry import TelemetryEvent

logger = logging.getLogger("fleetos.broadcast")


class ConnectionManager:
    """Tracks live WebSocket connections, grouped by organization (tenant)."""

    def __init__(self) -> None:
        self._by_org: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, org_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._by_org[org_id].add(ws)
        logger.info("WS connected org=%s (total=%d)", org_id, len(self._by_org[org_id]))

    async def disconnect(self, org_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._by_org[org_id].discard(ws)
            if not self._by_org[org_id]:
                self._by_org.pop(org_id, None)

    async def broadcast(self, event: TelemetryEvent) -> None:
        """Send an event to every client of the event's organization."""
        payload = event.model_dump_json()
        async with self._lock:
            targets = list(self._by_org.get(event.organization_id, set()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 — drop broken sockets
                dead.append(ws)
        for ws in dead:
            await self.disconnect(event.organization_id, ws)


manager = ConnectionManager()


async def publish_telemetry(event: TelemetryEvent) -> None:
    """Publish a telemetry event to Redis for cross-worker fan-out."""
    await redis_client.publish(settings.TELEMETRY_CHANNEL, event.model_dump_json())


async def redis_subscriber() -> None:
    """Background task: consume the Redis channel and fan out to WS clients.

    Started/cancelled by the FastAPI lifespan handler.
    """
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(settings.TELEMETRY_CHANNEL)
    logger.info("Subscribed to Redis channel %s", settings.TELEMETRY_CHANNEL)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                data = json.loads(message["data"])
                event = TelemetryEvent.model_validate(data)
            except Exception:  # noqa: BLE001 — ignore malformed payloads
                logger.exception("Failed to parse telemetry message")
                continue
            await manager.broadcast(event)
    except asyncio.CancelledError:
        logger.info("Redis subscriber cancelled; shutting down")
        raise
    finally:
        await pubsub.unsubscribe(settings.TELEMETRY_CHANNEL)
        await pubsub.aclose()
