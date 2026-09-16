"""Telemetry ingestion & broadcast schemas."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelemetryIn(BaseModel):
    """Inbound telematics ping from a vehicle/driver device."""

    vehicle_id: uuid.UUID
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: float | None = Field(default=None, ge=0, description="km/h")
    fuel_level: float | None = Field(default=None, ge=0, le=100, description="percent")
    timestamp: datetime | None = Field(
        default=None,
        validate_default=True,  # ensure the validator runs when omitted
        description="Device time; defaults to server receipt time (UTC).",
    )

    @field_validator("timestamp")
    @classmethod
    def _default_ts(cls, v: datetime | None) -> datetime:
        return v or datetime.now(timezone.utc)


class TelemetryEvent(BaseModel):
    """Message broadcast over Redis / WebSocket to dispatcher clients."""

    model_config = ConfigDict(from_attributes=True)

    type: str = "vehicle.telemetry"
    vehicle_id: uuid.UUID
    organization_id: uuid.UUID
    latitude: float
    longitude: float
    speed: float | None = None
    fuel_level: float | None = None
    status: str
    timestamp: datetime
