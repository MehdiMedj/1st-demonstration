"""Driver CRUD."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_org_id
from app.core.database import get_db
from app.models import Driver
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverRead])
async def list_drivers(
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Driver)
        .where(Driver.organization_id == org_id)
        .order_by(Driver.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.post("", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    driver = Driver(organization_id=org_id, **payload.model_dump())
    db.add(driver)
    await db.flush()
    await db.refresh(driver)
    return driver


@router.get("/{driver_id}", response_model=DriverRead)
async def get_driver(
    driver_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get(db, driver_id, org_id)


@router.patch("/{driver_id}", response_model=DriverRead)
async def update_driver(
    driver_id: uuid.UUID,
    payload: DriverUpdate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    driver = await _get(db, driver_id, org_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(driver, field, value)
    await db.flush()
    await db.refresh(driver)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(
    driver_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    driver = await _get(db, driver_id, org_id)
    await db.delete(driver)


async def _get(db: AsyncSession, driver_id: uuid.UUID, org_id: uuid.UUID) -> Driver:
    result = await db.execute(
        select(Driver).where(Driver.id == driver_id, Driver.organization_id == org_id)
    )
    driver = result.scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver
