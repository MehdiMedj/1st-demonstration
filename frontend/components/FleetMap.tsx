"use client";

import { useEffect, useRef } from "react";
import maplibregl, { Map as MLMap, Marker, Popup } from "maplibre-gl";
import type { Vehicle } from "@/lib/types";

// Keyless raster style (OpenStreetMap tiles) — swap for a MapTiler/Mapbox
// style URL + key in production.
const MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: ["https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors",
    },
  },
  layers: [{ id: "osm", type: "raster", source: "osm" }],
};

const STATUS_COLOR: Record<string, string> = {
  active: "#34d399",
  en_route: "#38bdf8",
  maintenance: "#fbbf24",
};

export default function FleetMap({ vehicles }: { vehicles: Vehicle[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const markersRef = useRef<Record<string, Marker>>({});

  // Init map once.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [-122.4194, 37.7749], // San Francisco
      zoom: 12,
    });
    mapRef.current.addControl(new maplibregl.NavigationControl(), "top-right");
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
      markersRef.current = {};
    };
  }, []);

  // Sync markers with vehicle positions.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    for (const v of vehicles) {
      if (!v.location) continue;
      const color = STATUS_COLOR[v.status] ?? "#94a3b8";
      const lngLat: [number, number] = [v.location.lng, v.location.lat];

      const popupHtml = `
        <div style="font-family:system-ui;font-size:12px;line-height:1.4">
          <strong>${v.name}</strong><br/>
          Status: ${v.status}<br/>
          Speed: ${v.speed?.toFixed?.(0) ?? "–"} km/h<br/>
          Fuel: ${v.fuel_level?.toFixed?.(0) ?? "–"}%
        </div>`;

      const existing = markersRef.current[v.id];
      if (existing) {
        existing.setLngLat(lngLat);
        existing.getElement().style.background = color;
        existing.getPopup()?.setHTML(popupHtml);
      } else {
        const el = document.createElement("div");
        el.style.cssText = `width:16px;height:16px;border-radius:9999px;background:${color};border:2px solid #0b1120;box-shadow:0 0 0 2px ${color}55;cursor:pointer`;
        const marker = new maplibregl.Marker({ element: el })
          .setLngLat(lngLat)
          .setPopup(new Popup({ offset: 14, closeButton: false }).setHTML(popupHtml))
          .addTo(map);
        markersRef.current[v.id] = marker;
      }
    }
  }, [vehicles]);

  return <div ref={containerRef} className="h-full w-full rounded-lg" />;
}
