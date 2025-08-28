#!/usr/bin/env python3
"""
Test runner script for the backend API tests
"""
import sys
import subprocess
import os
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """
    Run tests with various options
    
    Args:
        test_type: Type of tests to run ("all", "unit", "integration", "auth", "trips", "routing", "health")
        verbose: Whether to run in verbose mode
        coverage: Whether to generate coverage report
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
        cmd.append("tests/test_auth.py")
    elif test_type == "trips":
        cmd.extend(["tests/test_trips.py", "tests/test_trip_dates.py"])
    elif test_type == "routing":
        cmd.append("tests/test_routing.py")
    elif test_type == "health":
        cmd.append("tests/test_health.py")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
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
    
    print(f"Running command: {' '.join(cmd)}")
    print("-" * 50)
    
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
        choices=["all", "unit", "integration", "auth", "trips", "routing", "health"],
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
    
    args = parser.parse_args()
    
    # Run the tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
