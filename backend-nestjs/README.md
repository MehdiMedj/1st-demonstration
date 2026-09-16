# FleetOS Backend — NestJS variant

A drop-in alternative to the FastAPI backend (`../backend`). Same PostgreSQL +
PostGIS schema, same Redis telemetry channel, same HTTP + WebSocket contract —
so the existing Next.js frontend works against either backend unchanged.

## Stack

NestJS 10 · TypeORM 0.3 · PostgreSQL + PostGIS · ioredis · native WebSockets
(`@nestjs/platform-ws`).

## Design notes

- **Same schema.** Geography columns (`geography(Point/Polygon, 4326)`) are
  managed via raw parameterized SQL (`ST_GeogFromText`, `ST_DWithin`,
  `ST_Contains`) so responses are byte-compatible with the FastAPI backend
  (snake_case keys, `location: {lat, lng}`).
- **One schema owner.** The bundled TypeORM migration is fully idempotent
  (`CREATE ... IF NOT EXISTS`, guarded enum creation), so it bootstraps a fresh
  database and no-ops against one already created by the FastAPI Alembic
  migration. Run only one backend's migrations per database.
- **Realtime.** Telemetry is published to Redis and fanned out to native
  WebSocket clients per tenant — horizontally scalable, identical to FastAPI.

## Run (standalone, against local Postgres + Redis)

```bash
cp .env.example .env
npm install
npm run migration:run     # bootstraps schema + demo tenant (idempotent)
npm run start:dev
```

- API:   http://localhost:8000/api/v1
- Health: http://localhost:8000/health
- WS:     ws://localhost:8000/api/v1/ws/telemetry?org_id=<uuid>

To point the frontend here, no change is needed — it already targets
`http://localhost:8000`.

## Endpoints

Identical surface to the FastAPI backend: CRUD for `/vehicles`, `/drivers`,
`/places`; `GET /vehicles/nearby`; `GET /places/containing`;
`POST /telemetry`; `POST /orders/assign`; `WS /ws/telemetry`.
