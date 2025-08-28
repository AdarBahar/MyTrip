# Backend Configuration and Safety Checks

This backend connects to a remote MySQL database. To prevent accidental use of a wrong database in development, we enforce strict environment checks at startup.

## Required environment variables

Define these in the project root `.env` used by docker-compose:

- `DB_CLIENT` (mysql)
- `DB_HOST` (e.g., srv1135.hstgr.io)
- `DB_PORT` (3306)
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `CORS_ORIGINS` (e.g., http://localhost:3000)
- `APP_ENV` (dev)
- `ENFORCE_PROD_DB` (true/false)
- `PROD_DB_HOST` (srv1135.hstgr.io)

## Startup safety (prestart)

The Docker container runs `prestart.py` before starting uvicorn. It will:
- Fail if any required DB envs are missing
- Fail if `ENFORCE_PROD_DB=true` and `DB_HOST != PROD_DB_HOST`
- Connect to the DB and check the `trips` table exists
- Print a banner with the selected DB

## Health check

`/health` will include a DB readiness probe in a future update. For now, the container’s health depends on the app starting successfully, which includes the prestart DB checks.

## Alembic migrations

If you change models or pull latest code, apply migrations:

```
docker-compose exec backend bash -lc "alembic upgrade head"
```

This ensures the DB schema matches the code (e.g., enhanced `stops` columns).

