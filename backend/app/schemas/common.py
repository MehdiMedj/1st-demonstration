"""Reusable schema primitives."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LatLng(BaseModel):
    """A WGS84 coordinate pair."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lng: float = Field(..., ge=-180, le=180, description="Longitude in degrees")


class GeoJSONPolygon(BaseModel):
    """Minimal GeoJSON Polygon (coordinates as [[[lng, lat], ...]])."""

    type: str = Field(default="Polygon")
    coordinates: list[list[list[float]]]


class Message(BaseModel):
    detail: str
