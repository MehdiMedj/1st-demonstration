"""Vehicle model with a PostGIS geography(Point) current location."""
from __future__ import annotations

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import VehicleStatus, VehicleType


class Vehicle(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vin: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    license_plate: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type"),
        default=VehicleType.van,
        nullable=False,
    )
    status: Mapped[VehicleStatus] = mapped_column(
        Enum(VehicleStatus, name="vehicle_status"),
        default=VehicleStatus.active,
        nullable=False,
        index=True,
    )

    # Latest known position; SRID 4326 (WGS84). geography → metric distance queries.
    current_location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    # Denormalized latest telematics for fast dashboard reads.
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    organization = relationship("Organization", back_populates="vehicles")
    driver = relationship("Driver", back_populates="vehicle", uselist=False)
    telemetry = relationship(
        "TelemetryPing", back_populates="vehicle", cascade="all, delete-orphan"
    )
