"""Helpers to convert between app coordinates and PostGIS geography values.

We standardise on EWKT strings on the write path (GeoAlchemy2 accepts them for
``geography`` columns) and shapely for parsing the WKB elements read back.
"""
from __future__ import annotations

from typing import Any

from geoalchemy2.shape import to_shape

from app.schemas.common import GeoJSONPolygon, LatLng


def point_ewkt(lat: float, lng: float) -> str:
    """Build an EWKT POINT (note: PostGIS is lng/lat order)."""
    return f"SRID=4326;POINT({lng} {lat})"


def polygon_ewkt(polygon: GeoJSONPolygon) -> str:
    """Build an EWKT POLYGON from a GeoJSON polygon ([lng, lat] rings)."""
    rings = []
    for ring in polygon.coordinates:
        pts = ", ".join(f"{lng} {lat}" for lng, lat in ring)
        rings.append(f"({pts})")
    return f"SRID=4326;POLYGON({', '.join(rings)})"


def to_latlng(geo: Any | None) -> LatLng | None:
    """Convert a geography(Point) WKB element to a LatLng, or None."""
    if geo is None:
        return None
    shape = to_shape(geo)  # shapely Point (x=lng, y=lat)
    return LatLng(lat=shape.y, lng=shape.x)


def to_geojson_polygon(geo: Any | None) -> GeoJSONPolygon | None:
    """Convert a geography(Polygon) WKB element to a GeoJSON polygon."""
    if geo is None:
        return None
    shape = to_shape(geo)
    coords = [list(map(list, shape.exterior.coords))]
    for interior in shape.interiors:
        coords.append(list(map(list, interior.coords)))
    return GeoJSONPolygon(coordinates=coords)
