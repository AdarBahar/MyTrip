"""
Location database configuration and session management
Separate database for location-related endpoints
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Create location database engine with UTF8MB4 charset for proper Unicode support
location_engine = create_engine(
    settings.location_database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
    # Ensure proper UTF8MB4 charset for Unicode support (Hebrew, emojis, etc.)
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    },
)

# Create location database session factory
LocationSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=location_engine
)

# Create location database base class
LocationBase = declarative_base()


def get_location_db() -> Generator[Session, None, None]:
    """
    Dependency to get location database session
    """
    db = LocationSessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_location_tables():
    """
    Create all location database tables
    """
    LocationBase.metadata.create_all(bind=location_engine)


def drop_location_tables():
    """
    Drop all location database tables (for testing)
    """
    LocationBase.metadata.drop_all(bind=location_engine)
