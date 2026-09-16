"""Dispatch business rules: assigning a driver+vehicle to an order."""
from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Driver, Order, Vehicle
from app.models.enums import DriverStatus, OrderStatus, VehicleStatus


async def assign_order(
    db: AsyncSession,
    org_id: uuid.UUID,
    order_id: uuid.UUID,
    driver_id: uuid.UUID,
    vehicle_id: uuid.UUID,
) -> Order:
    """Assign a driver and vehicle to an order and recompute all statuses.

    Side effects (single transaction):
      - order.status  -> dispatched
      - driver.status -> on_trip, driver.vehicle_id -> vehicle
      - vehicle.status-> en_route
    """
    order = await _get_scoped(db, Order, order_id, org_id, "Order")
    driver = await _get_scoped(db, Driver, driver_id, org_id, "Driver")
    vehicle = await _get_scoped(db, Vehicle, vehicle_id, org_id, "Vehicle")

    if order.status in (OrderStatus.completed, OrderStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order is {order.status.value} and cannot be reassigned",
        )
    if driver.status == DriverStatus.on_trip and order.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver is already on a trip",
        )
    if vehicle.status == VehicleStatus.maintenance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is under maintenance",
        )

    order.driver_id = driver.id
    order.vehicle_id = vehicle.id
    order.status = OrderStatus.dispatched

    driver.status = DriverStatus.on_trip
    driver.vehicle_id = vehicle.id

    vehicle.status = VehicleStatus.en_route

    await db.flush()
    await db.refresh(order)
    return order


async def _get_scoped(
    db: AsyncSession,
    model: type,
    obj_id: uuid.UUID,
    org_id: uuid.UUID,
    label: str,
):
    result = await db.execute(
        select(model).where(model.id == obj_id, model.organization_id == org_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found"
        )
    return obj
