# Deploying FleetOS to a public URL

FleetOS is four moving parts — **PostgreSQL + PostGIS**, **Redis**, the
**backend API**, and the **Next.js frontend** — so "deploy" means standing up a
managed database + cache and two web services. The app is written to be
host-agnostic:

- The backend accepts a plain managed `DATABASE_URL` (`postgres://…?sslmode=require`)
  and derives the async/sync SQLAlchemy URLs + TLS itself.
- The frontend reads its API/WebSocket URLs **at runtime** (injected via
  `API_HOST` / `API_BASE_URL`), so nothing is baked to `localhost` at build time.

> You deploy under **your own** cloud account — that's what produces the live
> URL. The repo ships the config; the final click/login is yours.

## Option A — Render (recommended, one-click blueprint)

Render offers managed PostgreSQL **with PostGIS**, managed Redis, and Docker web
services described in a single [`render.yaml`](./render.yaml) blueprint.

1. Push this branch to your GitHub repo (already done).
2. In Render: **New + → Blueprint**, select the repo and this branch.
3. Render reads `render.yaml` and provisions `fleetos-db`, `fleetos-redis`,
   `fleetos-backend`, and `fleetos-frontend`. Click **Apply**.
4. First deploy: the backend runs `alembic upgrade head` (creates schema +
   enables PostGIS). Wait for both web services to go **Live**.
5. Seed demo data once — in the `fleetos-backend` service **Shell** tab:
   ```bash
   python -m app.seed
   ```
6. Open the `fleetos-frontend` URL (e.g. `https://fleetos-frontend.onrender.com`)
   → `/dashboard`. Share that URL.

Notes:
- Free Postgres/Redis are used so it costs nothing; they idle/expire on free
  tier — raise `plan:` in `render.yaml` for anything real.
- If your account calls Redis "Key Value", change `type: redis` to
  `type: keyvalue` in `render.yaml`.

## Option B — Railway

1. New Project → **Deploy from GitHub repo**.
2. Add plugins: **PostgreSQL** (enable PostGIS: `CREATE EXTENSION postgis;` — or
   use the PostGIS template) and **Redis**.
3. Add two services from the repo with root directories `backend` and
   `frontend` (both build via their `Dockerfile`).
4. Backend variables: `DATABASE_URL` (from the PG plugin), `REDIS_URL` (from the
   Redis plugin), `FRONTEND_URL` (the frontend's public domain). Start command:
   `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"`.
5. Frontend variable: `API_HOST` = the backend's public domain (no scheme).
6. Deploy, then run `python -m app.seed` in the backend service shell.

## Option C — Any Docker host / single VM

On a VM with Docker installed you can run the bundled Compose stack directly and
put a reverse proxy (Caddy/Nginx) with TLS in front:

```bash
git clone <repo> && cd 1st-demonstration
cp .env.example .env
# set BACKEND_CORS_ORIGINS + the frontend's NEXT_PUBLIC/API_HOST to your domain
docker compose up -d --build
docker compose exec backend python -m app.seed
```

Point your domain at the VM, terminate TLS at the proxy, and route `/` to the
frontend (`:3000`) and the API/WS to the backend (`:8000`).

## Environment variables reference

**Backend**

| Var                    | Purpose                                                        |
| ---------------------- | ------------------------------------------------------------- |
| `DATABASE_URL`         | Postgres URL (managed `postgres://…` is fine; TLS auto-handled) |
| `DATABASE_URL_SYNC`    | Optional; derived from `DATABASE_URL` for Alembic if unset    |
| `REDIS_URL`            | Redis connection string                                       |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed origins                               |
| `FRONTEND_URL`         | Frontend origin/host to allow through CORS (host is fine)     |

**Frontend**

| Var              | Purpose                                                              |
| ---------------- | ------------------------------------------------------------------- |
| `API_HOST`       | Backend host (no scheme); becomes `https://<host>` + `wss://<host>` |
| `API_BASE_URL`   | Full backend URL (overrides `API_HOST` if you prefer explicit)      |
| `WS_URL`         | Full WebSocket URL (optional; derived from `API_HOST` otherwise)    |

The map uses public OpenStreetMap tiles and needs outbound internet; swap in a
keyed tile provider (MapTiler/Mapbox) in `frontend/components/FleetMap.tsx` for
production traffic.
