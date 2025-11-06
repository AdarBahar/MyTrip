# Location Tracking API v2.0

A comprehensive location and driving data collection API with offline synchronization support.

## Features

- **Real-time Location Tracking** - Individual location point submission
- **Driving Events** - Trip tracking with start/data/stop events  
- **Batch Synchronization** - Offline data upload with multi-part support
- **Anomaly Detection** - Automatic GPS anomaly detection
- **Data Validation** - Comprehensive input validation
- **Rate Limiting** - Per-IP rate limiting protection
- **CORS Support** - Cross-origin resource sharing enabled
- **Fallback Storage** - Automatic database to file fallback
- **Production Ready** - Security headers, error handling, logging

## Endpoints

### GET `/` - API Information
Returns comprehensive API documentation and status.

### POST `/getloc.php` - Location Data
Submit individual location data points.

**Request:**
```json
{
  "id": "device-12345",
  "name": "john_doe", 
  "latitude": 32.0853,
  "longitude": 34.7818,
  "accuracy": 5.0,
  "timestamp": 1726588200000,
  "speed": 25.3,
  "bearing": 180.0,
  "battery": 85
}
```

### POST `/driving.php` - Driving Events
Submit driving event data (start, data, stop).

**Request:**
```json
{
  "id": "device-12345",
  "name": "john_doe",
  "event": "start",
  "timestamp": 1726588200000,
  "location": {
    "latitude": 32.0853,
    "longitude": 34.7818,
    "accuracy": 5.0
  }
}
```

### POST `/batch-sync.php` - Batch Synchronization
Batch synchronization for offline data.

### GET `/health.php` - Health Check
Simple health check endpoint.

### GET `/ping.php` - Connectivity Test
Minimal endpoint for testing basic connectivity.

## Authentication

All endpoints require authentication using one of these methods (in order of preference):

1. **Bearer Token (Recommended)**
   ```
   Authorization: Bearer {token}
   ```

2. **Bearer Token Alternative (Firewall Bypass)**
   ```
   X-Auth-Token: {token}
   ```

3. **API Key Header (Legacy)**
   ```
   X-API-Token: {token}
   ```

## Rate Limits

- Location: 1000 requests/hour per IP
- Driving: 500 requests/hour per IP  
- Batch Sync: 100 requests/hour per IP

## Response Format

**Success:**
```json
{
  "status": "success",
  "message": "Description of the result",
  "timestamp": "2025-09-23T14:32:52+00:00",
  "data": { ... }
}
```

**Error:**
```json
{
  "status": "error", 
  "message": "Error description",
  "timestamp": "2025-09-23T14:32:52+00:00",
  "error_code": 400,
  "details": { ... }
}
```

## Configuration

Set environment variables in `.env`:

```env
# API Authentication
LOC_API_TOKEN=your-secure-token-here

# CORS Origins
ALLOWED_ORIGINS=mobile,https://yourdomain.com

# Database (optional)
DB_HOST=localhost
DB_NAME=location_tracking
DB_USER=location_user
DB_PASS=secure_password

# Logging
LOC_LOG_DIR=./logs
```

## Storage Modes

1. **Database Mode** - MySQL storage with full features
2. **File Mode** - JSON file storage as fallback

The API automatically falls back to file storage if database is unavailable.

## Testing

```bash
# Test all endpoints
php test-endpoints.php

# Test specific URL
php test-endpoints.php https://your-api-url.com/location/api

# Browser testing
curl -X GET "https://your-api-url.com/location/api/"
```

## Security Features

- Input validation and sanitization
- SQL injection prevention
- XSS protection headers
- Rate limiting
- CORS configuration
- Authentication required
- Error logging

## Deployment

See `DEPLOYMENT.md` for detailed deployment instructions.

## Troubleshooting

### 406 Not Acceptable Error
This indicates ModSecurity is blocking requests. Contact your hosting provider to whitelist the API endpoints.

### 401 Unauthorized
Check your API token in the `.env` file and ensure it matches the token in your requests.

### 500 Internal Server Error
Check the PHP error logs and ensure all dependencies are properly configured.

## Support

- Documentation: `/docs/`
- Health Check: `/health.php`
- Connectivity Test: `/ping.php`
