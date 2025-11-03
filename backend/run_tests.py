#!/usr/bin/env python3
"""
Comprehensive Test Runner for MyTrip Backend API

This script runs various types of tests for the backend API, including:
- Health endpoints (main + location database)
- Authentication (login + app-login)
- All API endpoints (trips, days, stops, routing, etc.)
- Database integration tests
- Comprehensive test suites

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py comprehensive      # Run comprehensive test suite
    python run_tests.py endpoints          # Test all API endpoints
    python run_tests.py auth               # Test authentication
    python run_tests.py location           # Test location endpoints
    python run_tests.py health             # Test health endpoints
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --quick            # Run quick tests only
"""
import sys
import subprocess
import os
from pathlib import Path


def print_test_info():
    """Print information about available test types"""
    print("\n🧪 MyTrip Backend Test Runner")
    print("=" * 50)
    print("\n📋 Available Test Types:")
    print("  all           - Run all tests")
    print("  comprehensive - Complete test suite (health, auth, trips, days, stops, routing, location)")
    print("  endpoints     - Test all API endpoints")
    print("  unit          - Unit tests only")
    print("  integration   - Integration tests only")
    print("  auth          - Authentication tests (login + app-login)")
    print("  trips         - Trip management tests")
    print("  days          - Day management tests")
    print("  stops         - Stop management tests")
    print("  routing       - Routing and optimization tests")
    print("  health        - Health check tests (main + location)")
    print("  location      - Location database tests")
    print("  ai            - AI-powered features tests")

    print("\n🔧 Options:")
    print("  -v, --verbose - Verbose output")
    print("  -c, --coverage - Generate coverage report")
    print("  --quick       - Run quick tests only (exclude slow tests)")

    print("\n💡 Examples:")
    print("  python run_tests.py comprehensive --coverage")
    print("  python run_tests.py auth -v")
    print("  python run_tests.py location --quick")
    print("  python run_tests.py endpoints")


def run_tests(test_type="all", verbose=False, coverage=False, quick=False):
    """
    Run tests with various options

    Args:
        test_type: Type of tests to run
        verbose: Whether to run in verbose mode
        coverage: Whether to generate coverage report
        quick: Whether to run quick tests only (exclude slow tests)
    """

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test selection based on type
    if test_type == "all":
        cmd.append("tests/")
    elif test_type == "unit":
        cmd.extend(["-m", "unit", "tests/"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration", "tests/"])
    elif test_type == "auth":
        cmd.extend(["tests/test_auth.py", "tests/test_auth_comprehensive.py"])
    elif test_type == "trips":
        cmd.extend(["tests/test_trips.py", "tests/test_trip_dates.py"])
    elif test_type == "days":
        cmd.append("tests/test_days.py")
    elif test_type == "stops":
        cmd.append("tests/test_stops_management.py")
    elif test_type == "routing":
        cmd.extend(["tests/test_routing.py", "tests/test_route_optimization.py"])
    elif test_type == "health":
        cmd.append("tests/test_health.py")
    elif test_type == "location":
        cmd.append("tests/test_location.py")
    elif test_type == "ai":
        cmd.append("tests/test_ai.py")
    elif test_type == "comprehensive":
        # Run comprehensive test suite covering all major endpoints
        cmd.extend([
            "tests/test_health.py",
            "tests/test_auth.py",
            "tests/test_auth_comprehensive.py",
            "tests/test_trips.py",
            "tests/test_days.py",
            "tests/test_stops_management.py",
            "tests/test_routing.py",
            "tests/test_location.py"
        ])
    elif test_type == "endpoints":
        # Test all API endpoints
        cmd.extend([
            "tests/test_health.py",
            "tests/test_auth.py",
            "tests/test_trips.py",
            "tests/test_days.py",
            "tests/test_routing.py",
            "tests/test_location.py",
            "tests/test_ai.py"
        ])
    else:
        print(f"❌ Unknown test type: {test_type}")
        print_test_info()
        return 1

    # Add quick test filter
    if quick:
        cmd.extend(["-m", "not slow"])
    
    # Add verbose flag
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    # Print test summary
    print(f"\n🚀 Running {test_type} tests...")
    if test_type == "comprehensive":
        print("   📋 Test Coverage:")
        print("      ✅ Health endpoints (main + location database)")
        print("      ✅ Authentication (login + app-login)")
        print("      ✅ Trip management")
        print("      ✅ Day management")
        print("      ✅ Stop management")
        print("      ✅ Routing and optimization")
        print("      ✅ Location database integration")
    elif test_type == "endpoints":
        print("   📋 Testing all API endpoints for functionality")
    elif test_type == "location":
        print("   📋 Testing location database and endpoints")
    elif test_type == "auth":
        print("   📋 Testing authentication (login + app-login)")

    print(f"\n💻 Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run backend API tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=[
            "all", "unit", "integration", "auth", "trips", "days", "stops",
            "routing", "health", "location", "ai", "comprehensive", "endpoints"
        ],
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (exclude slow tests)"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show information about available test types"
    )

    args = parser.parse_args()

    # Show info if requested
    if args.info:
        print_test_info()
        return 0
    
    # Run the tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage,
        quick=args.quick
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if args.test_type == "comprehensive":
            print("\n🎉 Comprehensive test suite completed successfully!")
            print("   ✅ Health endpoints (main + location)")
            print("   ✅ Authentication (login + app-login)")
            print("   ✅ Trips management")
            print("   ✅ Days management")
            print("   ✅ Stops management")
            print("   ✅ Routing and optimization")
            print("   ✅ Location database integration")
        elif args.test_type == "endpoints":
            print("\n🎉 All API endpoints tested successfully!")
            print("   ✅ All major API endpoints are working")
            print("   ✅ Authentication is properly enforced")
            print("   ✅ Database connections are healthy")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
        if args.test_type in ["comprehensive", "endpoints"]:
            print("   💡 Run individual test types to isolate issues:")
            print("      python run_tests.py health")
            print("      python run_tests.py auth")
            print("      python run_tests.py location")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
