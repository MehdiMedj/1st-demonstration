"""Order / dispatch schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus


class OrderBase(BaseModel):
    pickup_place_id: uuid.UUID | None = None
    dropoff_place_id: uuid.UUID | None = None
    route_polyline: str | None = None


class OrderCreate(OrderBase):
    # Optional client-supplied tracking number; generated if omitted.
    tracking_number: str | None = Field(default=None, max_length=40)


class OrderUpdate(BaseModel):
    pickup_place_id: uuid.UUID | None = None
    dropoff_place_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    status: OrderStatus | None = None
    route_polyline: str | None = None


class OrderAssign(BaseModel):
    """Payload for POST /orders/assign."""

    order_id: uuid.UUID
    driver_id: uuid.UUID
    vehicle_id: uuid.UUID


class OrderRead(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    tracking_number: str
    driver_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
