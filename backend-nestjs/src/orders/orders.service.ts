import {
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { randomBytes } from 'crypto';
import { DataSource } from 'typeorm';
import { CreateOrderDto, UpdateOrderDto } from '../common/dto';

const COLS = `id, organization_id, tracking_number, pickup_place_id, dropoff_place_id,
  driver_id, vehicle_id, status, route_polyline, created_at, updated_at`;

function trackingNumber(): string {
  return `FLT-${randomBytes(4).toString('hex').toUpperCase()}`;
}

@Injectable()
export class OrdersService {
  constructor(@InjectDataSource() private readonly db: DataSource) {}

  list(orgId: string) {
    return this.db.query(
      `SELECT ${COLS} FROM orders WHERE organization_id = $1 ORDER BY created_at DESC`,
      [orgId],
    );
  }

  async create(orgId: string, dto: CreateOrderDto) {
    const rows = await this.db.query(
      `INSERT INTO orders
         (id, organization_id, tracking_number, pickup_place_id, dropoff_place_id, route_polyline)
       VALUES (gen_random_uuid(), $1,$2,$3,$4,$5) RETURNING ${COLS}`,
      [
        orgId,
        dto.tracking_number ?? trackingNumber(),
        dto.pickup_place_id ?? null,
        dto.dropoff_place_id ?? null,
        dto.route_polyline ?? null,
      ],
    );
    return rows[0];
  }

  async get(orgId: string, id: string) {
    const rows = await this.db.query(
      `SELECT ${COLS} FROM orders WHERE id = $1 AND organization_id = $2`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Order not found');
    return rows[0];
  }

  async update(orgId: string, id: string, dto: UpdateOrderDto) {
    await this.get(orgId, id);
    const sets: string[] = [];
    const params: unknown[] = [];
    const push = (col: string, val: unknown) => {
      params.push(val);
      sets.push(`${col} = $${params.length}`);
    };
    if (dto.pickup_place_id !== undefined) push('pickup_place_id', dto.pickup_place_id);
    if (dto.dropoff_place_id !== undefined) push('dropoff_place_id', dto.dropoff_place_id);
    if (dto.driver_id !== undefined) push('driver_id', dto.driver_id);
    if (dto.vehicle_id !== undefined) push('vehicle_id', dto.vehicle_id);
    if (dto.status !== undefined) push('status', dto.status);
    if (dto.route_polyline !== undefined) push('route_polyline', dto.route_polyline);
    if (sets.length > 0) {
      params.push(id, orgId);
      await this.db.query(
        `UPDATE orders SET ${sets.join(', ')}, updated_at = now()
         WHERE id = $${params.length - 1} AND organization_id = $${params.length}`,
        params,
      );
    }
    return this.get(orgId, id);
  }

  async remove(orgId: string, id: string) {
    const rows = await this.db.query(
      `DELETE FROM orders WHERE id = $1 AND organization_id = $2 RETURNING id`,
      [id, orgId],
    );
    if (rows.length === 0) throw new NotFoundException('Order not found');
  }

  /** Assign driver+vehicle to an order and recompute all statuses atomically. */
  async assign(orgId: string, orderId: string, driverId: string, vehicleId: string) {
    return this.db.transaction(async (m) => {
      const one = async (table: string, id: string, label: string) => {
        const rows = await m.query(
          `SELECT * FROM ${table} WHERE id = $1 AND organization_id = $2 FOR UPDATE`,
          [id, orgId],
        );
        if (rows.length === 0) throw new NotFoundException(`${label} not found`);
        return rows[0];
      };
      const order = await one('orders', orderId, 'Order');
      const driver = await one('drivers', driverId, 'Driver');
      const vehicle = await one('vehicles', vehicleId, 'Vehicle');

      if (order.status === 'completed' || order.status === 'cancelled') {
        throw new ConflictException(`Order is ${order.status} and cannot be reassigned`);
      }
      if (driver.status === 'on_trip' && order.driver_id !== driver.id) {
        throw new ConflictException('Driver is already on a trip');
      }
      if (vehicle.status === 'maintenance') {
        throw new ConflictException('Vehicle is under maintenance');
      }

      await m.query(
        `UPDATE orders SET driver_id=$1, vehicle_id=$2, status='dispatched', updated_at=now() WHERE id=$3`,
        [driver.id, vehicle.id, order.id],
      );
      await m.query(
        `UPDATE drivers SET status='on_trip', vehicle_id=$1, updated_at=now() WHERE id=$2`,
        [vehicle.id, driver.id],
      );
      await m.query(
        `UPDATE vehicles SET status='en_route', updated_at=now() WHERE id=$1`,
        [vehicle.id],
      );

      const rows = await m.query(`SELECT ${COLS} FROM orders WHERE id = $1`, [order.id]);
      return rows[0];
    });
  }
}
