MyTrip — https://github.com/AdarBahar/MyTrip

Overview
- MyTrip is a production-ready road trip planner with a FastAPI backend and a Next.js 14 frontend.
- Core capabilities: trip days and stops (START/VIA/END), route optimization with GraphHopper, places search (type‑ahead + full search), and live location streaming via SSE.
- This document orients new contributors and links to the most relevant in‑repo docs.

Architecture (high level)
- Backend (Python/FastAPI): backend/app/*
  - Domain models: trips, days, stops, places, users; live location ingestion and stats
  - Notable APIs: location ingestion + queries, SSE streaming, places search (suggest + search), stops management
- Frontend (Next.js/TypeScript): frontend/*
  - App Router, Tailwind, shadcn/ui, TanStack Query; SSE UI integration helpers
- Data: MySQL 8 (primary), optional SQLite for tests; SQLAlchemy + Alembic
- Maps/Routing: MapTiler (maps/geocoding), GraphHopper (routing)

Key backend areas (selected)
- Location module (PHP → FastAPI migration): backend/app/api/location/router.py
  - Legacy‑compatible endpoints: POST /location/api/getloc, POST /location/api/driving, POST /location/api/batch-sync
  - Queries: GET /location/api/locations, GET /location/api/driving-records, GET /location/api/users
  - Stats + caching: GET/POST /location/api/stats (timeframe windows, optional segments)
  - SSE streaming: GET /location/api/live/sse with “now” default when no since/Last-Event-ID
  - Latest point: GET /location/api/live/latest
- Places search (type‑ahead + full): backend/app/api/v1/places/endpoints.py
  - GET /places/v1/places/suggest (requires session_token) — fast autocomplete
  - GET /places/v1/places/search — comprehensive results with filters/sort/pagination
- Stops/Days (trip planning): backend/app/api/stops/*, backend/app/schemas/stop.py
  - START/VIA/END are all “stops” referencing a Place; constraints enforce START seq=1, END fixed

Important docs and references (in repo)
- API overview and references
  - docs/api/reference.md (index) and docs/api/openapi.json (export)
  - docs/api/places-autocomplete.md (autocomplete + full search)
  - docs/api/day-locations.md (adding START/VIA/END to a day)
- Architecture and guides
  - docs/architecture/overview.md
  - docs/guides/routing-profiles.md
- Location/SSE UX
  - frontend/docs/SSE_UI_INTEGRATION.md
- Infrastructure/operational docs
  - docs/SSL_SETUP.md, docs/CORS_FIX.md
  - backend/docs/TESTING_CONFIGURATION.md
  - backend/docs/route_optimization.md; docs/AI_ROUTE_OPTIMIZATION.md
  - docs/COMPLETE_ENDPOINTS_API.md (coverage/status)

Build, run, and tests (summary)
- Local quick start (see README.md for complete details):
  - Backend dev: cd backend && uvicorn app.main:app --reload (API at http://localhost:8000)
  - Frontend dev: cd frontend && pnpm dev (UI at http://localhost:3500)
  - Docker: make up / make down; migrations via make db.migrate
- Tests (safe‑by‑default):
  - cd backend && pytest -q (see backend/docs/TESTING_CONFIGURATION.md)
  - Lint/format/type‑check: ruff, black, mypy (configured in backend/pyproject.toml)

Deployment and production environments
- Production API base (example): https://mytrips-api.bahar.co.il
- SSL and CORS
  - See docs/SSL_SETUP.md and docs/CORS_FIX.md
  - README.md includes automated SSL helper scripts used on the server
- Update/deploy (server‑side scripts)
  - Typical backend update on server: sudo /opt/dayplanner/deployment/scripts/update.sh --backend-only && sudo systemctl restart dayplanner-backend
  - Verify SSE proxy and behavior post‑deploy (examples):
    - curl -sS https://mytrips-api.bahar.co.il/openapi.json | jq -r '.paths | keys[]' | grep '/api/location/live/sse'
    - No‑backlog default: curl -N "https://mytrips-api.bahar.co.il/api/location/live/sse?users=Adar&heartbeat=5" | head -n 20
    - Explicit backfill: curl -N "https://mytrips-api.bahar.co.il/api/location/live/sse?users=Adar&since=0&limit=50" | head -n 50
- Compatibility note
  - Code targets Python 3.11; a UTC fallback is implemented for Python 3.10 deployments (datetime.UTC → timezone.utc)

What’s implemented (highlights)
- Places search
  - Autocomplete: /places/v1/places/suggest with session_token, debouncing guidance, proximity/category/country filters
  - Full search: /places/v1/places/search with filters/sort/pagination
  - Documentation: docs/api/places-autocomplete.md
- Trip days and stops
  - Model + API for START/VIA/END as Stops referencing Places; constraints and automatic route recompute
  - Docs: docs/api/day-locations.md
- Live location and SSE
  - SSE default “start from now” when no since/Last-Event-ID provided
  - Same‑origin SSE proxy endpoint to inject X-API-Token for EventSource
  - Latest location and PHP‑compatible ingestion endpoints
  - Frontend SSE guidelines: frontend/docs/SSE_UI_INTEGRATION.md
- Operational improvements
  - SSL/CORS guides, health endpoints, stats caching windows, and testing configuration

What’s remaining / open items
- Pre‑commit health and repo hygiene
  - Align detect‑secrets baseline and versions; exclude build artifacts (frontend/.next) from hooks and git tracking
  - Ensure .gitignore covers transient outputs; re‑enable hooks after fix
- Deployment neutralization
  - Confirm SSE proxy route is deployed/visible in openapi.json in production
  - Roll out “now by default” SSE behavior to production and validate with curl
- Frontend integration work
  - Wire UI autocomplete to /places/v1/places/suggest (session_token lifecycle, debouncing)
  - Final search experience via /places/v1/places/search
  - Day editor: create/get Place then POST Stop (START/VIA/END) per docs/api/day-locations.md
- Testing
  - Expand integration tests around places endpoints and stops lifecycle
  - Validate SSE behavior (no backlog by default; Last-Event-ID resume)
- Documentation refinements
  - Keep docs/api/reference.md and exported openapi.json in sync with backend endpoints

Quick endpoint map (selected)
- Places: GET /places/v1/places/suggest, GET /places/v1/places/search, GET /places/v1/places/{place_id}
- Stops: POST /stops/{trip_id}/days/{day_id}/stops (create START/VIA/END), plus GET/PUT/DELETE
- Location ingest (legacy‑compatible): POST /location/api/getloc, POST /location/api/driving, POST /location/api/batch-sync
- Location queries: GET /location/api/locations, /driving-records, /users, /stats
- Live/SSE: GET /location/api/live/latest, GET /location/api/live/sse (and same‑origin proxy)

See also
- README.md — quick start, stack and deployment notes
- docs/architecture/overview.md — broader design context
- docs/COMPLETE_ENDPOINTS_API.md — endpoint coverage and status
- backend/docs/README.md and backend/docs/API_SUMMARY.md — backend‑centric overview
- docs/api/day-locations.md and docs/api/places-autocomplete.md — detailed how‑tos

