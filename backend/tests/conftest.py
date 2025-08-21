"""
Test configuration and fixtures
"""
import pytest
import asyncio
import os
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["DB_CLIENT"] = "sqlite"
os.environ["DB_HOST"] = ":memory:"
os.environ["DB_NAME"] = "test"
os.environ["DB_USER"] = "test"
os.environ["DB_PASSWORD"] = "test"

from app.main import app
from app.core.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.trip import Trip


# Test database URL (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        display_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user"""
    return {
        "Authorization": f"Bearer fake_token_{test_user.id}"
    }


@pytest.fixture
def test_trip_data():
    """Sample trip data for testing"""
    return {
        "title": "Test Road Trip",
        "destination": "California, USA",
        "start_date": "2025-09-15",  # Use string format for JSON serialization
        "timezone": "UTC",
        "status": "draft",
        "is_published": False
    }


@pytest.fixture
def test_trip(db_session, test_user, test_trip_data):
    """Create a test trip"""
    from datetime import datetime

    # Convert string date to date object for SQLite
    start_date = test_trip_data["start_date"]
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    trip = Trip(
        slug="test-road-trip",
        title=test_trip_data["title"],
        destination=test_trip_data["destination"],
        start_date=start_date,
        timezone=test_trip_data["timezone"],
        status=test_trip_data["status"],
        is_published=test_trip_data["is_published"],
        created_by=test_user.id
    )
    db_session.add(trip)
    db_session.commit()
    db_session.refresh(trip)
    return trip


@pytest.fixture
def multiple_test_trips(db_session, test_user):
    """Create multiple test trips for list testing"""
    from datetime import date
    trips = []
    for i in range(3):
        trip = Trip(
            slug=f"test-trip-{i+1}",
            title=f"Test Trip {i+1}",
            destination=f"Destination {i+1}",
            start_date=date(2025, 9, 15) if i % 2 == 0 else None,  # Some with dates, some without
            timezone="UTC",
            status="draft" if i == 0 else "active",
            is_published=i == 2,  # Only last one published
            created_by=test_user.id
        )
        db_session.add(trip)
        trips.append(trip)

    db_session.commit()
    for trip in trips:
        db_session.refresh(trip)

    return trips


@pytest.fixture
def test_day(db_session, test_trip):
    """Create a test day"""
    from app.models.day import Day, DayStatus
    from datetime import date

    day = Day(
        trip_id=test_trip.id,
        seq=1,
        date=date(2024, 6, 15),
        status=DayStatus.ACTIVE,
        rest_day=False,
        notes={"description": "Test day"}
    )
    db_session.add(day)
    db_session.commit()
    db_session.refresh(day)
    return day
