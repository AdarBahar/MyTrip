# Testing Configuration Guide

## 🚨 Critical: Preventing Test Configuration Leaks

This document explains how our testing configuration works and how to prevent test settings from leaking into development/production environments.

## The Problem We Solved

Previously, test configuration in `conftest.py` was being applied globally whenever the file was imported, causing:

- ❌ Development server using SQLite instead of MySQL
- ❌ Production deployments potentially using test database
- ❌ Authentication working with non-existent users
- ❌ Data inconsistencies between environments

## Current Solution

### 1. Conditional Test Configuration

Test settings are now only applied when actually running tests:

```python
# In conftest.py
if is_running_tests():
    # Apply test configuration
    os.environ["DB_CLIENT"] = "sqlite"
    app.dependency_overrides[get_db] = override_get_db
else:
    # Skip test configuration
    print("✅ Skipping database override - not in test environment")
```

### 2. Test Environment Detection

We use multiple indicators to detect test execution:

```python
def is_running_tests() -> bool:
    return (
        "pytest" in sys.modules or
        "pytest" in sys.argv[0] or
        any("pytest" in arg for arg in sys.argv) or
        os.environ.get("PYTEST_CURRENT_TEST") is not None
    )
```

### 3. Startup Warnings

The main application checks for configuration leaks on startup:

```python
# In main.py
from app.core.test_detection import warn_if_test_config_leaked
warn_if_test_config_leaked()
```

## Database Configuration by Environment

| Environment | Database | Configuration |
|-------------|----------|---------------|
| **Tests** | SQLite (in-memory) | `DB_CLIENT=sqlite`, `DB_HOST=:memory:` |
| **Development** | MySQL | From `.env` file |
| **Production** | MySQL | From environment variables |

## How to Verify Configuration

### 1. Check Current Database

```python
# In Python console or API endpoint
from app.core.config import settings
print(f"Database URL: {settings.database_url}")
```

### 2. Check for Test Overrides

```python
# Check if test overrides are active
from app.main import app
from app.core.database import get_db
print(f"Database overrides: {get_db in app.dependency_overrides}")
```

### 3. Test Environment Detection

```python
from app.core.test_detection import is_running_tests, get_test_indicators
print(f"Running tests: {is_running_tests()}")
print(f"Test indicators: {get_test_indicators()}")
```

## Best Practices

### ✅ DO

1. **Use conditional configuration** in test files
2. **Check environment** before applying test settings
3. **Add warnings** for configuration leaks
4. **Test in isolation** with separate databases
5. **Document configuration** clearly

### ❌ DON'T

1. **Set global environment variables** in test files
2. **Override dependencies globally** without conditions
3. **Import test configuration** in production code
4. **Test against production** databases
5. **Assume test settings** won't leak

## Troubleshooting

### Problem: Development server using SQLite

**Symptoms:**
- API returns data for non-existent users
- Database queries show different data than API
- Authentication works with phantom users

**Solution:**
1. Check for test configuration leaks:
   ```bash
   # Look for these warnings on startup
   ⚠️  WARNING: Test database configuration detected outside of test environment!
   ```

2. Restart the development server:
   ```bash
   # Stop the server and restart
   make down
   make up
   ```

3. Verify database configuration:
   ```bash
   # Check environment variables
   echo $DB_CLIENT  # Should be 'mysql' for development
   echo $DB_HOST    # Should NOT be ':memory:'
   ```

### Problem: Tests failing with MySQL errors

**Symptoms:**
- Tests trying to connect to MySQL
- Database connection errors during tests
- Test data persisting between runs

**Solution:**
1. Ensure test detection is working:
   ```python
   # In conftest.py, add debug output
   print(f"Test detection: {is_running_tests()}")
   ```

2. Check pytest execution:
   ```bash
   # Run tests with verbose output
   make test
   # Should show: "🧪 Test environment detected - configuring SQLite database"
   ```

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── test_detection.py    # Test environment detection
│   │   ├── config.py           # Application configuration
│   │   └── database.py         # Database connection
│   └── main.py                 # Application startup (with leak detection)
├── tests/
│   ├── conftest.py            # Test configuration (conditional)
│   └── test_*.py              # Test files
└── docs/
    └── TESTING_CONFIGURATION.md  # This file
```

## Monitoring

### Startup Checks

The application performs these checks on startup:

1. **Test configuration leak detection**
2. **Database configuration validation**
3. **Environment variable verification**

### Runtime Monitoring

During development, watch for these warnings:

- `⚠️  WARNING: Test database configuration detected outside of test environment!`
- `⚠️  WARNING: Removing existing database override that shouldn't be there!`
- `⚠️  conftest.py imported outside of test environment`

## Emergency Recovery

If test configuration leaks into production:

1. **Immediate action:**
   ```bash
   # Restart the application
   docker-compose restart backend
   ```

2. **Verify environment:**
   ```bash
   # Check environment variables
   docker-compose exec backend env | grep DB_
   ```

3. **Check database connection:**
   ```bash
   # Test database connectivity
   docker-compose exec backend python -c "from app.core.config import settings; print(settings.database_url)"
   ```

## Contact

If you encounter configuration issues:

1. Check this documentation first
2. Look for startup warnings in logs
3. Verify environment variables
4. Test with a fresh restart

Remember: **Test configuration should NEVER affect development or production environments!**
