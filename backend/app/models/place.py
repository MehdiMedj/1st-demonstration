"""Place & Geofence model with a PostGIS geography(Polygon) boundary."""
from __future__ import annotations

import uuid

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Place(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "places"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Representative centroid (for map pins / quick distance).
    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )
    # Geofence boundary.
    polygon_boundary: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POLYGON", srid=4326), nullable=True
    )

    organization = relationship("Organization", back_populates="places")
