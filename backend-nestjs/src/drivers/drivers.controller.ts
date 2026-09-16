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
} from '@nestjs/common';
import { OrgId } from '../common/org-id.decorator';
import { CreateDriverDto, UpdateDriverDto } from '../common/dto';
import { DriversService } from './drivers.service';

@Controller('drivers')
export class DriversController {
  constructor(private readonly svc: DriversService) {}

  @Get()
  list(@OrgId() orgId: string) {
    return this.svc.list(orgId);
  }

  @Post()
  @HttpCode(201)
  create(@OrgId() orgId: string, @Body() dto: CreateDriverDto) {
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
    @Body() dto: UpdateDriverDto,
  ) {
    return this.svc.update(orgId, id, dto);
  }

  @Delete(':id')
  @HttpCode(204)
  remove(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.remove(orgId, id);
  }
}
