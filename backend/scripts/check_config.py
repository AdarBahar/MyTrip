#!/usr/bin/env python3
"""
Configuration validation script

This script checks the current application configuration to ensure:
1. No test configuration is leaking into development/production
2. Database configuration is correct for the environment
3. All required environment variables are set
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.core.config import settings
    from app.core.test_detection import is_running_tests, get_test_indicators
    from app.main import app
    from app.core.database import get_db
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)


def check_test_environment():
    """Check if we're running in test environment"""
    print("🔍 Checking test environment detection...")
    
    running_tests = is_running_tests()
    indicators = get_test_indicators()
    
    print(f"   Running tests: {running_tests}")
    if indicators:
        print(f"   Test indicators: {indicators}")
    else:
        print("   No test indicators detected")
    
    return running_tests


def check_database_config():
    """Check database configuration"""
    print("\n🗄️  Checking database configuration...")
    
    db_client = settings.DB_CLIENT
    db_host = settings.DB_HOST
    db_name = settings.DB_NAME
    db_url = settings.database_url
    
    print(f"   DB_CLIENT: {db_client}")
    print(f"   DB_HOST: {db_host}")
    print(f"   DB_NAME: {db_name}")
    print(f"   Database URL: {db_url}")
    
    # Check for test configuration leak
    if db_client.lower() == "sqlite" and db_host == ":memory:":
        print("   ❌ WARNING: SQLite in-memory database detected!")
        print("      This should only be used during testing.")
        return False
    elif db_client.lower() == "mysql":
        print("   ✅ MySQL database configuration detected")
        return True
    else:
        print(f"   ⚠️  Unknown database client: {db_client}")
        return False


def check_dependency_overrides():
    """Check for FastAPI dependency overrides"""
    print("\n🔧 Checking FastAPI dependency overrides...")
    
    overrides = app.dependency_overrides
    
    if not overrides:
        print("   ✅ No dependency overrides detected")
        return True
    
    print(f"   Found {len(overrides)} dependency overrides:")
    for dependency, override in overrides.items():
        print(f"      {dependency.__name__} -> {override.__name__}")
    
    # Check specifically for database override
    if get_db in overrides:
        print("   ❌ WARNING: Database dependency is overridden!")
        print("      This should only happen during testing.")
        return False
    
    return True


def check_environment_variables():
    """Check critical environment variables"""
    print("\n🌍 Checking environment variables...")
    
    required_vars = ["DB_CLIENT", "DB_HOST", "DB_NAME", "DB_USER"]
    optional_vars = ["DB_PASSWORD", "APP_ENV", "DEBUG"]
    
    missing_vars = []
    
    print("   Required variables:")
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            display_value = value if var != "DB_PASSWORD" else "***"
            print(f"      {var}: {display_value}")
        else:
            print(f"      {var}: ❌ MISSING")
            missing_vars.append(var)
    
    print("   Optional variables:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            display_value = value if var != "DB_PASSWORD" else "***"
            print(f"      {var}: {display_value}")
        else:
            print(f"      {var}: (not set)")
    
    if missing_vars:
        print(f"   ❌ Missing required variables: {missing_vars}")
        return False
    
    print("   ✅ All required environment variables are set")
    return True


def main():
    """Main validation function"""
    print("🔍 Configuration Validation Report")
    print("=" * 50)
    
    checks = [
        ("Test Environment", check_test_environment),
        ("Database Configuration", check_database_config),
        ("Dependency Overrides", check_dependency_overrides),
        ("Environment Variables", check_environment_variables),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ❌ Error during {check_name} check: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n📊 Summary")
    print("-" * 20)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n🎯 Overall Status")
    print("-" * 20)
    
    if all_passed:
        print("✅ All configuration checks passed!")
        print("   Your application is properly configured.")
    else:
        print("❌ Some configuration checks failed!")
        print("   Please review the issues above and fix them.")
        print("   See backend/docs/TESTING_CONFIGURATION.md for help.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
