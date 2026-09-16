"""WebSocket endpoint streaming live vehicle telemetry to dispatchers."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.broadcast import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws/telemetry")
async def telemetry_ws(
    websocket: WebSocket,
    org_id: uuid.UUID = Query(..., description="Tenant/organization id to subscribe to"),
):
    """Dispatcher dashboard subscribes here; receives TelemetryEvent JSON frames.

    Connect: ws://host/api/v1/ws/telemetry?org_id=<uuid>

    Auth note: pass a signed token as a query param and verify it here in
    production (browsers can't set headers on the WS handshake).
    """
    await manager.connect(org_id, websocket)
    try:
        # We don't expect inbound messages, but keep the socket alive and
        # detect client disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(org_id, websocket)
    except Exception:  # noqa: BLE001
        await manager.disconnect(org_id, websocket)
