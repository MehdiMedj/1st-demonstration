"use client";

import { useCallback, useEffect, useState } from "react";
import type { Driver, Order, OrderStatus, Vehicle } from "@/lib/types";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface Column {
  key: string;
  title: string;
  statuses: OrderStatus[];
}

const COLUMNS: Column[] = [
  { key: "pending", title: "Pending", statuses: ["pending"] },
  { key: "assigned", title: "Assigned", statuses: ["dispatched"] },
  { key: "en_route", title: "En Route", statuses: ["en_route"] },
  { key: "completed", title: "Completed", statuses: ["completed"] },
];

export default function DispatchBoard() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [o, d, v] = await Promise.all([
      api.listOrders(),
      api.listDrivers(),
      api.listVehicles(),
    ]);
    setOrders(o);
    setDrivers(d);
    setVehicles(v);
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 8000);
    return () => clearInterval(t);
  }, [refresh]);

  const assign = async (order: Order) => {
    const driver = drivers.find((d) => d.status === "available");
    const vehicle = vehicles.find((v) => v.status === "active");
    if (!driver || !vehicle) {
      alert("No available driver/vehicle to assign.");
      return;
    }
    setBusy(order.id);
    try {
      await api.assignOrder(order.id, driver.id, vehicle.id);
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const advance = async (order: Order, status: OrderStatus) => {
    setBusy(order.id);
    try {
      await api.updateOrder(order.id, { status });
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  const driverName = (id: string | null) =>
    drivers.find((d) => d.id === id)?.name ?? "—";

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
      {COLUMNS.map((col) => {
        const items = orders.filter((o) => col.statuses.includes(o.status));
        return (
          <div key={col.key} className="flex flex-col rounded-lg border bg-card/50">
            <div className="flex items-center justify-between border-b px-3 py-2">
              <span className="text-sm font-semibold">{col.title}</span>
              <Badge variant="muted">{items.length}</Badge>
            </div>
            <div className="flex flex-col gap-2 p-2 min-h-[120px]">
              {items.map((o) => (
                <div
                  key={o.id}
                  className="rounded-md border bg-background/60 p-3 text-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{o.tracking_number}</span>
                    <Badge variant="muted">{o.status}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Driver: {driverName(o.driver_id)}
                  </p>

                  <div className="mt-2 flex gap-2">
                    {o.status === "pending" && (
                      <ActionButton
                        disabled={busy === o.id}
                        onClick={() => assign(o)}
                      >
                        Assign
                      </ActionButton>
                    )}
                    {o.status === "dispatched" && (
                      <ActionButton
                        disabled={busy === o.id}
                        onClick={() => advance(o, "en_route")}
                      >
                        Start trip
                      </ActionButton>
                    )}
                    {o.status === "en_route" && (
                      <ActionButton
                        disabled={busy === o.id}
                        onClick={() => advance(o, "completed")}
                      >
                        Complete
                      </ActionButton>
                    )}
                  </div>
                </div>
              ))}
              {items.length === 0 && (
                <p className="px-1 py-6 text-center text-xs text-muted-foreground">
                  No orders
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ActionButton({
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className="rounded-md bg-primary/15 px-2.5 py-1 text-xs font-medium text-primary transition-colors hover:bg-primary/25 disabled:opacity-50"
      {...props}
    >
      {children}
    </button>
  );
}
