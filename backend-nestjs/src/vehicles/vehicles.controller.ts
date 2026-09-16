import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';
import { OrgId } from '../common/org-id.decorator';
import {
  CreateVehicleDto,
  NearbyQueryDto,
  UpdateVehicleDto,
} from '../common/dto';
import { VehiclesService } from './vehicles.service';

@Controller('vehicles')
export class VehiclesController {
  constructor(private readonly svc: VehiclesService) {}

  @Get()
  list(@OrgId() orgId: string) {
    return this.svc.list(orgId);
  }

  @Get('nearby')
  nearby(@OrgId() orgId: string, @Query() q: NearbyQueryDto) {
    return this.svc.nearby(orgId, q.lat, q.lng, q.radius);
  }

  @Post()
  @HttpCode(201)
  create(@OrgId() orgId: string, @Body() dto: CreateVehicleDto) {
    return this.svc.create(orgId, dto);
  }

  @Get(':id')
  get(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.get(orgId, id);
  }

  @Patch(':id')
  update(
    @OrgId() orgId: string,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateVehicleDto,
  ) {
    return this.svc.update(orgId, id, dto);
  }

  @Delete(':id')
  @HttpCode(204)
  remove(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.remove(orgId, id);
  }
}
