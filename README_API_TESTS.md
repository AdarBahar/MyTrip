# MyTrips API Test Suite

Complete test scripts to verify your MyTrips backend API from your local machine.

## Files Included

1. **`test_mytrips_api.sh`** - Bash script for quick testing
2. **`test_mytrips_api.py`** - Python script with detailed reporting
3. **`api_test_config.json`** - Configuration file for test scenarios
4. **`README_API_TESTS.md`** - This documentation

## Quick Start

### Option 1: Bash Script (Simple)

```bash
# Make executable
chmod +x test_mytrips_api.sh

# Run tests
./test_mytrips_api.sh
```

### Option 2: Python Script (Detailed)

```bash
# Install requirements (if needed)
pip3 install requests

# Run tests
python3 test_mytrips_api.py

# Run with custom settings
python3 test_mytrips_api.py --api-base https://mytrips-api.bahar.co.il --email your-test@email.com
```

## What Gets Tested

### Core Functionality
- ✅ **Health Check** - API server status
- ✅ **API Documentation** - `/docs` endpoint accessibility
- ✅ **OpenAPI Spec** - `/openapi.json` availability
- ✅ **Authentication** - User login and token generation
- ✅ **Protected Access** - Bearer token validation

### CRUD Operations
- ✅ **Trips** - Create, Read, Update, Delete
- ✅ **Days** - Create, Read, List
- ✅ **Stops** - Create, Read, List
- ✅ **Database Integration** - All operations persist to InMotion database

### Additional Features
- ✅ **Places Search** - Location search functionality
- ✅ **User Settings** - User preferences and settings
- ✅ **Error Handling** - Proper HTTP status codes
- ✅ **Data Cleanup** - Removes test data after completion

## Test Output

### Bash Script Output
```
🚀 MyTrips API Comprehensive Test Suite
========================================
API Base: https://mytrips-api.bahar.co.il
Test Email: test@example.com
Log File: api_test_20241012_162345.log
Started: 2024-10-12 16:23:45

[1] Health Check
✅ PASS: Health endpoint responding
   Response: {"status":"healthy","service":"roadtrip-planner-backend"}

[2] User Authentication
✅ PASS: Authentication successful
   Token: fake_token_abcd1234...

🎯 Test Summary
===============
Total Tests: 12
Passed: 11
Failed: 1
Success Rate: 91%
```

### Python Script Output
```
🚀 MyTrips API Comprehensive Test Suite
==================================================
API Base: https://mytrips-api.bahar.co.il
Test Email: test@example.com
Log File: api_test_20241012_162345.log
Started: 2024-10-12T16:23:45

[1] Health Check
✅ PASS: Health endpoint responding
   Response: {'status': 'healthy', 'service': 'roadtrip-planner-backend'}

🎯 Test Summary
===============
Total Tests: 12
Passed: 11
Failed: 1
Warnings: 0
Success Rate: 91.7%

🎉 All critical tests passed!
Detailed report saved to: api_test_report_20241012_162345.json
```

## Generated Files

### Log Files
- `api_test_YYYYMMDD_HHMMSS.log` - Detailed test execution log
- `api_test_report_YYYYMMDD_HHMMSS.json` - JSON report with all responses (Python only)

### Report Contents
- Test summary and statistics
- All HTTP requests and responses
- Error details and debugging information
- Performance metrics

## Customization

### Change API Base URL
```bash
# Bash
API_BASE="https://your-api.domain.com" ./test_mytrips_api.sh

# Python
python3 test_mytrips_api.py --api-base https://your-api.domain.com
```

### Change Test Email
```bash
# Bash
TEST_EMAIL="your-test@email.com" ./test_mytrips_api.sh

# Python
python3 test_mytrips_api.py --email your-test@email.com
```

### Modify Test Data
Edit `api_test_config.json` to change:
- Trip titles and destinations
- Day dates and titles
- Stop types and details
- Test scenarios

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   curl: (7) Failed to connect to mytrips-api.bahar.co.il port 443
   ```
   - Check if nginx is configured for your domain
   - Verify SSL certificates are working
   - Test with HTTP instead of HTTPS

2. **Authentication Failed**
   ```
   ❌ FAIL: Authentication failed
   ```
   - Check if backend is running
   - Verify database connection
   - Check backend logs: `sudo journalctl -u dayplanner-backend -f`

3. **Database Errors**
   ```
   ❌ FAIL: Trip creation failed
   ```
   - Verify database credentials in `.env.production`
   - Check database connectivity from server
   - Review backend error logs

### Debug Commands

```bash
# Test basic connectivity
curl -I https://mytrips-api.bahar.co.il/health

# Test authentication manually
curl -X POST "https://mytrips-api.bahar.co.il/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Check backend logs
sudo journalctl -u dayplanner-backend -f

# Check nginx logs
sudo tail -f /var/log/nginx/mytrips-api_access.log
sudo tail -f /var/log/nginx/mytrips-api_error.log
```

## Success Criteria

### Critical Tests (Must Pass)
- ✅ Health Check
- ✅ Authentication
- ✅ Protected Access
- ✅ Trip CRUD
- ✅ Day CRUD
- ✅ Stop CRUD

### Optional Tests (May Warn)
- ⚠️ Places Search (requires API keys)
- ⚠️ User Settings (may not be fully implemented)
- ⚠️ Routing Health (requires GraphHopper setup)

## Running Regularly

### Automated Testing
```bash
# Add to crontab for daily testing
0 9 * * * /path/to/test_mytrips_api.py --email daily-test@example.com
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Test API
  run: |
    python3 test_mytrips_api.py --api-base ${{ secrets.API_BASE }}
```

## Support

If tests fail:
1. Check the generated log files for detailed error information
2. Verify your backend service is running: `sudo systemctl status dayplanner-backend`
3. Check database connectivity from your server
4. Review nginx configuration for your domain
5. Examine backend logs for specific error messages

The test scripts are designed to be comprehensive and provide clear feedback on what's working and what needs attention in your API.
