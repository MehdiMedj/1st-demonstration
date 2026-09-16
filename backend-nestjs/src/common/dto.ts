import { Type } from 'class-transformer';
import {
  IsArray,
  IsEnum,
  IsNumber,
  IsOptional,
  IsString,
  IsUUID,
  Max,
  MaxLength,
  Min,
  ValidateNested,
} from 'class-validator';
import {
  DriverStatus,
  OrderStatus,
  VehicleStatus,
  VehicleType,
} from '../entities/enums';

export class LatLngDto {
  @IsNumber() @Min(-90) @Max(90) lat: number;
  @IsNumber() @Min(-180) @Max(180) lng: number;
}

export class GeoJSONPolygonDto {
  @IsOptional() @IsString() type?: string;
  @IsArray() coordinates: number[][][];
}

// ─── Vehicles ───
export class CreateVehicleDto {
  @IsString() @MaxLength(255) name: string;
  @IsOptional() @IsString() @MaxLength(64) vin?: string;
  @IsOptional() @IsString() @MaxLength(32) license_plate?: string;
  @IsOptional() @IsEnum(VehicleType) type?: VehicleType;
  @IsOptional() @IsEnum(VehicleStatus) status?: VehicleStatus;
  @IsOptional() @ValidateNested() @Type(() => LatLngDto) location?: LatLngDto;
}

export class UpdateVehicleDto {
  @IsOptional() @IsString() @MaxLength(255) name?: string;
  @IsOptional() @IsString() @MaxLength(64) vin?: string;
  @IsOptional() @IsString() @MaxLength(32) license_plate?: string;
  @IsOptional() @IsEnum(VehicleType) type?: VehicleType;
  @IsOptional() @IsEnum(VehicleStatus) status?: VehicleStatus;
  @IsOptional() @ValidateNested() @Type(() => LatLngDto) location?: LatLngDto;
}

// ─── Drivers ───
export class CreateDriverDto {
  @IsString() @MaxLength(255) name: string;
  @IsOptional() @IsString() @MaxLength(32) phone?: string;
  @IsOptional() @IsEnum(DriverStatus) status?: DriverStatus;
  @IsOptional() @IsUUID() vehicle_id?: string;
}

export class UpdateDriverDto {
  @IsOptional() @IsString() @MaxLength(255) name?: string;
  @IsOptional() @IsString() @MaxLength(32) phone?: string;
  @IsOptional() @IsEnum(DriverStatus) status?: DriverStatus;
  @IsOptional() @IsUUID() vehicle_id?: string;
}

// ─── Places ───
export class CreatePlaceDto {
  @IsString() @MaxLength(255) name: string;
  @IsOptional() @IsString() address?: string;
  @IsOptional() @ValidateNested() @Type(() => LatLngDto) location?: LatLngDto;
  @IsOptional() @ValidateNested() @Type(() => GeoJSONPolygonDto)
  polygon_boundary?: GeoJSONPolygonDto;
}

export class UpdatePlaceDto extends CreatePlaceDto {
  @IsOptional() @IsString() @MaxLength(255) declare name: string;
}

// ─── Orders ───
export class CreateOrderDto {
  @IsOptional() @IsString() @MaxLength(40) tracking_number?: string;
  @IsOptional() @IsUUID() pickup_place_id?: string;
  @IsOptional() @IsUUID() dropoff_place_id?: string;
  @IsOptional() @IsString() route_polyline?: string;
}

export class UpdateOrderDto {
  @IsOptional() @IsUUID() pickup_place_id?: string;
  @IsOptional() @IsUUID() dropoff_place_id?: string;
  @IsOptional() @IsUUID() driver_id?: string;
  @IsOptional() @IsUUID() vehicle_id?: string;
  @IsOptional() @IsEnum(OrderStatus) status?: OrderStatus;
  @IsOptional() @IsString() route_polyline?: string;
}

export class AssignOrderDto {
  @IsUUID() order_id: string;
  @IsUUID() driver_id: string;
  @IsUUID() vehicle_id: string;
}

// ─── Telemetry ───
export class TelemetryInDto {
  @IsUUID() vehicle_id: string;
  @IsNumber() @Min(-90) @Max(90) latitude: number;
  @IsNumber() @Min(-180) @Max(180) longitude: number;
  @IsOptional() @IsNumber() @Min(0) speed?: number;
  @IsOptional() @IsNumber() @Min(0) @Max(100) fuel_level?: number;
  @IsOptional() @IsString() timestamp?: string;
}

// ─── Query ───
export class NearbyQueryDto {
  @Type(() => Number) @IsNumber() @Min(-90) @Max(90) lat: number;
  @Type(() => Number) @IsNumber() @Min(-180) @Max(180) lng: number;
  @Type(() => Number) @IsNumber() @Min(1) radius = 5000;
}

export class ContainingQueryDto {
  @Type(() => Number) @IsNumber() @Min(-90) @Max(90) lat: number;
  @Type(() => Number) @IsNumber() @Min(-180) @Max(180) lng: number;
}
