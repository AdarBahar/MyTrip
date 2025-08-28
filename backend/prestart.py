"""
Backend prestart checks: ensure DB config present, expected host, and schema reachable.
"""
from sqlalchemy import create_engine, text
import os
import sys

from app.core.config import settings


def redact_url(url: str) -> str:
    try:
        # Hide password in logs
        if '://' in url:
            scheme_rest = url.split('://', 1)
            creds_rest = scheme_rest[1].split('@', 1)
            if len(creds_rest) == 2 and ':' in creds_rest[0]:
                user, _ = creds_rest[0].split(':', 1)
                return f"{scheme_rest[0]}://{user}:***@{creds_rest[1]}"
        return url
    except Exception:
        return url


def main():
    required = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"[PRESTART] Missing required DB env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Enforce prod host if enabled
    if settings.ENFORCE_PROD_DB and settings.DB_HOST != settings.PROD_DB_HOST:
        print(
            f"[PRESTART] ENFORCE_PROD_DB is enabled and DB_HOST={settings.DB_HOST} != PROD_DB_HOST={settings.PROD_DB_HOST}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Try DB connection and basic schema check
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with engine.connect() as conn:
        dbname = conn.execute(text("SELECT DATABASE()")).scalar()
        print(f"[PRESTART] Connected to DB: {dbname}")
        try:
            conn.execute(text("SELECT 1 FROM trips LIMIT 1"))
        except Exception as e:
            print(f"[PRESTART] Schema check failed for 'trips' table: {e}", file=sys.stderr)
            sys.exit(1)

    # Success banner
    print("[PRESTART] DB check OK. Using:")
    print(f"  HOST={settings.DB_HOST}")
    print(f"  NAME={settings.DB_NAME}")
    print(f"  URL={redact_url(settings.database_url)}")


if __name__ == "__main__":
    main()

