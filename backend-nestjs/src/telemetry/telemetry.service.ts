import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource } from '@nestjs/typeorm';
import { DataSource } from 'typeorm';
import { RedisService } from '../redis/redis.service';
import { TelemetryInDto } from '../common/dto';

@Injectable()
export class TelemetryService {
  constructor(
    @InjectDataSource() private readonly db: DataSource,
    private readonly redis: RedisService,
  ) {}

  async ingest(orgId: string, dto: TelemetryInDto) {
    const vehicle = (
      await this.db.query(
        `SELECT id, status FROM vehicles WHERE id = $1 AND organization_id = $2`,
        [dto.vehicle_id, orgId],
      )
    )[0];
    if (!vehicle) throw new NotFoundException('Vehicle not found');

    const ts = dto.timestamp ? new Date(dto.timestamp) : new Date();
    const point = `SRID=4326;POINT(${dto.longitude} ${dto.latitude})`;

    await this.db.transaction(async (m) => {
      await m.query(
        `INSERT INTO telemetry_pings (id, vehicle_id, location, speed, fuel_level, recorded_at)
         VALUES (gen_random_uuid(), $1, ST_GeogFromText($2), $3, $4, $5)`,
        [vehicle.id, point, dto.speed ?? null, dto.fuel_level ?? null, ts],
      );
      await m.query(
        `UPDATE vehicles
           SET current_location = ST_GeogFromText($1), speed = $2, fuel_level = $3,
               last_seen_at = $4, updated_at = now()
         WHERE id = $5`,
        [point, dto.speed ?? null, dto.fuel_level ?? null, ts, vehicle.id],
      );
    });

    const event = {
      type: 'vehicle.telemetry',
      vehicle_id: vehicle.id,
      organization_id: orgId,
      latitude: dto.latitude,
      longitude: dto.longitude,
      speed: dto.speed ?? null,
      fuel_level: dto.fuel_level ?? null,
      status: vehicle.status,
      timestamp: ts.toISOString(),
    };
    await this.redis.publish(JSON.stringify(event));
    return event;
  }
}
