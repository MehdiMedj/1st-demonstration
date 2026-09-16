import type { Driver, Order, Vehicle } from "./types";
import { getApiBase, getOrgId } from "./runtime-config";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiBase()}/api/v1${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Org-Id": getOrgId(),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status} ${path}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get orgId() {
    return getOrgId();
  },

  listVehicles: () => request<Vehicle[]>("/vehicles"),
  listDrivers: () => request<Driver[]>("/drivers"),
  listOrders: () => request<Order[]>("/orders"),

  assignOrder: (order_id: string, driver_id: string, vehicle_id: string) =>
    request<Order>("/orders/assign", {
      method: "POST",
      body: JSON.stringify({ order_id, driver_id, vehicle_id }),
    }),

  updateOrder: (id: string, patch: Partial<Order>) =>
    request<Order>(`/orders/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  nearby: (lat: number, lng: number, radius = 5000) =>
    request<(Vehicle & { distance_m: number })[]>(
      `/vehicles/nearby?lat=${lat}&lng=${lng}&radius=${radius}`,
    ),

  // Convenience for demos: push a synthetic telemetry ping.
  sendTelemetry: (vehicle_id: string, latitude: number, longitude: number, speed = 0) =>
    request("/telemetry", {
      method: "POST",
      body: JSON.stringify({ vehicle_id, latitude, longitude, speed }),
    }),
};
