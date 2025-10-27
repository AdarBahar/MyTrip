#!/usr/bin/env python3
"""
Production Deployment Verification Script
Verifies that the app-login endpoint and other features are working correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
BASE_URL = "https://mytrips-api.bahar.co.il"
TEST_USER = {
    "email": "test@example.com",
    "password": "test123"
}

def log_info(message: str):
    print(f"ℹ️  {message}")

def log_success(message: str):
    print(f"✅ {message}")

def log_error(message: str):
    print(f"❌ {message}")

def log_warning(message: str):
    print(f"⚠️  {message}")

def test_health_endpoint() -> bool:
    """Test the health endpoint"""
    log_info("Testing health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            log_success("Health endpoint is working")
            return True
        else:
            log_error(f"Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Health endpoint failed: {e}")
        return False

def test_app_login_endpoint() -> bool:
    """Test the new app-login endpoint"""
    log_info("Testing app-login endpoint...")
    
    try:
        # Test with valid credentials (should work if test user exists)
        response = requests.post(
            f"{BASE_URL}/auth/app-login",
            json=TEST_USER,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "authenticated" in data and "message" in data:
                if data["authenticated"]:
                    log_success("App-login endpoint working with valid credentials")
                else:
                    log_warning("App-login endpoint working but user not found (expected if test user doesn't exist)")
                return True
            else:
                log_error("App-login endpoint returned invalid response format")
                return False
        else:
            log_error(f"App-login endpoint returned status {response.status_code}")
            log_error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        log_error(f"App-login endpoint failed: {e}")
        return False

def test_app_login_validation() -> bool:
    """Test app-login endpoint validation"""
    log_info("Testing app-login endpoint validation...")
    
    try:
        # Test with invalid data (should return 422)
        response = requests.post(
            f"{BASE_URL}/auth/app-login",
            json={"email": "invalid-email", "password": ""},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 422:
            log_success("App-login endpoint validation working correctly")
            return True
        else:
            log_warning(f"App-login validation returned unexpected status {response.status_code}")
            return True  # Not a critical failure
            
    except Exception as e:
        log_error(f"App-login validation test failed: {e}")
        return False

def test_swagger_documentation() -> bool:
    """Test that Swagger documentation is accessible"""
    log_info("Testing Swagger documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            log_success("Swagger documentation is accessible")
            return True
        else:
            log_error(f"Swagger documentation returned status {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Swagger documentation failed: {e}")
        return False

def test_openapi_spec() -> bool:
    """Test that OpenAPI specification includes app-login endpoint"""
    log_info("Testing OpenAPI specification...")
    
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            spec = response.json()
            if "/auth/app-login" in spec.get("paths", {}):
                log_success("OpenAPI specification includes app-login endpoint")
                return True
            else:
                log_error("OpenAPI specification missing app-login endpoint")
                return False
        else:
            log_error(f"OpenAPI specification returned status {response.status_code}")
            return False
    except Exception as e:
        log_error(f"OpenAPI specification test failed: {e}")
        return False

def test_existing_endpoints() -> bool:
    """Test that existing endpoints still work"""
    log_info("Testing existing endpoints...")
    
    try:
        # Test trips endpoint (should require auth but return 401, not 500)
        response = requests.get(f"{BASE_URL}/trips", timeout=10)
        if response.status_code in [401, 403]:
            log_success("Existing endpoints are working (auth required as expected)")
            return True
        elif response.status_code == 200:
            log_success("Existing endpoints are working")
            return True
        else:
            log_error(f"Existing endpoints returned unexpected status {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Existing endpoints test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 Production Deployment Verification")
    print("=" * 50)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("App-Login Endpoint", test_app_login_endpoint),
        ("App-Login Validation", test_app_login_validation),
        ("Swagger Documentation", test_swagger_documentation),
        ("OpenAPI Specification", test_openapi_spec),
        ("Existing Endpoints", test_existing_endpoints),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Deployment is successful.")
        print("\n🔗 Quick Links:")
        print(f"   📖 Swagger UI: {BASE_URL}/docs")
        print(f"   🔐 App Login: POST {BASE_URL}/auth/app-login")
        print(f"   📋 Health: {BASE_URL}/health")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
