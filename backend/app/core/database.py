"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create database engine with proper configuration based on database type
def _get_connect_args():
    """Get connection arguments based on database type"""
    if settings.database_url.startswith("sqlite://"):
        # SQLite configuration
        return {"check_same_thread": False}
    else:
        # MySQL/PostgreSQL configuration
        return {
            "charset": "utf8mb4",
            "use_unicode": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"
        }

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
    connect_args=_get_connect_args()
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()