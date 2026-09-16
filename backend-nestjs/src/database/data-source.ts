import 'reflect-metadata';
import { DataSource, DataSourceOptions } from 'typeorm';
import { config } from '../config/configuration';
import { Organization } from '../entities/organization.entity';
import { Vehicle } from '../entities/vehicle.entity';
import { Driver } from '../entities/driver.entity';
import { Place } from '../entities/place.entity';
import { Order } from '../entities/order.entity';
import { TelemetryPing } from '../entities/telemetry-ping.entity';
import { InitSchema1700000000000 } from './migrations/1700000000000-InitSchema';

const c = config();

export const entities = [Organization, Vehicle, Driver, Place, Order, TelemetryPing];

export const dataSourceOptions: DataSourceOptions = {
  type: 'postgres',
  host: c.db.host,
  port: c.db.port,
  username: c.db.username,
  password: c.db.password,
  database: c.db.database,
  entities,
  migrations: [InitSchema1700000000000],
  synchronize: false,
  logging: false,
};

export const AppDataSource = new DataSource(dataSourceOptions);
