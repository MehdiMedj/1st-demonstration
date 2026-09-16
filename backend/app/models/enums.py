"""Enumerations shared across models and schemas."""
from __future__ import annotations

import enum


class VehicleStatus(str, enum.Enum):
    active = "active"
    maintenance = "maintenance"
    en_route = "en_route"


class VehicleType(str, enum.Enum):
    van = "van"
    truck = "truck"
    car = "car"
    motorcycle = "motorcycle"
    other = "other"


class DriverStatus(str, enum.Enum):
    available = "available"
    on_trip = "on_trip"
    off_duty = "off_duty"


class OrderStatus(str, enum.Enum):
    pending = "pending"
    dispatched = "dispatched"
    en_route = "en_route"
    completed = "completed"
    cancelled = "cancelled"
