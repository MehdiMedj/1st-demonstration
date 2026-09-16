export enum VehicleStatus {
  active = 'active',
  maintenance = 'maintenance',
  en_route = 'en_route',
}

export enum VehicleType {
  van = 'van',
  truck = 'truck',
  car = 'car',
  motorcycle = 'motorcycle',
  other = 'other',
}

export enum DriverStatus {
  available = 'available',
  on_trip = 'on_trip',
  off_duty = 'off_duty',
}

export enum OrderStatus {
  pending = 'pending',
  dispatched = 'dispatched',
  en_route = 'en_route',
  completed = 'completed',
  cancelled = 'cancelled',
}
