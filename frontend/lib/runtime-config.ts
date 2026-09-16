/**
 * Runtime configuration resolver.
 *
 * `NEXT_PUBLIC_*` values are inlined at build time, which is awkward on managed
 * hosts where the backend URL isn't known until deploy. So the server injects
 * `window.__FLEETOS__` per-request (see app/layout.tsx) and the client reads it
 * here, falling back to build-time env and finally localhost for dev.
 */
export interface RuntimeConfig {
  apiBase: string;
  wsUrl: string;
  orgId: string;
}

function fromWindow(): Partial<RuntimeConfig> {
  if (typeof window === "undefined") return {};
  return (window as unknown as { __FLEETOS__?: Partial<RuntimeConfig> }).__FLEETOS__ ?? {};
}

export function getApiBase(): string {
  return (
    fromWindow().apiBase ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000"
  );
}

export function getWsUrl(): string {
  return (
    fromWindow().wsUrl ||
    process.env.NEXT_PUBLIC_WS_URL ||
    "ws://localhost:8000/api/v1/ws/telemetry"
  );
}

export function getOrgId(): string {
  return (
    fromWindow().orgId ||
    process.env.NEXT_PUBLIC_ORG_ID ||
    "00000000-0000-0000-0000-000000000001"
  );
}
