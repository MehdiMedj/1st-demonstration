"""initial schema: postgis, tenants, vehicles, drivers, places, orders, telemetry

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-16
"""
from typing import Sequence, Union

import geoalchemy2 as ga
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed demo tenant id — matches NEXT_PUBLIC_ORG_ID in .env.example.
DEMO_ORG_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    # PostGIS + gen_random_uuid().
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    vehicle_type = sa.Enum(
        "van", "truck", "car", "motorcycle", "other", name="vehicle_type"
    )
    vehicle_status = sa.Enum("active", "maintenance", "en_route", name="vehicle_status")
    driver_status = sa.Enum("available", "on_trip", "off_duty", name="driver_status")
    order_status = sa.Enum(
        "pending", "dispatched", "en_route", "completed", "cancelled", name="order_status"
    )

    # ─── organizations ───
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # ─── vehicles ───
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("vin", sa.String(64), unique=True, nullable=True),
        sa.Column("license_plate", sa.String(32), nullable=True),
        sa.Column("type", vehicle_type, nullable=False, server_default="van"),
        sa.Column("status", vehicle_status, nullable=False, server_default="active"),
        sa.Column("current_location",
                  ga.Geography(geometry_type="POINT", srid=4326, spatial_index=False),
                  nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("fuel_level", sa.Float(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vehicles_organization_id", "vehicles", ["organization_id"])
    op.create_index("ix_vehicles_license_plate", "vehicles", ["license_plate"])
    op.create_index("ix_vehicles_status", "vehicles", ["status"])
    op.create_index(
        "ix_vehicles_current_location", "vehicles", ["current_location"],
        postgresql_using="gist",
    )

    # ─── drivers ───
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("vehicles.id", ondelete="SET NULL"), unique=True, nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("status", driver_status, nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_drivers_organization_id", "drivers", ["organization_id"])
    op.create_index("ix_drivers_phone", "drivers", ["phone"])
    op.create_index("ix_drivers_status", "drivers", ["status"])

    # ─── places ───
    op.create_table(
        "places",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("location",
                  ga.Geography(geometry_type="POINT", srid=4326, spatial_index=False),
                  nullable=True),
        sa.Column("polygon_boundary",
                  ga.Geography(geometry_type="POLYGON", srid=4326, spatial_index=False),
                  nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_places_organization_id", "places", ["organization_id"])
    op.create_index("ix_places_location", "places", ["location"], postgresql_using="gist")
    op.create_index("ix_places_polygon_boundary", "places", ["polygon_boundary"], postgresql_using="gist")

    # ─── orders ───
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tracking_number", sa.String(40), nullable=False, unique=True),
        sa.Column("pickup_place_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("places.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dropoff_place_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("places.id", ondelete="SET NULL"), nullable=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", order_status, nullable=False, server_default="pending"),
        sa.Column("route_polyline", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_orders_organization_id", "orders", ["organization_id"])
    op.create_index("ix_orders_tracking_number", "orders", ["tracking_number"])
    op.create_index("ix_orders_status", "orders", ["status"])

    # ─── telemetry_pings (append-only time-series) ───
    op.create_table(
        "telemetry_pings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("location",
                  ga.Geography(geometry_type="POINT", srid=4326, spatial_index=False),
                  nullable=False),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("fuel_level", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_telemetry_pings_vehicle_id", "telemetry_pings", ["vehicle_id"])
    op.create_index("ix_telemetry_pings_recorded_at", "telemetry_pings", ["recorded_at"])
    op.create_index("ix_telemetry_pings_location", "telemetry_pings", ["location"], postgresql_using="gist")

    # ─── seed a demo tenant so the dashboard works out of the box ───
    op.execute(
        sa.text(
            "INSERT INTO organizations (id, name, slug) "
            "VALUES (:id, :name, :slug) ON CONFLICT (id) DO NOTHING"
        ).bindparams(id=DEMO_ORG_ID, name="Demo Base", slug="demo-base")
    )


def downgrade() -> None:
    op.drop_table("telemetry_pings")
    op.drop_table("orders")
    op.drop_table("places")
    op.drop_table("drivers")
    op.drop_table("vehicles")
    op.drop_table("organizations")
    for enum_name in ("order_status", "driver_status", "vehicle_status", "vehicle_type"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
