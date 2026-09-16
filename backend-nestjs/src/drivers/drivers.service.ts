import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { CreateDriverDto, UpdateDriverDto } from '../common/dto';

const COLS =
  'id, organization_id, vehicle_id, name, phone, status, created_at, updated_at';

@Injectable()
export class DriversService {
  constructor(@InjectDataSource() private readonly db: DataSource) {}

  list(orgId: string) {
    return this.db.query(
      `SELECT ${COLS} FROM drivers WHERE organization_id = $1 ORDER BY created_at DESC`,
      [orgId],
    );
  }

  async create(orgId: string, dto: CreateDriverDto) {
    const rows = await this.db.query(
      `INSERT INTO drivers (id, organization_id, name, phone, status, vehicle_id)
       VALUES (gen_random_uuid(), $1,$2,$3,$4,$5) RETURNING ${COLS}`,
      [orgId, dto.name, dto.phone ?? null, dto.status ?? 'available', dto.vehicle_id ?? null],
    );
    return rows[0];
  }

  async get(orgId: string, id: string) {
    const rows = await this.db.query(
      `SELECT ${COLS} FROM drivers WHERE id = $1 AND organization_id = $2`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Driver not found');
    return rows[0];
  }

  async update(orgId: string, id: string, dto: UpdateDriverDto) {
    await this.get(orgId, id);
    const sets: string[] = [];
    const params: unknown[] = [];
    const push = (col: string, val: unknown) => {
      params.push(val);
      sets.push(`${col} = $${params.length}`);
    };
    if (dto.name !== undefined) push('name', dto.name);
    if (dto.phone !== undefined) push('phone', dto.phone);
    if (dto.status !== undefined) push('status', dto.status);
    if (dto.vehicle_id !== undefined) push('vehicle_id', dto.vehicle_id);
    if (sets.length > 0) {
      params.push(id, orgId);
      await this.db.query(
        `UPDATE drivers SET ${sets.join(', ')}, updated_at = now()
         WHERE id = $${params.length - 1} AND organization_id = $${params.length}`,
        params,
      );
    }
    return this.get(orgId, id);
  }

  async remove(orgId: string, id: string) {
    const rows = await this.db.query(
      `DELETE FROM drivers WHERE id = $1 AND organization_id = $2 RETURNING id`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Driver not found');
  }
}
