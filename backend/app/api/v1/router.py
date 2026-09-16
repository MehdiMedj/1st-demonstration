"""Aggregate v1 API router."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    drivers,
    orders,
    places,
    telemetry,
    vehicles,
    ws,
)

api_router = APIRouter()
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
api_router.include_router(places.router)
api_router.include_router(orders.router)
api_router.include_router(telemetry.router)
api_router.include_router(ws.router)
