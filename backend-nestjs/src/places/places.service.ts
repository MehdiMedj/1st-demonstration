import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import {
  CreatePlaceDto,
  GeoJSONPolygonDto,
  LatLngDto,
  UpdatePlaceDto,
} from '../common/dto';

const SELECT = `
  SELECT id, organization_id, name, address,
    CASE WHEN location IS NULL THEN NULL ELSE
      json_build_object('lat', ST_Y(location::geometry),
                        'lng', ST_X(location::geometry)) END AS location,
    CASE WHEN polygon_boundary IS NULL THEN NULL ELSE
      ST_AsGeoJSON(polygon_boundary)::json END AS polygon_boundary,
    created_at, updated_at
  FROM places`;

function pointEwkt(loc: LatLngDto): string {
  return `SRID=4326;POINT(${loc.lng} ${loc.lat})`;
}

function polygonEwkt(poly: GeoJSONPolygonDto): string {
  const rings = poly.coordinates
    .map((ring) => '(' + ring.map(([lng, lat]) => `${lng} ${lat}`).join(', ') + ')')
    .join(', ');
  return `SRID=4326;POLYGON(${rings})`;
}

@Injectable()
export class PlacesService {
  constructor(@InjectDataSource() private readonly db: DataSource) {}

  list(orgId: string) {
    return this.db.query(
      `${SELECT} WHERE organization_id = $1 ORDER BY created_at DESC`,
      [orgId],
    );
  }

  async create(orgId: string, dto: CreatePlaceDto) {
    const loc = dto.location ? pointEwkt(dto.location) : null;
    const poly = dto.polygon_boundary ? polygonEwkt(dto.polygon_boundary) : null;
    const rows = await this.db.query(
      `INSERT INTO places (id, organization_id, name, address, location, polygon_boundary)
       VALUES (gen_random_uuid(), $1,$2,$3,
         CASE WHEN $4::text IS NULL THEN NULL ELSE ST_GeogFromText($4) END,
         CASE WHEN $5::text IS NULL THEN NULL ELSE ST_GeogFromText($5) END)
       RETURNING id`,
      [orgId, dto.name, dto.address ?? null, loc, poly],
    );
    return this.get(orgId, rows[0].id);
  }

  containing(orgId: string, lat: number, lng: number) {
    return this.db.query(
      `${SELECT}
       WHERE organization_id = $1 AND polygon_boundary IS NOT NULL
         AND ST_Contains(polygon_boundary::geometry,
                         ST_SetSRID(ST_MakePoint($3, $2), 4326))`,
      [orgId, lat, lng],
    );
  }

  async get(orgId: string, id: string) {
    const rows = await this.db.query(
      `${SELECT} WHERE id = $1 AND organization_id = $2`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Place not found');
    return rows[0];
  }

  async update(orgId: string, id: string, dto: UpdatePlaceDto) {
    await this.get(orgId, id);
    const sets: string[] = [];
    const params: unknown[] = [];
    const setScalar = (col: string, val: unknown) => {
      params.push(val);
      sets.push(`${col} = $${params.length}`);
    };
    const setGeog = (col: string, ewkt: string | null) => {
      params.push(ewkt);
      const n = params.length;
      sets.push(`${col} = CASE WHEN $${n}::text IS NULL THEN NULL ELSE ST_GeogFromText($${n}) END`);
    };
    if (dto.name !== undefined) setScalar('name', dto.name);
    if (dto.address !== undefined) setScalar('address', dto.address);
    if (dto.location !== undefined) {
      setGeog('location', dto.location ? pointEwkt(dto.location) : null);
    }
    if (dto.polygon_boundary !== undefined) {
      setGeog('polygon_boundary', dto.polygon_boundary ? polygonEwkt(dto.polygon_boundary) : null);
    }
    if (sets.length > 0) {
      params.push(id, orgId);
      await this.db.query(
        `UPDATE places SET ${sets.join(', ')}, updated_at = now()
         WHERE id = $${params.length - 1} AND organization_id = $${params.length}`,
        params,
      );
    }
    return this.get(orgId, id);
  }

  async remove(orgId: string, id: string) {
    const rows = await this.db.query(
      `DELETE FROM places WHERE id = $1 AND organization_id = $2 RETURNING id`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Place not found');
  }
}
