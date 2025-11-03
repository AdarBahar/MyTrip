#!/usr/bin/env python3
"""
Integration test for location health endpoint
Tests the actual endpoint with FastAPI TestClient
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def test_health_endpoint_integration():
    """Test the health endpoint with FastAPI TestClient"""
    print("🔗 Testing location health endpoint integration...")

    try:
        # Set environment for testing
        os.environ.setdefault("DB_CLIENT", "mysql")
        os.environ.setdefault("DB_HOST", "localhost")
        os.environ.setdefault("DB_NAME", "test_main")
        os.environ.setdefault("DB_USER", "test_user")
        os.environ.setdefault("DB_PASSWORD", "test_pass")

        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)

        print("   ✅ FastAPI TestClient created successfully")

        # Test the health endpoint
        response = client.get("/location/health")

        print(f"   📊 Response status: {response.status_code}")
        print(f"   📋 Response headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print("   ✅ Health endpoint returned 200 OK")
            print(f"   📋 Response data: {data}")

            # Validate response structure
            required_fields = ["status", "module", "database", "timestamp"]
            for field in required_fields:
                if field in data:
                    print(f"   ✅ Required field '{field}' present")
                else:
                    print(f"   ❌ Required field '{field}' missing")
                    return False

            # Check database info
            db_info = data.get("database", {})
            if "connected" in db_info:
                if db_info["connected"]:
                    print(f"   ✅ Database connected: {db_info.get('database_name')}")
                else:
                    print(f"   ⚠️  Database connection failed: {db_info.get('error')}")

            return True

        else:
            print(f"   ❌ Health endpoint returned {response.status_code}")
            print(f"   📋 Response text: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run integration test"""
    print("🧪 Location Health Endpoint Integration Test")
    print("=" * 50)

    result = test_health_endpoint_integration()

    print("\n" + "=" * 50)
    if result:
        print("🎉 Integration test passed!")
        print("\n📋 Endpoint Ready:")
        print("   URL: GET /location/health")
        print("   Purpose: Check baharc5_location database connection")
        print("   Status: ✅ Working correctly")
        print("\n🚀 You can now test the endpoint:")
        print("   curl http://localhost:8000/location/health")
        return 0
    else:
        print("❌ Integration test failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Check database configuration")
        print("   2. Verify location database credentials")
        print("   3. Ensure FastAPI app is properly configured")
        return 1


if __name__ == "__main__":
    sys.exit(main())
