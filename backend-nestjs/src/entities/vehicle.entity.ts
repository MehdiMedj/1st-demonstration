import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';
import { VehicleStatus, VehicleType } from './enums';

@Entity('vehicles')
export class Vehicle {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column({ name: 'organization_id', type: 'uuid' })
  organizationId: string;

  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'varchar', length: 64, nullable: true, unique: true })
  vin: string | null;

  @Column({ name: 'license_plate', type: 'varchar', length: 32, nullable: true })
  licensePlate: string | null;

  @Column({ type: 'enum', enum: VehicleType, enumName: 'vehicle_type', default: VehicleType.van })
  type: VehicleType;

  @Index()
  @Column({ type: 'enum', enum: VehicleStatus, enumName: 'vehicle_status', default: VehicleStatus.active })
  status: VehicleStatus;

  // Geography(Point,4326). Managed via raw ST_* expressions in the service, so
  // TypeORM never reads/writes the raw WKB directly.
  @Column({
    name: 'current_location',
    type: 'geography',
    spatialFeatureType: 'Point',
    srid: 4326,
    nullable: true,
    select: false,
    insert: false,
    update: false,
  })
  currentLocation?: unknown;

  @Column({ type: 'double precision', nullable: true })
  speed: number | null;

  @Column({ name: 'fuel_level', type: 'double precision', nullable: true })
  fuelLevel: number | null;

  @Column({ name: 'last_seen_at', type: 'timestamptz', nullable: true })
  lastSeenAt: Date | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;
}
