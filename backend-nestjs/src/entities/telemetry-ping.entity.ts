import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
} from 'typeorm';

@Entity('telemetry_pings')
export class TelemetryPing {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column({ name: 'vehicle_id', type: 'uuid' })
  vehicleId: string;

  @Column({
    name: 'location',
    type: 'geography',
    spatialFeatureType: 'Point',
    srid: 4326,
    select: false,
    insert: false,
    update: false,
  })
  location?: unknown;

  @Column({ type: 'double precision', nullable: true })
  speed: number | null;

  @Column({ name: 'fuel_level', type: 'double precision', nullable: true })
  fuelLevel: number | null;

  @Index()
  @Column({ name: 'recorded_at', type: 'timestamptz' })
  recordedAt: Date;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;
}
