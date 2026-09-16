export type VehicleStatus = "active" | "maintenance" | "en_route";
export type DriverStatus = "available" | "on_trip" | "off_duty";
export type OrderStatus =
  | "pending"
  | "dispatched"
  | "en_route"
  | "completed"
  | "cancelled";

export interface LatLng {
  lat: number;
  lng: number;
}

export interface Vehicle {
  id: string;
  organization_id: string;
  name: string;
  vin: string | null;
  license_plate: string | null;
  type: string;
  status: VehicleStatus;
  location: LatLng | null;
  speed: number | null;
  fuel_level: number | null;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Driver {
  id: string;
  name: string;
  phone: string | null;
  status: DriverStatus;
  vehicle_id: string | null;
}

export interface Order {
  id: string;
  tracking_number: string;
  status: OrderStatus;
  driver_id: string | null;
  vehicle_id: string | null;
  pickup_place_id: string | null;
  dropoff_place_id: string | null;
}

/** Frame pushed over the telemetry WebSocket. */
export interface TelemetryEvent {
  type: string;
  vehicle_id: string;
  organization_id: string;
  latitude: number;
  longitude: number;
  speed: number | null;
  fuel_level: number | null;
  status: VehicleStatus;
  timestamp: string;
}
