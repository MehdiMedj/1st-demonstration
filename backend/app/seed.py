"""Seed demo data for the fixed demo tenant. Run: python -m app.seed"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models import Driver, Order, Organization, Place, Vehicle
from app.models.enums import DriverStatus, OrderStatus, VehicleStatus, VehicleType
from app.services.geo import point_ewkt, polygon_ewkt
from app.schemas.common import GeoJSONPolygon

DEMO_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# A few points around downtown San Francisco.
FLEET = [
    ("Truck 01", "1FTFW1ET0BFA00001", "FLEET-001", VehicleType.truck, 37.7793, -122.4193),
    ("Van 02", "1FTFW1ET0BFA00002", "FLEET-002", VehicleType.van, 37.7849, -122.4094),
    ("Van 03", "1FTFW1ET0BFA00003", "FLEET-003", VehicleType.van, 37.7699, -122.4469),
    ("Car 04", "1FTFW1ET0BFA00004", "FLEET-004", VehicleType.car, 37.7599, -122.4148),
]

DRIVERS = [
    ("Alex Rivera", "+14155550101"),
    ("Sam Chen", "+14155550102"),
    ("Jordan Blake", "+14155550103"),
    ("Taylor Kim", "+14155550104"),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        org = await db.get(Organization, DEMO_ORG_ID)
        if org is None:
            org = Organization(id=DEMO_ORG_ID, name="Demo Base", slug="demo-base")
            db.add(org)
            await db.flush()

        # Idempotent: wipe demo fleet before reseeding.
        await db.execute(delete(Order).where(Order.organization_id == DEMO_ORG_ID))
        await db.execute(delete(Driver).where(Driver.organization_id == DEMO_ORG_ID))
        await db.execute(delete(Vehicle).where(Vehicle.organization_id == DEMO_ORG_ID))
        await db.execute(delete(Place).where(Place.organization_id == DEMO_ORG_ID))
        await db.flush()

        vehicles = []
        for name, vin, plate, vtype, lat, lng in FLEET:
            v = Vehicle(
                organization_id=DEMO_ORG_ID,
                name=name,
                vin=vin,
                license_plate=plate,
                type=vtype,
                status=VehicleStatus.active,
                current_location=point_ewkt(lat, lng),
                speed=0.0,
                fuel_level=85.0,
            )
            db.add(v)
            vehicles.append(v)
        await db.flush()

        for (name, phone), v in zip(DRIVERS, vehicles):
            db.add(
                Driver(
                    organization_id=DEMO_ORG_ID,
                    name=name,
                    phone=phone,
                    status=DriverStatus.available,
                )
            )

        # Two geofenced places (warehouse + delivery zone).
        warehouse = Place(
            organization_id=DEMO_ORG_ID,
            name="Central Warehouse",
            address="200 Market St, San Francisco, CA",
            location=point_ewkt(37.7936, -122.3965),
            polygon_boundary=polygon_ewkt(
                GeoJSONPolygon(
                    coordinates=[[
                        [-122.3985, 37.7946],
                        [-122.3945, 37.7946],
                        [-122.3945, 37.7926],
                        [-122.3985, 37.7926],
                        [-122.3985, 37.7946],
                    ]]
                )
            ),
        )
        dropzone = Place(
            organization_id=DEMO_ORG_ID,
            name="Mission Delivery Zone",
            address="Mission District, San Francisco, CA",
            location=point_ewkt(37.7599, -122.4148),
        )
        db.add_all([warehouse, dropzone])
        await db.flush()

        # A couple of pending orders on the board.
        db.add_all([
            Order(
                organization_id=DEMO_ORG_ID,
                tracking_number="FLT-DEMO0001",
                pickup_place_id=warehouse.id,
                dropoff_place_id=dropzone.id,
                status=OrderStatus.pending,
            ),
            Order(
                organization_id=DEMO_ORG_ID,
                tracking_number="FLT-DEMO0002",
                pickup_place_id=warehouse.id,
                dropoff_place_id=dropzone.id,
                status=OrderStatus.pending,
            ),
        ])

        await db.commit()
        result = await db.execute(
            select(Vehicle).where(Vehicle.organization_id == DEMO_ORG_ID)
        )
        print(f"Seeded {len(result.scalars().all())} vehicles for org {DEMO_ORG_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
