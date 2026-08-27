# FloodSafe Nepal — Scale Gateway

This folder is the production-scale data delivery layer for FloodSafe Nepal.

## Why it exists

The public UI may refresh every few seconds, but millions of browsers must never poll BIPAD/DHM/DoR directly. The gateway centralizes official-source reads, stores a last-known snapshot, and serves cached responses from the edge.

## Production flow

1. Scheduled ingestion refreshes the official Nepal snapshot once per minute.
2. The snapshot is stored in `SNAPSHOT_KV` for last-known-good fallback.
3. `/api/live` is cached at the edge for 15 seconds with stale-while-revalidate.
4. User devices read the gateway instead of government APIs.
5. If refresh fails, the last known snapshot is returned as stale/unverified rather than falsely reporting a safe condition.

## Endpoints

- `GET /api/live`
- `GET /api/v1/live`
- `GET /api/v1/feed/rivers`
- `GET /api/v1/feed/riverStations`
- `GET /api/v1/feed/rain`
- `GET /api/v1/feed/alerts`
- `GET /api/v1/feed/roads`
- `GET /api/v1/feed/weather`
- `GET /api/v1/feed/incidents`
- `GET /api/v1/feed/losses`
- `GET /api/v1/feed/bulletins`
- `GET /api/v1/feed/affected`
- `GET /health`

## Deployment requirements

Create two KV namespaces (production and preview), replace the placeholder IDs in `wrangler.jsonc`, then deploy the Worker. The cron trigger is already configured for every minute.

After deployment, wire the public V24/V25 client to the gateway endpoint and disable direct browser polling of BIPAD/DHM/DoR.

## Safety rules

- Never convert missing data into a green/safe status.
- Show `generated_at` and stale state to the user.
- Keep official source attribution visible.
- Preserve the last known valid snapshot during upstream outages.
- Do not claim 10M simultaneous-user capacity until load tests and provider quotas have been validated.
