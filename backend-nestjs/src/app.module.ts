import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { dataSourceOptions } from './database/data-source';
import { RedisModule } from './redis/redis.module';
import { VehiclesModule } from './vehicles/vehicles.module';
import { DriversModule } from './drivers/drivers.module';
import { PlacesModule } from './places/places.module';
import { OrdersModule } from './orders/orders.module';
import { TelemetryModule } from './telemetry/telemetry.module';
import { RealtimeModule } from './realtime/realtime.module';

@Module({
  imports: [
    TypeOrmModule.forRoot(dataSourceOptions),
    RedisModule,
    VehiclesModule,
    DriversModule,
    PlacesModule,
    OrdersModule,
    TelemetryModule,
    RealtimeModule,
  ],
  controllers: [AppController],
})
export class AppModule {}
