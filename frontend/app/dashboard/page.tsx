"use client";

import dynamic from "next/dynamic";
import { useVehicleSocket } from "@/lib/useVehicleSocket";
import DispatchBoard from "@/components/DispatchBoard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// maplibre-gl touches `window`, so load the map only on the client.
const FleetMap = dynamic(() => import("@/components/FleetMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Loading map…
    </div>
  ),
});

export default function DashboardPage() {
  const { vehicles, connected } = useVehicleSocket();

  const counts = {
    active: vehicles.filter((v) => v.status === "active").length,
    en_route: vehicles.filter((v) => v.status === "en_route").length,
    maintenance: vehicles.filter((v) => v.status === "maintenance").length,
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-[1500px] flex-col gap-4 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            FleetOS · Dispatcher
          </h1>
          <p className="text-sm text-muted-foreground">
            Live telematics &amp; dispatch board
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="active">{counts.active} active</Badge>
          <Badge variant="en_route">{counts.en_route} en route</Badge>
          <Badge variant="maintenance">{counts.maintenance} maint.</Badge>
          <Badge variant={connected ? "active" : "muted"}>
            {connected ? "● live" : "○ offline"}
          </Badge>
        </div>
      </header>

      <Card className="h-[52vh] overflow-hidden">
        <CardContent className="h-full p-0">
          <FleetMap vehicles={vehicles} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Dispatch board</CardTitle>
        </CardHeader>
        <CardContent>
          <DispatchBoard />
        </CardContent>
      </Card>
    </main>
  );
}
