"""Place & geofence schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GeoJSONPolygon, LatLng


class PlaceBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: str | None = None
    location: LatLng | None = None
    # Geofence as GeoJSON polygon; coordinates are [lng, lat] rings.
    polygon_boundary: GeoJSONPolygon | None = None


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    address: str | None = None
    location: LatLng | None = None
    polygon_boundary: GeoJSONPolygon | None = None


class PlaceRead(PlaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
