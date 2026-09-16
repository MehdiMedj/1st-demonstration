"""Place & geofence CRUD, plus a geofence containment check."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from geoalchemy2.functions import ST_Contains, ST_GeomFromText
from sqlalchemy import cast, select
from geoalchemy2 import Geometry
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_org_id
from app.api.v1.serializers import serialize_place
from app.core.database import get_db
from app.models import Place
from app.schemas.place import PlaceCreate, PlaceRead, PlaceUpdate
from app.services.geo import point_ewkt, polygon_ewkt

router = APIRouter(prefix="/places", tags=["places"])


@router.get("", response_model=list[PlaceRead])
async def list_places(
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Place)
        .where(Place.organization_id == org_id)
        .order_by(Place.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [serialize_place(p) for p in result.scalars().all()]


@router.post("", response_model=PlaceRead, status_code=status.HTTP_201_CREATED)
async def create_place(
    payload: PlaceCreate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    place = Place(
        organization_id=org_id,
        name=payload.name,
        address=payload.address,
        location=(
            point_ewkt(payload.location.lat, payload.location.lng)
            if payload.location
            else None
        ),
        polygon_boundary=(
            polygon_ewkt(payload.polygon_boundary)
            if payload.polygon_boundary
            else None
        ),
    )
    db.add(place)
    await db.flush()
    await db.refresh(place)
    return serialize_place(place)


@router.get("/containing", response_model=list[PlaceRead])
async def places_containing_point(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Geofences (places) whose polygon contains the given point."""
    point_geom = ST_GeomFromText(f"POINT({lng} {lat})", 4326)
    result = await db.execute(
        select(Place).where(
            Place.organization_id == org_id,
            Place.polygon_boundary.isnot(None),
            ST_Contains(cast(Place.polygon_boundary, Geometry), point_geom),
        )
    )
    return [serialize_place(p) for p in result.scalars().all()]


@router.get("/{place_id}", response_model=PlaceRead)
async def get_place(
    place_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    return serialize_place(await _get(db, place_id, org_id))


@router.patch("/{place_id}", response_model=PlaceRead)
async def update_place(
    place_id: uuid.UUID,
    payload: PlaceUpdate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    place = await _get(db, place_id, org_id)
    data = payload.model_dump(exclude_unset=True)
    if "location" in data:
        loc = data.pop("location")
        place.location = point_ewkt(loc["lat"], loc["lng"]) if loc else None
    if "polygon_boundary" in data:
        poly = data.pop("polygon_boundary")
        place.polygon_boundary = (
            polygon_ewkt(payload.polygon_boundary) if poly else None
        )
    for field, value in data.items():
        setattr(place, field, value)
    await db.flush()
    await db.refresh(place)
    return serialize_place(place)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_place(
    place_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    place = await _get(db, place_id, org_id)
    await db.delete(place)


async def _get(db: AsyncSession, place_id: uuid.UUID, org_id: uuid.UUID) -> Place:
    result = await db.execute(
        select(Place).where(Place.id == place_id, Place.organization_id == org_id)
    )
    place = result.scalar_one_or_none()
    if place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place
