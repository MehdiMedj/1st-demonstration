import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { CreateVehicleDto, UpdateVehicleDto } from '../common/dto';

const SELECT = `
  SELECT id, organization_id, name, vin, license_plate, type, status,
    CASE WHEN current_location IS NULL THEN NULL ELSE
      json_build_object('lat', ST_Y(current_location::geometry),
                        'lng', ST_X(current_location::geometry)) END AS location,
    speed, fuel_level, last_seen_at, created_at, updated_at
  FROM vehicles`;

@Injectable()
export class VehiclesService {
  constructor(@InjectDataSource() private readonly db: DataSource) {}

  list(orgId: string) {
    return this.db.query(
      `${SELECT} WHERE organization_id = $1 ORDER BY created_at DESC`,
      [orgId],
    );
  }

  nearby(orgId: string, lat: number, lng: number, radius: number) {
    const point = `SRID=4326;POINT(${lng} ${lat})`;
    return this.db.query(
      `SELECT id, organization_id, name, vin, license_plate, type, status,
         json_build_object('lat', ST_Y(current_location::geometry),
                           'lng', ST_X(current_location::geometry)) AS location,
         speed, fuel_level, last_seen_at, created_at, updated_at,
         ST_Distance(current_location, ST_GeogFromText($2)) AS distance_m
       FROM vehicles
       WHERE organization_id = $1 AND current_location IS NOT NULL
         AND ST_DWithin(current_location, ST_GeogFromText($2), $3)
       ORDER BY distance_m ASC`,
      [orgId, point, radius],
    );
  }

  async create(orgId: string, dto: CreateVehicleDto) {
    const loc = dto.location
      ? `SRID=4326;POINT(${dto.location.lng} ${dto.location.lat})`
      : null;
    const rows = await this.db.query(
      `INSERT INTO vehicles
         (id, organization_id, name, vin, license_plate, type, status, current_location)
       VALUES (gen_random_uuid(), $1,$2,$3,$4,$5,$6, CASE WHEN $7::text IS NULL THEN NULL ELSE ST_GeogFromText($7) END)
       RETURNING id`,
      [
        orgId,
        dto.name,
        dto.vin ?? null,
        dto.license_plate ?? null,
        dto.type ?? 'van',
        dto.status ?? 'active',
        loc,
      ],
    );
    return this.get(orgId, rows[0].id);
  }

  async get(orgId: string, id: string) {
    const rows = await this.db.query(
      `${SELECT} WHERE id = $1 AND organization_id = $2`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Vehicle not found');
    return rows[0];
  }

  async update(orgId: string, id: string, dto: UpdateVehicleDto) {
    await this.get(orgId, id); // 404 if missing
    const sets: string[] = [];
    const params: unknown[] = [];
    const push = (frag: string, val: unknown) => {
      params.push(val);
      sets.push(`${frag} = $${params.length}`);
    };
    if (dto.name !== undefined) push('name', dto.name);
    if (dto.vin !== undefined) push('vin', dto.vin);
    if (dto.license_plate !== undefined) push('license_plate', dto.license_plate);
    if (dto.type !== undefined) push('type', dto.type);
    if (dto.status !== undefined) push('status', dto.status);
    if (dto.location !== undefined) {
      const loc = dto.location
        ? `SRID=4326;POINT(${dto.location.lng} ${dto.location.lat})`
        : null;
      params.push(loc);
      sets.push(
        `current_location = CASE WHEN $${params.length}::text IS NULL THEN NULL ELSE ST_GeogFromText($${params.length}) END`,
      );
    }
    if (sets.length > 0) {
      params.push(id, orgId);
      await this.db.query(
        `UPDATE vehicles SET ${sets.join(', ')}, updated_at = now()
         WHERE id = $${params.length - 1} AND organization_id = $${params.length}`,
        params,
      );
    }
    return this.get(orgId, id);
  }

  async remove(orgId: string, id: string) {
    const rows = await this.db.query(
      `DELETE FROM vehicles WHERE id = $1 AND organization_id = $2 RETURNING id`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Vehicle not found');
  }
}
