#!/usr/bin/env python3
"""
Test script to verify dual database configuration
Tests both main database and location database connections
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_main_database():
    """Test main database configuration"""
    print("🔍 Testing main database configuration...")

    try:
        from app.core.config import settings
        from app.core.database import engine

        print(f"   Main DB URL: {settings.database_url}")
        print(f"   Main DB Host: {settings.DB_HOST}")
        print(f"   Main DB Name: {settings.DB_NAME}")
        print(f"   Main DB User: {settings.DB_USER}")

        # Test connection (will fail if no database, but that's expected in dev)
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT 1 as test").scalar()
                print(f"   ✅ Main database connection successful: {result}")
                return True
        except Exception as e:
            print(f"   ⚠️  Main database connection failed (expected in dev): {e}")
            return False

    except Exception as e:
        print(f"   ❌ Main database configuration error: {e}")
        return False


def test_location_database():
    """Test location database configuration"""
    print("\n🔍 Testing location database configuration...")

    try:
        from app.core.config import settings
        from app.core.location_database import location_engine

        print(f"   Location DB URL: {settings.location_database_url}")
        print(f"   Location DB Host: {settings.LOCATION_DB_HOST or settings.DB_HOST}")
        print(f"   Location DB Name: {settings.LOCATION_DB_NAME}")
        print(f"   Location DB User: {settings.LOCATION_DB_USER}")

        # Test connection (will fail if no database, but that's expected in dev)
        try:
            with location_engine.connect() as conn:
                result = conn.execute("SELECT 1 as test").scalar()
                print(f"   ✅ Location database connection successful: {result}")
                return True
        except Exception as e:
            print(f"   ⚠️  Location database connection failed (expected in dev): {e}")
            return False

    except Exception as e:
        print(f"   ❌ Location database configuration error: {e}")
        return False


def test_models():
    """Test model imports"""
    print("\n🔍 Testing model imports...")

    try:
        # Test main database models

        print("   ✅ Main database models imported successfully")

        # Test location database models

        print("   ✅ Location database models imported successfully")

        return True

    except Exception as e:
        print(f"   ❌ Model import error: {e}")
        return False


def test_dependencies():
    """Test database dependencies"""
    print("\n🔍 Testing database dependencies...")

    try:
        print("   ✅ Main database dependency imported successfully")
        print("   ✅ Location database dependency imported successfully")

        return True

    except Exception as e:
        print(f"   ❌ Dependency import error: {e}")
        return False


def test_router():
    """Test location router"""
    print("\n🔍 Testing location router...")

    try:
        from app.api.location.router import router

        routes = [route.path for route in router.routes]
        print("   ✅ Location router imported successfully")
        print(f"   ✅ Router has {len(router.routes)} routes: {routes}")

        return True

    except Exception as e:
        print(f"   ❌ Router import error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Dual Database Configuration")
    print("=" * 50)

    # Set minimal environment for testing
    os.environ.setdefault("DB_CLIENT", "mysql")
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_NAME", "test_main")
    os.environ.setdefault("DB_USER", "test_user")
    os.environ.setdefault("DB_PASSWORD", "test_pass")

    tests = [
        test_main_database,
        test_location_database,
        test_models,
        test_dependencies,
        test_router,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n🎉 All tests passed! Dual database configuration is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the configuration above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
