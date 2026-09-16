"""ORM -> Pydantic serializers that handle PostGIS geography columns."""
from __future__ import annotations

from app.models import Place, Vehicle
from app.schemas.place import PlaceRead
from app.schemas.vehicle import VehicleRead
from app.services.geo import to_geojson_polygon, to_latlng


def serialize_vehicle(v: Vehicle) -> VehicleRead:
    return VehicleRead(
        id=v.id,
        organization_id=v.organization_id,
        name=v.name,
        vin=v.vin,
        license_plate=v.license_plate,
        type=v.type,
        status=v.status,
        location=to_latlng(v.current_location),
        speed=v.speed,
        fuel_level=v.fuel_level,
        last_seen_at=v.last_seen_at,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


def serialize_place(p: Place) -> PlaceRead:
    return PlaceRead(
        id=p.id,
        organization_id=p.organization_id,
        name=p.name,
        address=p.address,
        location=to_latlng(p.location),
        polygon_boundary=to_geojson_polygon(p.polygon_boundary),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
