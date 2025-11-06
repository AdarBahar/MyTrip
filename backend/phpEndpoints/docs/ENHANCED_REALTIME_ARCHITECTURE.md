# Enhanced Real-Time Location Tracking Architecture

## Overview

This document describes the enhanced real-time location tracking system with:
- **Server-Sent Events (SSE)** for push-based streaming
- **Change detection** to reduce unnecessary updates
- **Duplicate/stale detection** for data quality
- **Dwell/Drive segmentation** for analytics
- **JWT session management** for secure streaming
- **Redis pub/sub** (optional) for horizontal scaling

---

## Architecture Components

### 1. Data Ingestion Layer

**Endpoint:** `POST /api/getloc.php`

**Responsibilities:**
- Validate incoming location data
- Detect duplicates and stale updates
- Store in `location_records` (permanent)
- Update `device_last_position` (current state)
- Insert into `location_history_cache` (24h window)
- **NEW:** Publish to streaming layer (Redis/in-memory)
- **NEW:** Apply change detection before publishing

**Flow:**
```
Mobile App → POST /getloc.php
    ↓
Validate & Sanitize
    ↓
Duplicate Detection ← Check last location
    ↓
Store in Database (3 tables)
    ↓
Change Detection ← Compare with last emitted
    ↓
Publish to Stream ← Only if changed
```

---

### 2. Streaming Layer

**Endpoint:** `GET /api/live/stream-sse.php`

**Technology:** Server-Sent Events (SSE)

**Responsibilities:**
- Authenticate via JWT session token
- Maintain persistent connection
- Subscribe to location updates for specific users/devices
- Emit events: `loc`, `no_change`, `bye`
- Auto-close on session expiry or client disconnect

**Event Types:**
```javascript
// Location changed
event: loc
data: {"device_id":"...", "latitude":32.08, "longitude":34.78, ...}

// Location stable (heartbeat)
event: no_change
data: {"device_id":"...", "last_update":"2025-10-28T16:00:00Z"}

// Connection closing
event: bye
data: {"reason":"session_expired"}
```

**Flow:**
```
UI Client → GET /live/stream-sse.php?token=JWT
    ↓
Validate JWT & Create Session
    ↓
Subscribe to Updates (Redis/Memory)
    ↓
Keep Connection Open
    ↓
Emit Events on Change
    ↓
Close on Disconnect/Expiry
```

---

### 3. Change Detection Logic

**Purpose:** Reduce bandwidth and processing by only emitting significant changes

**Thresholds:**
- **Distance:** > 20 meters (configurable)
- **Time:** > 5 minutes since last change (configurable)
- **Speed:** > 10% change in speed
- **Bearing:** > 15° change in direction

**Algorithm:**
```php
function shouldEmitLocation($newLoc, $lastEmitted) {
    // Always emit first location
    if (!$lastEmitted) return true;
    
    // Calculate distance
    $distance = haversineDistance($newLoc, $lastEmitted);
    if ($distance > DISTANCE_THRESHOLD) return true;
    
    // Check time elapsed
    $timeDiff = $newLoc['timestamp'] - $lastEmitted['timestamp'];
    if ($timeDiff > TIME_THRESHOLD) return true;
    
    // Check speed change
    $speedChange = abs($newLoc['speed'] - $lastEmitted['speed']);
    if ($speedChange > SPEED_THRESHOLD) return true;
    
    // Check bearing change
    $bearingChange = abs($newLoc['bearing'] - $lastEmitted['bearing']);
    if ($bearingChange > BEARING_THRESHOLD) return true;
    
    return false; // No significant change
}
```

---

### 4. Duplicate & Stale Detection

**Purpose:** Prevent storing/emitting duplicate or outdated data

**Duplicate Detection:**
- Check if exact same coordinates + timestamp already exist
- Use hash of (device_id, lat, lng, timestamp)
- Store recent hashes in Redis (TTL: 5 minutes)

**Stale Detection:**
- Reject updates older than 5 minutes (configurable)
- Compare `client_time` with `server_time`
- Log stale updates for debugging

