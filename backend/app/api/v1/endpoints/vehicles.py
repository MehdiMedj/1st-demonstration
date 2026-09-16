"""Vehicle CRUD + PostGIS nearby search."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_DWithin, ST_Distance
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_org_id
from app.api.v1.serializers import serialize_vehicle
from app.core.database import get_db
from app.models import Vehicle
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleNearby,
    VehicleRead,
    VehicleUpdate,
)
from app.services.geo import point_ewkt

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleRead])
async def list_vehicles(
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Vehicle)
        .where(Vehicle.organization_id == org_id)
        .order_by(Vehicle.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [serialize_vehicle(v) for v in result.scalars().all()]


@router.get("/nearby", response_model=list[VehicleNearby])
async def vehicles_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(5000, gt=0, description="Search radius in metres"),
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Vehicles within `radius` metres of (lat,lng), nearest first (ST_DWithin)."""
    # Build an explicit geography literal so PostGIS picks the geography overloads
    # (metric distance / radius) unambiguously.
    point = func.ST_GeogFromText(point_ewkt(lat, lng))
    distance = ST_Distance(Vehicle.current_location, point)
    result = await db.execute(
        select(Vehicle, distance.label("distance_m"))
        .where(
            Vehicle.organization_id == org_id,
            Vehicle.current_location.isnot(None),
            ST_DWithin(Vehicle.current_location, point, radius),
        )
        .order_by(distance.asc())
    )
    out: list[VehicleNearby] = []
    for vehicle, distance_m in result.all():
        base = serialize_vehicle(vehicle)
        out.append(VehicleNearby(**base.model_dump(), distance_m=float(distance_m)))
    return out


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    vehicle = Vehicle(
        organization_id=org_id,
        name=payload.name,
        vin=payload.vin,
        license_plate=payload.license_plate,
        type=payload.type,
        status=payload.status,
        current_location=(
            point_ewkt(payload.location.lat, payload.location.lng)
            if payload.location
            else None
        ),
    )
    db.add(vehicle)
    await db.flush()
    await db.refresh(vehicle)
    return serialize_vehicle(vehicle)


@router.get("/{vehicle_id}", response_model=VehicleRead)
async def get_vehicle(
    vehicle_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await _get(db, vehicle_id, org_id)
    return serialize_vehicle(vehicle)


@router.patch("/{vehicle_id}", response_model=VehicleRead)
async def update_vehicle(
    vehicle_id: uuid.UUID,
    payload: VehicleUpdate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await _get(db, vehicle_id, org_id)
    data = payload.model_dump(exclude_unset=True)
    if "location" in data:
        loc = data.pop("location")
        vehicle.current_location = (
            point_ewkt(loc["lat"], loc["lng"]) if loc else None
        )
    for field, value in data.items():
        setattr(vehicle, field, value)
    await db.flush()
    await db.refresh(vehicle)
    return serialize_vehicle(vehicle)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(
    vehicle_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    vehicle = await _get(db, vehicle_id, org_id)
    await db.delete(vehicle)


async def _get(db: AsyncSession, vehicle_id: uuid.UUID, org_id: uuid.UUID) -> Vehicle:
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id, Vehicle.organization_id == org_id
        )
    )
    vehicle = result.scalar_one_or_none()
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle
