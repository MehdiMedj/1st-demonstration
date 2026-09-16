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
  ContainingQueryDto,
  CreatePlaceDto,
  UpdatePlaceDto,
} from '../common/dto';
import { PlacesService } from './places.service';

@Controller('places')
export class PlacesController {
  constructor(private readonly svc: PlacesService) {}

  @Get()
  list(@OrgId() orgId: string) {
    return this.svc.list(orgId);
  }

  @Get('containing')
  containing(@OrgId() orgId: string, @Query() q: ContainingQueryDto) {
    return this.svc.containing(orgId, q.lat, q.lng);
  }

  @Post()
  @HttpCode(201)
  create(@OrgId() orgId: string, @Body() dto: CreatePlaceDto) {
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
    @Body() dto: UpdatePlaceDto,
  ) {
    return this.svc.update(orgId, id, dto);
  }

  @Delete(':id')
  @HttpCode(204)
  remove(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.remove(orgId, id);
  }
}
