import { Body, Controller, HttpCode, Post } from '@nestjs/common';
import { OrgId } from '../common/org-id.decorator';
import { TelemetryInDto } from '../common/dto';
import { TelemetryService } from './telemetry.service';

@Controller('telemetry')
export class TelemetryController {
  constructor(private readonly svc: TelemetryService) {}

  @Post()
  @HttpCode(202)
  ingest(@OrgId() orgId: string, @Body() dto: TelemetryInDto) {
    return this.svc.ingest(orgId, dto);
  }
}
