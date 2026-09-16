"""End-to-end API tests covering CRUD, PostGIS search, dispatch and telemetry."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1"


async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_missing_org_header_rejected(client: AsyncClient):
    r = await client.get(f"{API}/vehicles", headers={"X-Org-Id": ""})
    assert r.status_code in (400, 422)


async def test_vehicle_crud_and_nearby(client: AsyncClient):
    # Create at a distinctive point.
    lat, lng = 40.7484, -73.9857  # Empire State Building
    r = await client.post(
        f"{API}/vehicles",
        json={
            "name": "Test Rig",
            "type": "truck",
            "status": "active",
            "location": {"lat": lat, "lng": lng},
        },
    )
    assert r.status_code == 201, r.text
    v = r.json()
    vid = v["id"]
    assert v["location"]["lat"] == pytest.approx(lat, abs=1e-6)

    # Get
    r = await client.get(f"{API}/vehicles/{vid}")
    assert r.status_code == 200

    # Nearby: found within 1km, not within 1m.
    r = await client.get(f"{API}/vehicles/nearby", params={"lat": lat, "lng": lng, "radius": 1000})
    ids = [x["id"] for x in r.json()]
    assert vid in ids
    assert all("distance_m" in x for x in r.json())

    r = await client.get(f"{API}/vehicles/nearby", params={"lat": lat, "lng": lng, "radius": 1})
    far = await client.get(
        f"{API}/vehicles/nearby", params={"lat": 0, "lng": 0, "radius": 1000}
    )
    assert vid not in [x["id"] for x in far.json()]

    # Patch
    r = await client.patch(f"{API}/vehicles/{vid}", json={"status": "maintenance"})
    assert r.json()["status"] == "maintenance"

    # Delete
    r = await client.delete(f"{API}/vehicles/{vid}")
    assert r.status_code == 204
    r = await client.get(f"{API}/vehicles/{vid}")
    assert r.status_code == 404


async def test_telemetry_updates_position(client: AsyncClient):
    r = await client.post(
        f"{API}/vehicles", json={"name": "Telem Rig", "status": "active"}
    )
    vid = r.json()["id"]

    r = await client.post(
        f"{API}/telemetry",
        json={"vehicle_id": vid, "latitude": 51.5074, "longitude": -0.1278, "speed": 30},
    )
    assert r.status_code == 202, r.text
    assert r.json()["latitude"] == pytest.approx(51.5074, abs=1e-6)

    r = await client.get(f"{API}/vehicles/{vid}")
    body = r.json()
    assert body["location"]["lat"] == pytest.approx(51.5074, abs=1e-6)
    assert body["speed"] == 30
    assert body["last_seen_at"] is not None

    await client.delete(f"{API}/vehicles/{vid}")


async def test_telemetry_unknown_vehicle_404(client: AsyncClient):
    r = await client.post(
        f"{API}/telemetry",
        json={"vehicle_id": str(uuid.uuid4()), "latitude": 1, "longitude": 1},
    )
    assert r.status_code == 404


async def test_dispatch_assign_cascades_status(client: AsyncClient):
    v = (await client.post(f"{API}/vehicles", json={"name": "D-Veh", "status": "active"})).json()
    d = (await client.post(f"{API}/drivers", json={"name": "D-Driver"})).json()
    o = (await client.post(f"{API}/orders", json={})).json()

    r = await client.post(
        f"{API}/orders/assign",
        json={"order_id": o["id"], "driver_id": d["id"], "vehicle_id": v["id"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "dispatched"

    assert (await client.get(f"{API}/drivers/{d['id']}")).json()["status"] == "on_trip"
    assert (await client.get(f"{API}/vehicles/{v['id']}")).json()["status"] == "en_route"

    # Cleanup (order first: FK).
    await client.delete(f"{API}/orders/{o['id']}")
    await client.delete(f"{API}/drivers/{d['id']}")
    await client.delete(f"{API}/vehicles/{v['id']}")


async def test_place_geofence_containment(client: AsyncClient):
    # Square geofence around (10, 10) as [lng, lat] ring.
    poly = {
        "type": "Polygon",
        "coordinates": [[
            [9.99, 9.99], [10.01, 9.99], [10.01, 10.01], [9.99, 10.01], [9.99, 9.99],
        ]],
    }
    p = (await client.post(
        f"{API}/places",
        json={"name": "Geo Test", "location": {"lat": 10, "lng": 10}, "polygon_boundary": poly},
    )).json()

    inside = await client.get(f"{API}/places/containing", params={"lat": 10, "lng": 10})
    assert p["id"] in [x["id"] for x in inside.json()]

    outside = await client.get(f"{API}/places/containing", params={"lat": 20, "lng": 20})
    assert p["id"] not in [x["id"] for x in outside.json()]

    await client.delete(f"{API}/places/{p['id']}")
