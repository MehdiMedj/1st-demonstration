import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FleetOS — Dispatcher",
  description: "Fleet Management & Logistics Operating System",
};

// Read config at request time so the deployed backend URL can be provided via
// runtime env (API_BASE_URL / API_HOST) instead of being baked at build time.
export const dynamic = "force-dynamic";

function runtimeConfig() {
  const host = process.env.API_HOST; // e.g. Render "host" of the backend service
  const apiBase =
    process.env.API_BASE_URL ||
    (host ? `https://${host}` : "") ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "";
  const wsUrl =
    process.env.WS_URL ||
    (host ? `wss://${host}/api/v1/ws/telemetry` : "") ||
    process.env.NEXT_PUBLIC_WS_URL ||
    "";
  const orgId =
    process.env.ORG_ID ||
    process.env.NEXT_PUBLIC_ORG_ID ||
    "00000000-0000-0000-0000-000000000001";
  return { apiBase, wsUrl, orgId };
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cfg = runtimeConfig();
  return (
    <html lang="en" className="dark">
      <head>
        <script
          // Expose runtime config to the client before hydration.
          dangerouslySetInnerHTML={{
            __html: `window.__FLEETOS__=${JSON.stringify(cfg)}`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
