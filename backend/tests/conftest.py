"""
Test configuration and fixtures
"""
import pytest
import asyncio
import os
import sys
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


# Import test detection utility
try:
    from app.core.test_detection import is_running_tests, warn_if_test_config_leaked
except ImportError:
    # Fallback if the utility is not available
    def is_running_tests() -> bool:
        """Fallback test detection"""
        return (
            "pytest" in sys.modules or
            "pytest" in sys.argv[0] if sys.argv else False or
            any("pytest" in str(arg) for arg in sys.argv) or
            os.environ.get("PYTEST_CURRENT_TEST") is not None
        )

    def warn_if_test_config_leaked() -> None:
        """Fallback warning function"""
        pass


# Only set test environment variables when actually running tests
if is_running_tests():
    print("🧪 Test environment detected - configuring SQLite database")
    os.environ["DB_CLIENT"] = "sqlite"
    os.environ["DB_HOST"] = ":memory:"
    os.environ["DB_NAME"] = "test"
    os.environ["DB_USER"] = "test"
    os.environ["DB_PASSWORD"] = "test"
else:
    print("⚠️  conftest.py imported outside of test environment")
    warn_if_test_config_leaked()

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


# Only override the database dependency when actually running tests
if is_running_tests():
    print("🧪 Overriding database dependency for tests (SQLite in-memory)")
    app.dependency_overrides[get_db] = override_get_db
else:
    print("✅ Skipping database override - not in test environment")
    # Ensure no test overrides are accidentally applied
    if get_db in app.dependency_overrides:
        print("⚠️  WARNING: Removing existing database override that shouldn't be there!")
        del app.dependency_overrides[get_db]


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

    day = Day(
        trip_id=test_trip.id,
        seq=1,
        status=DayStatus.ACTIVE,
        rest_day=False,
        notes={"description": "Test day"}
    )
    db_session.add(day)
    db_session.commit()
    db_session.refresh(day)
    return day


@pytest.fixture
def test_place(db_session, test_user):
    """Create a test place"""
    from app.models.place import Place, OwnerType

    place = Place(
        owner_type=OwnerType.USER,
        owner_id=test_user.id,
        name="Test Restaurant",
        address="123 Main St, Test City, TS 12345",
        lat=40.7128,
        lon=-74.0060,
        meta={"type": "restaurant", "cuisine": "american"}
    )
    db_session.add(place)
    db_session.commit()
    db_session.refresh(place)
    return place


# Enhanced testing fixtures for authentication testing
@pytest.fixture
def test_admin_user(db_session):
    """Create a test admin user"""
    user = User(
        email="admin@example.com",
        display_name="Admin User",
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_auth_headers(test_admin_user):
    """Create authentication headers for admin user"""
    return {
        "Authorization": f"Bearer fake_token_{test_admin_user.id}"
    }


@pytest.fixture
def invalid_auth_headers():
    """Create invalid authentication headers for testing"""
    return {
        "Authorization": "Bearer invalid_token_123"
    }


@pytest.fixture
def expired_auth_headers():
    """Create expired authentication headers for testing"""
    return {
        "Authorization": "Bearer fake_token_expired_user"
    }


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_user_data(email: str = "test@example.com", **kwargs):
        """Create user data for API requests"""
        return {
            "email": email,
            "display_name": kwargs.get("display_name", "Test User"),
            "password": kwargs.get("password", "testpassword123"),
            **kwargs
        }

    @staticmethod
    def create_login_data(email: str = "test@example.com", password: str = "testpassword123"):
        """Create login data for authentication tests"""
        return {
            "email": email,
            "password": password
        }

    @staticmethod
    def create_trip_data(title: str = "Test Trip", **kwargs):
        """Create trip data for API requests"""
        return {
            "title": title,
            "destination": kwargs.get("destination", "Test Destination"),
            "start_date": kwargs.get("start_date", "2024-06-01"),
            "timezone": kwargs.get("timezone", "UTC"),
            "status": kwargs.get("status", "draft"),
            "is_published": kwargs.get("is_published", False),
            **kwargs
        }


@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory


# Security testing utilities
def assert_requires_auth(client: TestClient, method: str, endpoint: str, **kwargs):
    """Assert that an endpoint requires authentication"""
    response = getattr(client, method.lower())(endpoint, **kwargs)
    assert response.status_code == 401, f"Expected 401 for unauthenticated {method} {endpoint}"


def assert_requires_admin(client: TestClient, method: str, endpoint: str, auth_headers: dict, **kwargs):
    """Assert that an endpoint requires admin privileges"""
    response = getattr(client, method.lower())(endpoint, headers=auth_headers, **kwargs)
    assert response.status_code in [401, 403], f"Expected 401/403 for non-admin {method} {endpoint}"


# Performance testing utilities
import time
from contextlib import contextmanager

@contextmanager
def measure_time():
    """Context manager to measure execution time"""
    start = time.time()
    yield lambda: time.time() - start


def assert_response_time(client: TestClient, method: str, endpoint: str, max_time: float = 1.0, **kwargs):
    """Assert that an API call completes within specified time"""
    with measure_time() as get_time:
        response = getattr(client, method.lower())(endpoint, **kwargs)

    elapsed = get_time()
    assert elapsed < max_time, f"{method} {endpoint} took {elapsed:.2f}s (max: {max_time}s)"
    return response


# Custom pytest markers for better test organization
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "jwt: JWT authentication tests")
    config.addinivalue_line("markers", "regression: Regression tests")