**Implementation:**
```php
function isDuplicate($deviceId, $location) {
    $hash = md5($deviceId . $location['latitude'] . 
                $location['longitude'] . $location['client_time']);
    
    // Check Redis cache
    if (Redis::exists("loc:hash:$hash")) {
        return true;
    }
    
    // Store hash with 5-minute TTL
    Redis::setex("loc:hash:$hash", 300, 1);
    return false;
}

function isStale($location) {
    $clientTime = $location['client_time'] / 1000; // Convert ms to seconds
    $serverTime = time();
    $age = $serverTime - $clientTime;
    
    return $age > 300; // 5 minutes
}
```

---

### 5. Session Management (JWT)

**Purpose:** Secure, short-lived tokens for streaming connections

**Token Structure:**
```json
{
  "sub": "user_123",
  "device_ids": ["device_1", "device_2"],
  "exp": 1698765432,
  "iat": 1698761832,
  "jti": "session_abc123"
}
```

**Endpoints:**

**Create Session:**
```
POST /api/live/session
Authorization: Bearer <API_TOKEN>
Body: {"device_ids": ["device_1"], "duration": 3600}

Response:
{
  "session_token": "eyJhbGc...",
  "expires_at": "2025-10-28T17:00:00Z",
  "stream_url": "/api/live/stream-sse.php?token=eyJhbGc..."
}
```

**Stream with Session:**
```
GET /api/live/stream-sse.php?token=<JWT>
```

**Revoke Session:**
```
DELETE /api/live/session/<session_id>
```

---

### 6. History & Analytics

**Endpoint:** `GET /api/live/history.php` (enhanced)

**New Features:**
- **Dwell Detection:** Identify periods where device stayed in one place
- **Drive Segmentation:** Identify movement between dwells
- **Route Simplification:** Use Ramer-Douglas-Peucker algorithm to reduce points

**Dwell Detection:**
```php
function detectDwells($locations, $radiusMeters = 50, $minDurationSec = 300) {
    $dwells = [];
    $currentDwell = null;
    
    foreach ($locations as $loc) {
        if (!$currentDwell) {
            $currentDwell = [
                'center' => $loc,
                'start_time' => $loc['timestamp'],
                'points' => [$loc]
            ];
            continue;
        }
        
        $distance = haversineDistance($currentDwell['center'], $loc);
        
        if ($distance <= $radiusMeters) {
            // Still in dwell
            $currentDwell['points'][] = $loc;
            $currentDwell['end_time'] = $loc['timestamp'];
        } else {
            // Left dwell area
            $duration = $currentDwell['end_time'] - $currentDwell['start_time'];
            if ($duration >= $minDurationSec) {
                $dwells[] = $currentDwell;
            }
            $currentDwell = null;
        }
    }
    
    return $dwells;
}
```

**Drive Segmentation:**
```php
function segmentDrives($locations, $dwells) {
    $drives = [];
    $dwellTimes = array_map(fn($d) => $d['start_time'], $dwells);
    
    $currentDrive = null;
    foreach ($locations as $loc) {
        $inDwell = false;
        foreach ($dwells as $dwell) {
            if ($loc['timestamp'] >= $dwell['start_time'] && 
                $loc['timestamp'] <= $dwell['end_time']) {
                $inDwell = true;
                break;
            }
        }
        
        if (!$inDwell) {
            if (!$currentDrive) {
                $currentDrive = ['points' => []];
            }
            $currentDrive['points'][] = $loc;
        } else {
            if ($currentDrive && count($currentDrive['points']) > 1) {
                $drives[] = $currentDrive;
            }
            $currentDrive = null;
        }
    }
    
    return $drives;
}
```

---

## Database Schema Enhancements

### New Table: `location_change_log`

Tracks when locations were emitted to streams (for debugging):

