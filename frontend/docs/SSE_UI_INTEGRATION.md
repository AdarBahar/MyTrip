# UI SSE Integration Guide

This guide explains how to integrate the Live Location Server‑Sent Events (SSE) endpoint into the UI.

- Backend SSE endpoint: `/location/live/sse`
- Frontend same‑origin proxy: `/api/location/live/sse` (recommended for browsers)
- Protocol: text/event-stream (SSE)
- Event type: `point` with JSON payload per location record
- Keep‑alives: periodic comment lines starting with `:`

## Why a proxy route?
Browsers’ `EventSource` cannot set custom headers (like `X-API-Token`). The Next.js proxy route forwards the stream to the backend and attaches the server-side API token. Use the proxy route from UI code.

- Proxy source: `frontend/app/api/location/live/sse/route.ts`
- Token resolution in proxy: `LOC_API_TOKEN` (preferred, server-only) or `NEXT_PUBLIC_LOC_API_TOKEN` (fallback)

## Requirements
- You must pass at least one filter or `all=true`:
  - `user`, `users`, `users[]` (usernames)
  - `device`, `devices`, `devices[]` (device IDs)
  - or `all=true` to include all
- Optional resume cursor: `since=<ms>` or rely on `Last-Event-ID` (EventSource auto-sends it on reconnect)
- Optional: `heartbeat=<seconds>` (default 15), `limit=<1-500>` per fetch cycle

## Query parameters
- `user`: string, single username (comma-separated also supported)
- `users`: repeatable, e.g. `?users=adar&users=ben`
- `users[]`: bracket array form, e.g. `?users[]=adar&users[]=ben`
- `device`: string, single device ID (comma-separated also supported)
- `devices`: repeatable, e.g. `?devices=dev1&devices=dev2`
- `devices[]`: bracket array form
- `all`: boolean, include all users/devices (disables other filters)
- `since`: number (ms since epoch) initial cursor; if omitted, server uses `Last-Event-ID`
- `limit`: number (1–500) max points per cycle (default 100)
- `heartbeat`: seconds between keep‑alive comments (default 15)
- `session_id`: optional, echoed in initial meta comment (not required)

## Event schema
Each `point` event carries JSON data similar to:

```json
{
  "device_id": "dev-123",
  "user_id": 42,
  "username": "adar",
  "display_name": "Adar Bahar",
  "latitude": 32.0777,
  "longitude": 34.7733,
  "accuracy": 6.0,
  "altitude": 20.5,
  "speed": 1.2,
  "bearing": 270,
  "battery_level": 0.78,
  "recorded_at": "2024-10-01T12:34:56Z",
  "server_time": "2024-10-01T12:34:57.001Z",
  "server_timestamp": 1727786097001
}
```

Notes:
- Each event also has an SSE `id` equal to `server_timestamp` for resume.
- Keep‑alive comments look like `: keep-alive <ms>`; they are not delivered to `onmessage` and do not have data.

## Quick start (minimal UI)
Use the proxy route from the UI so the token is added server-side:

```ts
const params = new URLSearchParams({ all: "true", heartbeat: "10", limit: "100" });
const es = new EventSource(`/api/location/live/sse?${params.toString()}`);

es.addEventListener("point", (ev) => {
  const point = JSON.parse(ev.data as string);
  console.log("point", point.username, point.latitude, point.longitude, point.server_timestamp);
});

es.onerror = () => {
  // EventSource auto-reconnects; you can update UI state here
};

// Later, to close:
// es.close();
```

## Recommended React hook
A small hook that manages connection, cleanup, and exposes points and state.

