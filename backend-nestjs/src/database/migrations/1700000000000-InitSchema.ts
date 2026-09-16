import { MigrationInterface, QueryRunner } from 'typeorm';

/**
 * Idempotent bootstrap that mirrors the FastAPI backend's Alembic schema.
 * Safe to run against a fresh database OR one already created by Alembic
 * (everything is IF NOT EXISTS / guarded), so both backends share one schema.
 */
export class InitSchema1700000000000 implements MigrationInterface {
  name = 'InitSchema1700000000000';

  public async up(q: QueryRunner): Promise<void> {
    await q.query(`CREATE EXTENSION IF NOT EXISTS postgis`);
    await q.query(`CREATE EXTENSION IF NOT EXISTS pgcrypto`);

    await q.query(`DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='vehicle_type') THEN
        CREATE TYPE vehicle_type AS ENUM ('van','truck','car','motorcycle','other'); END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='vehicle_status') THEN
        CREATE TYPE vehicle_status AS ENUM ('active','maintenance','en_route'); END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='driver_status') THEN
        CREATE TYPE driver_status AS ENUM ('available','on_trip','off_duty'); END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='order_status') THEN
        CREATE TYPE order_status AS ENUM ('pending','dispatched','en_route','completed','cancelled'); END IF;
    END $$;`);

    await q.query(`CREATE TABLE IF NOT EXISTS organizations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name varchar(255) NOT NULL,
      slug varchar(120) NOT NULL UNIQUE,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )`);

    await q.query(`CREATE TABLE IF NOT EXISTS vehicles (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      name varchar(255) NOT NULL,
      vin varchar(64) UNIQUE,
      license_plate varchar(32),
      type vehicle_type NOT NULL DEFAULT 'van',
      status vehicle_status NOT NULL DEFAULT 'active',
      current_location geography(Point,4326),
      speed double precision,
      fuel_level double precision,
      last_seen_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_vehicles_organization_id ON vehicles(organization_id)`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_vehicles_current_location ON vehicles USING gist(current_location)`);

    await q.query(`CREATE TABLE IF NOT EXISTS drivers (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      vehicle_id uuid UNIQUE REFERENCES vehicles(id) ON DELETE SET NULL,
      name varchar(255) NOT NULL,
      phone varchar(32),
      status driver_status NOT NULL DEFAULT 'available',
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_drivers_organization_id ON drivers(organization_id)`);

    await q.query(`CREATE TABLE IF NOT EXISTS places (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      name varchar(255) NOT NULL,
      address text,
      location geography(Point,4326),
      polygon_boundary geography(Polygon,4326),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_places_organization_id ON places(organization_id)`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_places_polygon_boundary ON places USING gist(polygon_boundary)`);

    await q.query(`CREATE TABLE IF NOT EXISTS orders (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      tracking_number varchar(40) NOT NULL UNIQUE,
      pickup_place_id uuid REFERENCES places(id) ON DELETE SET NULL,
      dropoff_place_id uuid REFERENCES places(id) ON DELETE SET NULL,
      driver_id uuid REFERENCES drivers(id) ON DELETE SET NULL,
      vehicle_id uuid REFERENCES vehicles(id) ON DELETE SET NULL,
      status order_status NOT NULL DEFAULT 'pending',
      route_polyline text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    )`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_orders_organization_id ON orders(organization_id)`);

    await q.query(`CREATE TABLE IF NOT EXISTS telemetry_pings (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      vehicle_id uuid NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
      location geography(Point,4326) NOT NULL,
      speed double precision,
      fuel_level double precision,
      recorded_at timestamptz NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    )`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_telemetry_pings_vehicle_id ON telemetry_pings(vehicle_id)`);
    await q.query(`CREATE INDEX IF NOT EXISTS ix_telemetry_pings_location ON telemetry_pings USING gist(location)`);

    await q.query(`INSERT INTO organizations (id, name, slug)
      VALUES ('00000000-0000-0000-0000-000000000001','Demo Base','demo-base')
      ON CONFLICT (id) DO NOTHING`);
  }

  public async down(q: QueryRunner): Promise<void> {
    await q.query(`DROP TABLE IF EXISTS telemetry_pings`);
    await q.query(`DROP TABLE IF EXISTS orders`);
    await q.query(`DROP TABLE IF EXISTS places`);
    await q.query(`DROP TABLE IF EXISTS drivers`);
    await q.query(`DROP TABLE IF EXISTS vehicles`);
    await q.query(`DROP TABLE IF EXISTS organizations`);
  }
}
