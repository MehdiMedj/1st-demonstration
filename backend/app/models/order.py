"""Order / Dispatch model."""
from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import OrderStatus


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tracking_number: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )

    pickup_place_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    dropoff_place_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("places.id", ondelete="SET NULL"), nullable=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.pending,
        nullable=False,
        index=True,
    )
    # Encoded route geometry (e.g. Google/Mapbox polyline) for map rendering.
    route_polyline: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization = relationship("Organization", back_populates="orders")
    pickup_place = relationship("Place", foreign_keys=[pickup_place_id])
    dropoff_place = relationship("Place", foreign_keys=[dropoff_place_id])
    driver = relationship("Driver", foreign_keys=[driver_id])
    vehicle = relationship("Vehicle", foreign_keys=[vehicle_id])