```ts
import { useEffect, useRef, useState } from "react";

export type LivePoint = {
  device_id: string;
  user_id: number | null;
  username: string | null;
  display_name: string | null;
  latitude: number | null;
  longitude: number | null;
  accuracy?: number | null;
  altitude?: number | null;
  speed?: number | null;
  bearing?: number | null;
  battery_level?: number | null;
  recorded_at?: string | null;
  server_time?: string | null;
  server_timestamp: number;
};

export function useLiveLocations(params: {
  all?: boolean;
  users?: string[];
  devices?: string[];
  since?: number;
  heartbeat?: number;
  limit?: number;
}) {
  const [connected, setConnected] = useState(false);
  const [lastEventId, setLastEventId] = useState<string | null>(null);
  const [points, setPoints] = useState<LivePoint[]>([]);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const qs = new URLSearchParams();
    if (params.all) qs.set("all", "true");
    (params.users || []).forEach((u) => qs.append("users", u));
    (params.devices || []).forEach((d) => qs.append("devices", d));
    if (params.since != null) qs.set("since", String(params.since));
    if (params.heartbeat) qs.set("heartbeat", String(params.heartbeat));
    if (params.limit) qs.set("limit", String(params.limit));

    const es = new EventSource(`/api/location/live/sse?${qs.toString()}`);
    esRef.current = es;

    const onOpen = () => setConnected(true);
    const onError = () => setConnected(false);
    const onPoint = (ev: MessageEvent) => {
      if ((ev as any).lastEventId) setLastEventId((ev as any).lastEventId);
      try {
        const p = JSON.parse(ev.data as string) as LivePoint;
        setPoints((prev) => [...prev, p]);
      } catch (_) {
        // ignore parse errors
      }
    };

    es.addEventListener("open", onOpen);
    es.addEventListener("point", onPoint as any);
    es.addEventListener("error", onError as any);

    es.onerror = onError;

    return () => {
      es.removeEventListener("open", onOpen as any);
      es.removeEventListener("point", onPoint as any);
      es.removeEventListener("error", onError as any);
      es.close();
      esRef.current = null;
    };
  }, [JSON.stringify(params)]);

  return { connected, lastEventId, points };
}
```

Usage:

```tsx
const { connected, points } = useLiveLocations({ all: true, heartbeat: 5, limit: 100 });
```

## Resuming and deduping
- Automatic: `EventSource` sends `Last-Event-ID` on reconnect. Server uses it as the starting cursor.
- Manual: you can set `since=<ms>` to start from a specific time.
- Deduping: if you persist `lastEventId` in your state/store and include `since=lastEventId` on new mounts, you avoid missing records across page reloads.

## Configuration (env vars)
- Set `LOC_API_TOKEN` in the frontend environment for the proxy route to attach to backend requests. Prefer server-only env (do not expose secrets client-side).
- The proxy also supports `NEXT_PUBLIC_LOC_API_TOKEN` as a fallback, but avoid this in production if possible.

Example `.env.local` (Next.js):

```dotenv
# Server-side token used by the proxy route
LOC_API_TOKEN=your-backend-api-token

# Backend base is resolved by your existing getApiBaseSync()
# Optionally ensure NEXT_PUBLIC_API_BASE or similar is configured if your proxy uses it.
```

## Testing locally
- Visit the included test page: `/test/live-sse` (if present in your build) which uses the same proxy.
- Or, connect from your own page with `all=true&heartbeat=1&limit=1` to quickly verify keep-alives.

## Troubleshooting
- 400/422 error immediately: you must pass a filter (`user/users/devices`) or `all=true`.
- No events but connection stays open: keep‑alives are comments; listen for `point` events or set `heartbeat=1` temporarily to see quick activity.
- CORS issues: use the same-origin proxy (`/api/location/live/sse`). If connecting cross-origin directly to the backend, you cannot set headers from `EventSource`.
- Nginx buffering: the backend and proxy set `X-Accel-Buffering: no`. Ensure your reverse proxy honors it.

## Reference
- Backend implementation: `backend/app/api/location/router.py` (`/location/live/sse` via `StreamingResponse`)
- Frontend proxy implementation: `frontend/app/api/location/live/sse/route.ts`
- Example test page: `frontend/app/test/live-sse/page.tsx`

## Security notes
- Do not put tokens in client JavaScript. Keep tokens server-side and inject via the proxy.
- Use `LOC_API_TOKEN` on the server for production.

## FAQ
- Can I pass custom headers from `EventSource`? No. Use the same-origin proxy.
- How do I resume after a page reload? Use `Last-Event-ID` (automatic) or persist the last seen `server_timestamp` and use `since`.
- Does the server send `retry:` directives? Not currently; default `EventSource` backoff is sufficient in most cases.
