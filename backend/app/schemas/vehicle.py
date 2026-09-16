"""Vehicle schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import VehicleStatus, VehicleType
from app.schemas.common import LatLng


class VehicleBase(BaseModel):
    name: str = Field(..., max_length=255)
    vin: str | None = Field(default=None, max_length=64)
    license_plate: str | None = Field(default=None, max_length=32)
    type: VehicleType = VehicleType.van
    status: VehicleStatus = VehicleStatus.active


class VehicleCreate(VehicleBase):
    location: LatLng | None = None


class VehicleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    vin: str | None = Field(default=None, max_length=64)
    license_plate: str | None = Field(default=None, max_length=32)
    type: VehicleType | None = None
    status: VehicleStatus | None = None
    location: LatLng | None = None


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    location: LatLng | None = None
    speed: float | None = None
    fuel_level: float | None = None
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class VehicleNearby(VehicleRead):
    distance_m: float = Field(..., description="Distance from query point in metres")
