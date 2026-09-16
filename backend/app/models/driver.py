"""Driver model."""
from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import DriverStatus


class Driver(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "drivers"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # A driver may be assigned to at most one vehicle (unique).
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, name="driver_status"),
        default=DriverStatus.available,
        nullable=False,
        index=True,
    )

    organization = relationship("Organization", back_populates="drivers")
    vehicle = relationship("Vehicle", back_populates="driver")
