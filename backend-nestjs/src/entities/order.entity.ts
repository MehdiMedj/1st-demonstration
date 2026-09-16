import {
  Column,
  CreateDateColumn,
  Entity,
  Index,
  PrimaryGeneratedColumn,
  UpdateDateColumn,
} from 'typeorm';
import { OrderStatus } from './enums';

@Entity('orders')
export class Order {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Index()
  @Column({ name: 'organization_id', type: 'uuid' })
  organizationId: string;

  @Column({ name: 'tracking_number', type: 'varchar', length: 40, unique: true })
  trackingNumber: string;

  @Column({ name: 'pickup_place_id', type: 'uuid', nullable: true })
  pickupPlaceId: string | null;

  @Column({ name: 'dropoff_place_id', type: 'uuid', nullable: true })
  dropoffPlaceId: string | null;

  @Column({ name: 'driver_id', type: 'uuid', nullable: true })
  driverId: string | null;

  @Column({ name: 'vehicle_id', type: 'uuid', nullable: true })
  vehicleId: string | null;

  @Index()
  @Column({ type: 'enum', enum: OrderStatus, enumName: 'order_status', default: OrderStatus.pending })
  status: OrderStatus;

  @Column({ name: 'route_polyline', type: 'text', nullable: true })
  routePolyline: string | null;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;
}
