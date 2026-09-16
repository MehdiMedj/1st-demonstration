"""Organization (tenant root) model."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Organization(UUIDMixin, TimestampMixin, Base):
    """A tenant. All fleet resources are isolated per organization/base."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)

    vehicles = relationship("Vehicle", back_populates="organization", cascade="all, delete-orphan")
    drivers = relationship("Driver", back_populates="organization", cascade="all, delete-orphan")
    places = relationship("Place", back_populates="organization", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="organization", cascade="all, delete-orphan")
