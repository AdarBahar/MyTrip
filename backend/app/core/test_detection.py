"""
Test environment detection utilities

This module provides utilities to detect if the application is running in a test environment.
This is crucial to prevent test configurations from leaking into development/production.
"""
import os
import sys
from typing import List


def is_running_tests() -> bool:
    """
    Detect if we're currently running in a test environment.
    
    This function checks multiple indicators to determine if tests are being executed:
    1. pytest module is imported
    2. pytest is in the command line arguments
    3. PYTEST_CURRENT_TEST environment variable is set
    4. Common test runner patterns in sys.argv
    
    Returns:
        bool: True if running tests, False otherwise
    """
    # Check if pytest is imported
    if "pytest" in sys.modules:
        return True
    
    # Check command line arguments
    if sys.argv:
        # Check if pytest is in the main command
        if "pytest" in sys.argv[0]:
            return True
        
        # Check if pytest is anywhere in the arguments
        if any("pytest" in str(arg) for arg in sys.argv):
            return True
        
        # Check for test runner patterns
        test_patterns = ["test", "run_tests.py", "-m pytest"]
        if any(pattern in " ".join(sys.argv) for pattern in test_patterns):
            return True
    
    # Check environment variables
    test_env_vars = [
        "PYTEST_CURRENT_TEST",
        "TESTING",
        "_PYTEST_RAISE",
        "PYTEST_VERSION"
    ]
    
    if any(os.environ.get(var) for var in test_env_vars):
        return True
    
    return False


def get_test_indicators() -> List[str]:
    """
    Get a list of current test environment indicators for debugging.
    
    Returns:
        List[str]: List of detected test indicators
    """
    indicators = []
    
    if "pytest" in sys.modules:
        indicators.append("pytest module imported")
    
    if sys.argv and "pytest" in sys.argv[0]:
        indicators.append(f"pytest in main command: {sys.argv[0]}")
    
    if sys.argv and any("pytest" in str(arg) for arg in sys.argv):
        pytest_args = [arg for arg in sys.argv if "pytest" in str(arg)]
        indicators.append(f"pytest in arguments: {pytest_args}")
    
    test_env_vars = ["PYTEST_CURRENT_TEST", "TESTING", "_PYTEST_RAISE", "PYTEST_VERSION"]
    for var in test_env_vars:
        if os.environ.get(var):
            indicators.append(f"environment variable {var}={os.environ.get(var)}")
    
    return indicators


def ensure_not_in_tests(operation_name: str) -> None:
    """
    Ensure that a sensitive operation is not being performed during tests.
    
    This is useful for operations that should never happen during testing,
    such as connecting to production databases or sending real emails.
    
    Args:
        operation_name: Name of the operation being performed
        
    Raises:
        RuntimeError: If running in test environment
    """
    if is_running_tests():
        indicators = get_test_indicators()
        raise RuntimeError(
            f"Operation '{operation_name}' should not be performed during tests. "
            f"Test indicators detected: {indicators}"
        )


def warn_if_test_config_leaked() -> None:
    """
    Warn if test configuration appears to be leaking into non-test environment.
    
    This function checks for common test configuration patterns that might
    indicate test settings are being applied outside of test execution.
    """
    if not is_running_tests():
        # Check for test database configuration
        db_client = os.environ.get("DB_CLIENT", "").lower()
        db_host = os.environ.get("DB_HOST", "")
        
        if db_client == "sqlite" and db_host == ":memory:":
            print(
                "⚠️  WARNING: Test database configuration detected outside of test environment!\n"
                "   DB_CLIENT=sqlite and DB_HOST=:memory: should only be used during testing.\n"
                "   This might indicate test configuration is leaking into development/production.\n"
                "   Check your test configuration files (conftest.py) for global overrides."
            )
