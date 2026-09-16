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
import {
  AssignOrderDto,
  CreateOrderDto,
  UpdateOrderDto,
} from '../common/dto';
import { OrdersService } from './orders.service';

@Controller('orders')
export class OrdersController {
  constructor(private readonly svc: OrdersService) {}

  @Get()
  list(@OrgId() orgId: string) {
    return this.svc.list(orgId);
  }

  @Post()
  @HttpCode(201)
  create(@OrgId() orgId: string, @Body() dto: CreateOrderDto) {
    return this.svc.create(orgId, dto);
  }

  // Declared before ':id' so "assign" is not captured as an id param.
  @Post('assign')
  assign(@OrgId() orgId: string, @Body() dto: AssignOrderDto) {
    return this.svc.assign(orgId, dto.order_id, dto.driver_id, dto.vehicle_id);
  }

  @Get(':id')
  get(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.get(orgId, id);
  }

  @Patch(':id')
  update(
    @OrgId() orgId: string,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateOrderDto,
  ) {
    return this.svc.update(orgId, id, dto);
  }

  @Delete(':id')
  @HttpCode(204)
  remove(@OrgId() orgId: string, @Param('id', ParseUUIDPipe) id: string) {
    return this.svc.remove(orgId, id);
  }
}
