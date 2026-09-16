"""Order / dispatch CRUD + the assign endpoint."""
from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_org_id
from app.core.database import get_db
from app.models import Order
from app.schemas.order import (
    OrderAssign,
    OrderCreate,
    OrderRead,
    OrderUpdate,
)
from app.services.dispatch import assign_order

router = APIRouter(prefix="/orders", tags=["orders"])


def _tracking_number() -> str:
    return f"FLT-{secrets.token_hex(4).upper()}"


@router.get("", response_model=list[OrderRead])
async def list_orders(
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0),
):
    result = await db.execute(
        select(Order)
        .where(Order.organization_id == org_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    order = Order(
        organization_id=org_id,
        tracking_number=payload.tracking_number or _tracking_number(),
        pickup_place_id=payload.pickup_place_id,
        dropoff_place_id=payload.dropoff_place_id,
        route_polyline=payload.route_polyline,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


@router.post("/assign", response_model=OrderRead)
async def assign(
    payload: OrderAssign,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    """Assign a driver+vehicle to an order and recompute statuses."""
    return await assign_order(
        db,
        org_id=org_id,
        order_id=payload.order_id,
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get(db, order_id, org_id)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdate,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    order = await _get(db, order_id, org_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    await db.flush()
    await db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_org_id),
    db: AsyncSession = Depends(get_db),
):
    order = await _get(db, order_id, org_id)
    await db.delete(order)


async def _get(db: AsyncSession, order_id: uuid.UUID, org_id: uuid.UUID) -> Order:
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.organization_id == org_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
