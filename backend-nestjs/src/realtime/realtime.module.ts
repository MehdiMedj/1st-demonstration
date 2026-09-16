import { Module } from '@nestjs/common';
import { TelemetryGateway } from './telemetry.gateway';

@Module({
  providers: [TelemetryGateway],
})
export class RealtimeModule {}
