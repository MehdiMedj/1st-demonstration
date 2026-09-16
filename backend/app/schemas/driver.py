"""Driver schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DriverStatus


class DriverBase(BaseModel):
    name: str = Field(..., max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    status: DriverStatus = DriverStatus.available
    vehicle_id: uuid.UUID | None = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    status: DriverStatus | None = None
    vehicle_id: uuid.UUID | None = None


class DriverRead(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
