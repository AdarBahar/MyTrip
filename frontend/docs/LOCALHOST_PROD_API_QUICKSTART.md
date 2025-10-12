# Localhost Dev against Production API

Run the frontend locally on port 3500 and point all API calls to the production backend.

## Prereqs
- Node >= 18
- pnpm >= 8

## Install
```
pnpm install --no-frozen-lockfile
```

## Run
```
pnpm dev
```
Open http://localhost:3500

## Login
- Use your production credentials.

## Notes
- API base URL is set via `next.config.js` env defaults:
  - `NEXT_PUBLIC_API_URL=https://mytrips-api.bahar.co.il`
- The login page stores `auth_token` in localStorage; all requests include `Authorization: Bearer <token>` automatically.
- If you need to override the API endpoint, create `.env.local` with:
```
NEXT_PUBLIC_API_URL=https://mytrips-api.bahar.co.il
```