```sql
CREATE TABLE location_change_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_id VARCHAR(100) NOT NULL,
    location_id BIGINT NOT NULL,
    change_type ENUM('distance', 'time', 'speed', 'bearing', 'first') NOT NULL,
    distance_meters FLOAT NULL,
    time_diff_seconds INT NULL,
    emitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_device_time (device_id, emitted_at),
    FOREIGN KEY (location_id) REFERENCES location_records(id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

### New Table: `streaming_session_tokens`

Stores JWT sessions:

```sql
CREATE TABLE streaming_session_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(50) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    device_ids JSON NULL,
    token_hash VARCHAR(64) NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked BOOLEAN DEFAULT FALSE,
    
    INDEX idx_session (session_id),
    INDEX idx_expires (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

---

## Implementation Plan

### Phase 1: Core Infrastructure
1. ✅ Analyze current architecture
2. Create JWT session management class
3. Create change detection utility class
4. Create duplicate detection utility class

### Phase 2: Streaming Endpoint
5. Implement `/api/live/session` (create/revoke JWT)
6. Implement `/api/live/stream-sse.php` (SSE streaming)
7. Add Redis pub/sub support (optional)

### Phase 3: Enhanced Ingestion
8. Update `/api/getloc.php` with duplicate detection
9. Update `/api/getloc.php` with stale detection
10. Add change detection before publishing

### Phase 4: Analytics
11. Enhance `/api/live/history.php` with dwell detection
12. Add drive segmentation
13. Add route simplification (RDP algorithm)

### Phase 5: Testing & Deployment
14. Test with simulator
15. Update documentation
16. Deploy to production

---

## Configuration

**Environment Variables:**

```env
# Change Detection
CHANGE_DETECTION_DISTANCE_THRESHOLD=20  # meters
CHANGE_DETECTION_TIME_THRESHOLD=300     # seconds (5 min)
CHANGE_DETECTION_SPEED_THRESHOLD=5      # km/h
CHANGE_DETECTION_BEARING_THRESHOLD=15   # degrees

# Duplicate Detection
DUPLICATE_DETECTION_TTL=300             # seconds (5 min)

# Stale Detection
STALE_DETECTION_MAX_AGE=300             # seconds (5 min)

# Session Management
JWT_SECRET_KEY=your-secret-key-here
JWT_SESSION_DURATION=3600               # seconds (1 hour)
JWT_MAX_SESSIONS_PER_USER=5

# Dwell Detection
DWELL_RADIUS_METERS=50
DWELL_MIN_DURATION_SECONDS=300          # 5 minutes

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

---

## API Examples

### Create Streaming Session

```bash
curl -X POST 'https://www.bahar.co.il/location/api/live/session' \
  -H 'X-API-Token: YOUR_API_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "device_ids": ["device_aa9e19da71fc702b"],
    "duration": 3600
  }'
```

### Stream Locations (SSE)

```javascript
const token = 'eyJhbGc...'; // From session creation
const eventSource = new EventSource(`/api/live/stream-sse.php?token=${token}`);

eventSource.addEventListener('loc', (e) => {
  const location = JSON.parse(e.data);
  console.log('New location:', location);
  updateMap(location);
});

eventSource.addEventListener('no_change', (e) => {
  console.log('Location stable:', e.data);
});

eventSource.addEventListener('bye', (e) => {
  console.log('Stream closed:', e.data);
  eventSource.close();
});
```

### Get History with Segments

```bash
curl -X GET 'https://www.bahar.co.il/location/api/live/history.php?device=device_123&duration=86400&segments=true' \
  -H 'X-API-Token: YOUR_API_TOKEN'
```

Response:
```json
{
  "status": "success",
  "data": {
    "points": [...],
    "dwells": [
      {
        "center": {"latitude": 32.08, "longitude": 34.78},
        "start_time": 1698761832000,
        "end_time": 1698762132000,
        "duration_seconds": 300,
        "point_count": 15
      }
    ],
    "drives": [
      {
        "start_time": 1698762132000,
        "end_time": 1698763432000,
        "distance_meters": 5420,
        "avg_speed_kmh": 45,
        "point_count": 120,
        "simplified_points": [...]  // RDP simplified
      }
    ]
  }
}
```

---

## Next Steps

1. Review and approve architecture
2. Begin implementation with Phase 1
3. Test each phase before moving to next
4. Deploy incrementally to production

