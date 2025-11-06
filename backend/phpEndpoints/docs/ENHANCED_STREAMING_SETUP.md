# Enhanced Real-Time Location Streaming - Setup Guide

## Overview

This guide covers the setup and deployment of the enhanced real-time location streaming system with:

- ✅ **Server-Sent Events (SSE)** for push-based streaming
- ✅ **JWT Session Management** for secure connections
- ✅ **Change Detection** to reduce bandwidth
- ✅ **Duplicate/Stale Detection** for data quality
- ✅ **Dwell/Drive Segmentation** for analytics
- ✅ **Route Simplification** using RDP algorithm

---

## Prerequisites

- PHP 7.4+ with PDO extension
- MySQL/MariaDB database
- Existing location tracking system (v2.0+)
- APCu extension (optional, for better performance)

---

## Installation Steps

### Step 1: Run Database Migration

Execute the SQL migration to create new tables:

```bash
mysql -h HOST -u USER -p DATABASE < database-migrations/add-enhanced-streaming.sql
```

**Tables Created:**
- `streaming_session_tokens` - JWT session management
- `location_change_log` - Change detection logging (optional)

**Indexes Added:**
- `idx_device_server_time` on `device_last_position`
- `idx_server_time` on `location_history_cache`

### Step 2: Deploy Backend Files

Upload these new files to your server:

```
shared/classes/
├── JwtSessionManager.php       (NEW - JWT session management)
├── ChangeDetector.php           (NEW - Change detection logic)
├── DuplicateDetector.php        (NEW - Duplicate/stale detection)
└── LocationAnalyzer.php         (NEW - Dwell/drive analysis)

api/live/
├── session.php                  (NEW - Create/revoke sessions)
└── stream-sse.php               (NEW - SSE streaming endpoint)
```

**Updated Files:**
```
api/
├── getloc.php                   (UPDATED - Added duplicate/stale detection)
└── live/history.php             (UPDATED - Added segment analysis)
```

### Step 3: Configure Environment

Add these environment variables to your `.env` or configuration:

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_SESSION_DURATION=3600

# Change Detection Thresholds
CHANGE_DETECTION_DISTANCE_THRESHOLD=20
CHANGE_DETECTION_TIME_THRESHOLD=300
CHANGE_DETECTION_SPEED_THRESHOLD=5
CHANGE_DETECTION_BEARING_THRESHOLD=15

# Duplicate Detection
DUPLICATE_DETECTION_TTL=300

# Stale Detection
STALE_DETECTION_MAX_AGE=300

# Dwell Detection
DWELL_RADIUS_METERS=50
DWELL_MIN_DURATION_SECONDS=300
```

### Step 4: Test the Installation

Run the test script:

```bash
php test-enhanced-streaming.php
```

Expected output:
```
✅ Database Connection - PASS
✅ Table: streaming_session_tokens - PASS
✅ Table: location_change_log - PASS
✅ Class: JwtSessionManager - PASS
✅ Class: ChangeDetector - PASS
✅ Class: DuplicateDetector - PASS
✅ Class: LocationAnalyzer - PASS
✅ Session Creation - PASS
✅ Token Validation - PASS
✅ Change Detection - PASS
✅ Duplicate Detection - PASS
✅ Dwell Detection - PASS
```

---

## Usage Examples

### 1. Create Streaming Session

**Request:**
```bash
curl -X POST 'https://your-domain.com/location/api/live/session' \
  -H 'X-API-Token: YOUR_API_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "device_ids": ["device_123"],
    "duration": 3600
  }'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "sess_abc123...",
    "session_token": "eyJhbGc...",
    "expires_at": "2025-10-28T17:00:00Z",
    "duration": 3600,
    "stream_url": "/api/live/stream-sse.php?token=eyJhbGc...",
    "device_ids": ["device_123"]
  }
}
```

### 2. Stream Locations (SSE)

**JavaScript Client:**
```javascript
// Create session first
const sessionResponse = await fetch('/api/live/session', {
  method: 'POST',
  headers: {
    'X-API-Token': 'YOUR_API_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    device_ids: ['device_123'],
    duration: 3600
  })
});

const session = await sessionResponse.json();
const token = session.data.session_token;

// Connect to SSE stream
const eventSource = new EventSource(`/api/live/stream-sse.php?token=${token}`);

// Handle connection
eventSource.addEventListener('connected', (e) => {
  const data = JSON.parse(e.data);
  console.log('Connected:', data);
});

// Handle location updates
eventSource.addEventListener('loc', (e) => {
  const location = JSON.parse(e.data);
  console.log('New location:', location);
  
  // Update map
  updateMarker(location.device_id, {
    lat: location.latitude,
    lng: location.longitude,
    speed: location.speed,
    bearing: location.bearing
  });
  
  // Show change reason
  console.log('Change reason:', location.change_reason);
  console.log('Metrics:', location.change_metrics);
});

