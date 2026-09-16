"use client";

import { useEffect, useRef, useState } from "react";
import type { TelemetryEvent, Vehicle } from "./types";
import { api } from "./api";
import { getWsUrl } from "./runtime-config";

type VehicleMap = Record<string, Vehicle>;

/**
 * Loads the initial fleet snapshot, then keeps positions live by consuming the
 * telemetry WebSocket. Auto-reconnects with backoff.
 */
export function useVehicleSocket() {
  const [vehicles, setVehicles] = useState<VehicleMap>({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  // Initial snapshot from REST.
  useEffect(() => {
    let cancelled = false;
    api.listVehicles().then((list) => {
      if (cancelled) return;
      setVehicles(Object.fromEntries(list.map((v) => [v.id, v])));
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Live updates from WebSocket.
  useEffect(() => {
    let closedByUs = false;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      const url = `${getWsUrl()}?org_id=${encodeURIComponent(api.orgId)}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryRef.current = 0;
      };

      ws.onmessage = (evt) => {
        const e: TelemetryEvent = JSON.parse(evt.data);
        setVehicles((prev) => {
          const existing = prev[e.vehicle_id];
          return {
            ...prev,
            [e.vehicle_id]: {
              ...(existing ?? ({} as Vehicle)),
              id: e.vehicle_id,
              organization_id: e.organization_id,
              name: existing?.name ?? e.vehicle_id.slice(0, 6),
              status: e.status,
              location: { lat: e.latitude, lng: e.longitude },
              speed: e.speed,
              fuel_level: e.fuel_level,
              last_seen_at: e.timestamp,
            } as Vehicle,
          };
        });
      };

      ws.onclose = () => {
        setConnected(false);
        if (closedByUs) return;
        const delay = Math.min(1000 * 2 ** retryRef.current, 15000);
        retryRef.current += 1;
        reconnectTimer = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      closedByUs = true;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  return { vehicles: Object.values(vehicles), connected };
}
