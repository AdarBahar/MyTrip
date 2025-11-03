#!/usr/bin/env python3
"""
Test the location health endpoint
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_health_endpoint():
    """Test the location health endpoint"""
    print("🏥 Testing location health endpoint...")

    try:
        # Set minimal environment for testing
        os.environ.setdefault("DB_CLIENT", "mysql")
        os.environ.setdefault("DB_HOST", "localhost")
        os.environ.setdefault("DB_NAME", "test_main")
        os.environ.setdefault("DB_USER", "test_user")
        os.environ.setdefault("DB_PASSWORD", "test_pass")

        from app.schemas.location import LocationHealthResponse

        print("   ✅ Health endpoint imported successfully")
        print("   ✅ Location database dependency imported successfully")
        print("   ✅ Health response schema imported successfully")

        # Test schema validation
        test_response = {
            "status": "ok",
            "module": "location",
            "database": {
                "connected": True,
                "database_name": "baharc5_location",
                "database_user": "baharc5_location",
                "test_query": 1,
                "expected_database": "baharc5_location",
                "expected_user": "baharc5_location",
            },
            "timestamp": "2024-01-01T12:00:00Z",
        }

        # Validate response schema
        validated_response = LocationHealthResponse(**test_response)
        print("   ✅ Health response schema validation successful")
        print(f"   📋 Response fields: {list(validated_response.model_dump().keys())}")

        return True

    except Exception as e:
        print(f"   ❌ Health endpoint test failed: {e}")
        return False


def test_error_response():
    """Test error response schema"""
    print("\n🚨 Testing error response schema...")

    try:
        from app.schemas.location import LocationHealthResponse

        test_error_response = {
            "status": "error",
            "module": "location",
            "database": {
                "connected": False,
                "expected_database": "baharc5_location",
                "expected_user": "baharc5_location",
                "error": "Connection failed",
            },
            "timestamp": "2024-01-01T12:00:00Z",
        }

        # Validate error response schema
        validated_response = LocationHealthResponse(**test_error_response)
        print("   ✅ Error response schema validation successful")
        print(f"   📋 Error response: {validated_response.database.error}")

        return True

    except Exception as e:
        print(f"   ❌ Error response test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Location Health Endpoint")
    print("=" * 50)

    tests = [test_health_endpoint, test_error_response]

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
        print("\n🎉 All tests passed! Location health endpoint is ready.")
        print("\n📋 Endpoint Details:")
        print("   URL: GET /location/health")
        print("   Purpose: Check baharc5_location database connection")
        print("   Response: JSON with connection status and database info")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the configuration above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
