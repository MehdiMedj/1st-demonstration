"""Telemetry ingestion endpoint.

Flow: validate vehicle -> persist immutable ping -> update denormalized
vehicle position -> publish event to Redis for realtime fan-out.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_org_id
from app.core.database import get_db
from app.models import TelemetryPing, Vehicle
from app.schemas.telemetry import TelemetryEvent, TelemetryIn
from app.services.broadcast import publish_telemetry
from app.services.geo import point_ewkt

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=TelemetryEvent)
async def ingest_telemetry(
    payload: TelemetryIn,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == payload.vehicle_id, Vehicle.organization_id == org_id
        )
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    point = point_ewkt(payload.latitude, payload.longitude)

    # 1) append-only history
    db.add(
        TelemetryPing(
            vehicle_id=vehicle.id,
            location=point,
            speed=payload.speed,
            fuel_level=payload.fuel_level,
            recorded_at=payload.timestamp,
        )
    )
    # 2) denormalized latest position for fast dashboard reads
    vehicle.current_location = point
    vehicle.speed = payload.speed
    vehicle.fuel_level = payload.fuel_level
    vehicle.last_seen_at = payload.timestamp

    await db.flush()

    # 3) broadcast (committed by the get_db dependency on success)
    event = TelemetryEvent(
        vehicle_id=vehicle.id,
        organization_id=org_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        fuel_level=payload.fuel_level,
        status=vehicle.status.value,
        timestamp=payload.timestamp,
    )
    await publish_telemetry(event)
    return event
