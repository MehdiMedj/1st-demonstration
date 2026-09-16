# FleetOS — Fleet Management & Logistics Operating System

An open-source, self-hostable Fleet Management & Logistics OS (inspired by Fleetbase).
Multi-tenant fleet operations, live driver telematics, geofencing, and a real-time
dispatcher dashboard.

## Tech Stack

| Layer        | Technology                                                            |
| ------------ | -------------------------------------------------------------------- |
| Backend      | FastAPI (Python 3.12), SQLAlchemy 2.0 (async), GeoAlchemy2, Alembic |
| Database     | PostgreSQL 16 + PostGIS 3.4 (geospatial)                            |
| Realtime     | Redis 7 Pub/Sub + WebSockets                                        |
| Frontend     | Next.js 14 (App Router), Tailwind CSS, Shadcn UI, MapLibre GL       |
| Infra        | Docker Compose                                                       |

## Architecture

```
                    ┌──────────────────────────────────────────┐
   Driver apps ───► │  POST /api/v1/telemetry                   │
   (GPS pings)      │        │                                  │
                    │        ▼                                  │
                    │  FastAPI  ──write──► PostgreSQL + PostGIS  │
                    │     │                                     │
                    │     └──publish──► Redis Pub/Sub channel   │
                    │                        │                  │
                    │                        ▼                  │
   Dispatchers ◄────┤  WebSocket /api/v1/ws/telemetry ◄─────────┤
   (dashboard)      │        (fan-out to connected clients)     │
                    └──────────────────────────────────────────┘
```

- **Ingestion is decoupled from broadcast.** Telemetry is persisted, then published to
  Redis. Every API worker subscribes to Redis and fans out to its own WebSocket clients,
  so the system scales horizontally behind a load balancer.
- **Multi-tenancy** is enforced at the query layer: every core row carries an
  `organization_id`, and requests are scoped by an `X-Org-Id` header (swap for JWT claims
  in production).
- **Geospatial** queries (`nearby`, geofence containment) run in PostGIS via `ST_DWithin`
  / `ST_Contains` on `geography` columns.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Then:

- API docs (Swagger):  http://localhost:8000/docs
- Dispatcher dashboard: http://localhost:3000/dashboard
- Postgres:             localhost:5432 (fleetos / fleetos)

### Backend variants (FastAPI or NestJS)

The default `backend/` service is **FastAPI**. A fully equivalent **NestJS**
implementation lives in `backend-nestjs/` — same schema, same Redis channel,
same HTTP + native-WebSocket contract, so the frontend works against either
unchanged. To run the NestJS backend instead:

```bash
docker compose -f docker-compose.yml -f docker-compose.nestjs.yml up --build
```

Run only one backend's migrations against a given database (both produce the
identical schema).

Migrations run automatically on backend startup (`alembic upgrade head`). To seed demo
data:

```bash
docker compose exec backend python -m app.seed
```

## Getting started & using it

A step-by-step runbook to go from a clean checkout to a working dispatcher.

### 1. Start the stack

```bash
git clone https://github.com/MehdiMedj/1st-demonstration.git
cd 1st-demonstration
cp .env.example .env
docker compose up --build
```

This starts four containers — **PostGIS**, **Redis**, the **FastAPI backend**
(which runs `alembic upgrade head` on boot), and the **Next.js frontend**. Wait
for the backend to log `Application startup complete`. Ports **3000, 8000, 5432,
6379** must be free on the host.

### 2. Load demo data (one time)

```bash
docker compose exec backend python -m app.seed
```

Creates a demo tenant with 4 vehicles, 4 drivers, 2 geofenced places, and 2
pending orders.

### 3. Open it

| What                     | URL                                   |
| ------------------------ | ------------------------------------- |
| Dispatcher dashboard     | http://localhost:3000/dashboard       |
| API docs (Swagger)       | http://localhost:8000/docs            |
| Health check             | http://localhost:8000/health          |

### 4. Use it

On the **dashboard** you'll see the seeded fleet on the map and the orders in the
**Pending** column:

- Click a vehicle marker for a status tooltip (speed, fuel).
- On a Pending order click **Assign** → it moves to **Assigned** and the vehicle
  flips to *en route*; then **Start trip** → **Complete** walks it across the board.

Every API request carries an `X-Org-Id` header — the multi-tenancy key (swap for
JWT claims in production). The seeded demo tenant id is
`00000000-0000-0000-0000-000000000001`.

Drive a vehicle live from the CLI — the marker moves instantly over the WebSocket:

```bash
ORG=00000000-0000-0000-0000-000000000001

# list vehicles, copy an "id"
curl -s -H "X-Org-Id: $ORG" http://localhost:8000/api/v1/vehicles | jq '.[].id'

# push a GPS/telematics ping (replace <VEHICLE_ID>)
curl -s -X POST http://localhost:8000/api/v1/telemetry \
  -H "X-Org-Id: $ORG" -H "Content-Type: application/json" \
  -d '{"vehicle_id":"<VEHICLE_ID>","latitude":37.7849,"longitude":-122.4094,"speed":45,"fuel_level":80}'

# nearest vehicles to a point (PostGIS ST_DWithin)
curl -s -H "X-Org-Id: $ORG" \
  "http://localhost:8000/api/v1/vehicles/nearby?lat=37.7749&lng=-122.4194&radius=5000" | jq
```

### Stop / reset

```bash
docker compose down       # stop, keep data
docker compose down -v    # stop and wipe the database volume
```

### Local dev (hot reload, no Docker for the apps)

Run only the datastores in Docker, then the apps on the host:

```bash
# datastores
docker compose up db redis

# backend (terminal 2)
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+asyncpg://fleetos:fleetos@localhost:5432/fleetos
export DATABASE_URL_SYNC=postgresql+psycopg://fleetos:fleetos@localhost:5432/fleetos
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head && python -m app.seed
uvicorn app.main:app --reload

# frontend (terminal 3)
cd frontend && npm install && npm run dev
```

## Deploy to a public URL

The app is host-agnostic (managed `DATABASE_URL` auto-handled; frontend API/WS
URLs resolved at runtime). A one-click **Render blueprint** ([`render.yaml`](./render.yaml))
provisions managed PostgreSQL+PostGIS, Redis, and both web services. Full
instructions — plus Railway and single-VM options — are in
**[DEPLOY.md](./DEPLOY.md)**.

## Repository layout

```
.
├── docker-compose.yml
├── .env.example
├── backend/                 # FastAPI service
│   ├── app/
│   │   ├── main.py          # app factory, lifespan, Redis<->WS bridge
│   │   ├── core/            # config, db session, redis client
│   │   ├── models/          # SQLAlchemy ORM (PostGIS geography columns)
│   │   ├── schemas/         # Pydantic v2 request/response models
│   │   ├── api/v1/          # routers: vehicles, drivers, places, orders, telemetry, ws
│   │   └── services/        # dispatch logic, geo helpers, broadcast bus
│   └── alembic/             # migrations (enables PostGIS, creates schema)
└── frontend/                # Next.js dispatcher dashboard
    ├── app/dashboard/       # map + kanban board
    ├── components/          # FleetMap, DispatchBoard, ui/*
    └── lib/                 # api client, ws hook, types
```

## Key API endpoints

| Method | Path                                            | Purpose                                  |
| ------ | ----------------------------------------------- | ---------------------------------------- |
| CRUD   | `/api/v1/vehicles`                              | Vehicle management                       |
| CRUD   | `/api/v1/drivers`                               | Driver management                        |
| CRUD   | `/api/v1/places`                                | Geofenced places (polygon boundaries)    |
| GET    | `/api/v1/vehicles/nearby?lat=&lng=&radius=`     | PostGIS `ST_DWithin` radius search       |
| POST   | `/api/v1/telemetry`                             | Ingest GPS/telematics ping               |
| POST   | `/api/v1/orders/assign`                         | Assign driver+vehicle, recompute status  |
| WS     | `/api/v1/ws/telemetry`                          | Live vehicle coordinate stream           |

## License

MIT
