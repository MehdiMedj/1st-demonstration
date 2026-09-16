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

Migrations run automatically on backend startup (`alembic upgrade head`). To seed demo
data:

```bash
docker compose exec backend python -m app.seed
```

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