// Handle heartbeat (no change)
eventSource.addEventListener('no_change', (e) => {
  const data = JSON.parse(e.data);
  console.log('Heartbeat - Active devices:', data.active_devices);
});

// Handle connection close
eventSource.addEventListener('bye', (e) => {
  const data = JSON.parse(e.data);
  console.log('Connection closed:', data.reason);
  eventSource.close();
});

// Handle errors
eventSource.addEventListener('error', (e) => {
  console.error('SSE error:', e);
});
```

### 3. Get History with Segments

**Request:**
```bash
curl -X GET 'https://your-domain.com/location/api/live/history.php?device=device_123&duration=86400&segments=true' \
  -H 'X-API-Token: YOUR_API_TOKEN'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "points": [...],
    "count": 1250,
    "segments": {
      "dwells": [
        {
          "center": {
            "latitude": 32.0853,
            "longitude": 34.7818
          },
          "start_time": 1698761832000,
          "end_time": 1698762132000,
          "duration_seconds": 300,
          "point_count": 15,
          "radius_meters": 50
        }
      ],
      "drives": [
        {
          "start_time": 1698762132000,
          "end_time": 1698763432000,
          "duration_seconds": 1300,
          "distance_meters": 5420,
          "avg_speed_kmh": 45,
          "point_count": 120,
          "simplified_point_count": 25,
          "simplified_points": [...]
        }
      ],
      "dwell_count": 3,
      "drive_count": 2
    }
  }
}
```

### 4. Revoke Session

**Request:**
```bash
curl -X DELETE 'https://your-domain.com/location/api/live/session/sess_abc123' \
  -H 'X-API-Token: YOUR_API_TOKEN'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "sess_abc123",
    "revoked": true
  }
}
```

---

## Features Explained

### Change Detection

The system only emits location updates when significant changes occur:

- **Distance:** > 20 meters from last emitted location
- **Time:** > 5 minutes since last emission
- **Speed:** > 5 km/h change in speed
- **Bearing:** > 15° change in direction

**Benefits:**
- Reduces bandwidth by ~70%
- Reduces client-side processing
- Maintains data quality

### Duplicate Detection

Prevents processing the same location data multiple times:

- Uses hash of (device_id, lat, lng, timestamp)
- Stores recent hashes in APCu or session
- Returns success but skips processing (idempotent)

### Stale Detection

Rejects location data that is too old:

- Default threshold: 5 minutes
- Compares client_time with server_time
- Logs stale data for debugging

### Dwell Detection

Identifies periods where device stayed in one place:

- Default radius: 50 meters
- Minimum duration: 5 minutes
- Calculates average center point
- Counts points in dwell

### Drive Segmentation

Identifies movement periods between dwells:

- Calculates total distance
- Calculates average speed
- Simplifies route using RDP algorithm
- Reduces points by ~80% while maintaining shape

---

## Performance Considerations

### APCu Extension

For best performance, install APCu:

```bash
# Ubuntu/Debian
sudo apt-get install php-apcu

# Enable in php.ini
apc.enabled=1
apc.shm_size=32M
```

### Database Indexes

Ensure indexes are created:

```sql
SHOW INDEX FROM device_last_position;
SHOW INDEX FROM location_history_cache;
SHOW INDEX FROM streaming_session_tokens;
```

### Connection Limits

SSE connections are long-lived. Configure your server:

**Nginx:**
```nginx
location /api/live/stream-sse.php {
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 3600s;
    proxy_connect_timeout 3600s;
}
```

**Apache:**
```apache
<Location /api/live/stream-sse.php>
    ProxyPass http://localhost:8080/api/live/stream-sse.php
    ProxyPassReverse http://localhost:8080/api/live/stream-sse.php
    ProxyTimeout 3600
</Location>
```

---

## Troubleshooting

### SSE Connection Drops

**Problem:** SSE connection closes immediately

**Solutions:**
1. Check JWT token is valid
2. Verify database connection
3. Check server buffering settings
4. Review error logs

### No Location Updates

**Problem:** Connected but no `loc` events

**Solutions:**
1. Verify change detection thresholds
2. Check if device is actually moving
3. Review `location_change_log` table
4. Test with lower thresholds

### High Memory Usage

**Problem:** PHP memory usage increases over time

**Solutions:**
1. Enable APCu for caching
2. Reduce session duration
3. Limit concurrent connections
4. Clean up expired sessions regularly

---

## Next Steps

1. ✅ Deploy to production
2. ✅ Test with real mobile devices
3. ✅ Monitor performance metrics
4. ✅ Adjust thresholds based on usage
5. ✅ Implement Redis pub/sub (optional, for scaling)

---

## Support

For issues or questions:
- Review logs in `/var/log/php-errors.log`
- Check database for errors
- Test with simulator: `./simulate.sh 1`
- Review architecture: `docs/ENHANCED_REALTIME_ARCHITECTURE.md`

