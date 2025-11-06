# 🚗 Driving API Endpoint Guide

## 📍 **Endpoint**
```
POST https://www.bahar.co.il/location/driving.php
```

## 🔐 **Authentication**
Use the same authentication as the location endpoint:

**Headers:**
```
X-API-Token: your-api-token-here
Content-Type: application/json
```

## 📊 **Event Types**

### 1. **Driving Start** (`driving_start`)
Signals the beginning of a driving trip.

**Request:**
```json
{
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_start",
  "timestamp": "2024-01-15T10:30:00Z",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 10
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Driving trip started",
  "trip_id": "device-001_1705315800",
  "request_id": "abc123...",
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_start"
}
```

### 2. **Driving Data** (`driving_data`)
Continuous location updates during driving.

**Request:**
```json
{
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_data",
  "timestamp": "2024-01-15T10:31:00Z",
  "location": {
    "latitude": 37.7750,
    "longitude": -122.4195,
    "accuracy": 8
  },
  "speed": 45.5,
  "bearing": 180.0,
  "altitude": 100.5
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Driving data received",
  "trip_id": "device-001_1705315800",
  "request_id": "def456...",
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_data"
}
```

### 3. **Driving Stop** (`driving_stop`)
Signals the end of a driving trip with optional summary.

**Request:**
```json
{
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_stop",
  "timestamp": "2024-01-15T11:00:00Z",
  "location": {
    "latitude": 37.7800,
    "longitude": -122.4200,
    "accuracy": 12
  },
  "trip_summary": {
    "duration_seconds": 1800,
    "distance_meters": 15000,
    "avg_speed": 30.0,
    "max_speed": 60.0
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Driving trip stopped",
  "trip_id": "device-001_1705315800",
  "request_id": "ghi789...",
  "id": "device-001",
  "name": "John's Phone",
  "event_type": "driving_stop"
}
```

## 📋 **Field Specifications**

### **Required Fields (All Events):**
- `id` (string, max 100 chars): Unique device identifier
- `name` (string, max 100 chars): Human-readable device name
- `event_type` (string): One of `driving_start`, `driving_data`, `driving_stop`
- `timestamp` (string): ISO 8601 timestamp
- `location` (object): Location data
  - `latitude` (number): -90 to 90
  - `longitude` (number): -180 to 180
  - `accuracy` (number, optional): GPS accuracy in meters

### **Optional Fields for `driving_data`:**
- `speed` (number): Speed in km/h (≥ 0)
- `bearing` (number): Direction in degrees (0-359.9999)
- `altitude` (number): Altitude in meters

### **Optional Fields for `driving_stop`:**
- `trip_summary` (object): Trip statistics
  - `duration_seconds` (number): Trip duration (≥ 0)
  - `distance_meters` (number): Total distance (≥ 0)
  - `avg_speed` (number): Average speed (≥ 0)
  - `max_speed` (number): Maximum speed (≥ 0)

## 🔄 **Trip Session Management**

The API automatically manages trip sessions:

1. **Starting a Trip:**
   - Creates a new session with unique `trip_id`
   - If device already has active trip, returns warning

2. **During Trip:**
   - Updates session timestamp on each `driving_data` event
   - Sessions expire after 1 hour of inactivity

3. **Ending Trip:**
   - Removes session from active trips
   - If no active trip found, returns warning (not error)

## 📱 **Android Integration Example**

```kotlin
// Driving start
val startRequest = DrivingRequest(
    id = "device-001",
    name = "John's Phone",
    eventType = "driving_start",
    timestamp = Instant.now().toString(),
    location = LocationData(37.7749, -122.4194, 10.0)
)

// Driving data (continuous updates)
val dataRequest = DrivingRequest(
    id = "device-001",
    name = "John's Phone",
    eventType = "driving_data",
    timestamp = Instant.now().toString(),
    location = LocationData(37.7750, -122.4195, 8.0),
    speed = 45.5,
    bearing = 180.0,
    altitude = 100.5
)

// Driving stop
val stopRequest = DrivingRequest(
    id = "device-001",
    name = "John's Phone",
    eventType = "driving_stop",
    timestamp = Instant.now().toString(),
    location = LocationData(37.7800, -122.4200, 12.0),
    tripSummary = TripSummary(
        durationSeconds = 1800,
        distanceMeters = 15000,
        avgSpeed = 30.0,
        maxSpeed = 60.0
    )
)

// Send with OkHttp
val request = Request.Builder()
    .url("https://www.bahar.co.il/location/driving.php")
    .post(requestBody)
    .addHeader("Content-Type", "application/json")
    .addHeader("X-API-Token", apiToken)
    .build()
```

## 📁 **Data Storage**

- **Log Files:** `/logs/{sanitized_name}/driving-{name}-{date}.log`
- **Trip Sessions:** `/logs/trip_sessions.json`
- **Security Logs:** `/logs/security.log`

## ⚠️ **Error Responses**

### **Authentication Errors:**
```json
{
  "status": "error",
  "message": "Unauthorized - Bearer token required",
  "hint": "Use Authorization: Bearer TOKEN or X-API-Token: TOKEN header"
}
```

### **Validation Errors:**
```json
{
  "status": "error",
  "message": "Missing or invalid required fields",
  "request_id": "abc123...",
  "details": {
    "id_valid": true,
    "name_valid": true,
    "event_type_valid": false,
    "timestamp_valid": true,
    "location_valid": true
  }
}
```

### **Trip Management Warnings:**
```json
{
  "status": "warning",
  "message": "Trip already active for this device",
  "trip_id": "device-001_1705315800"
}
```

## 🧪 **Testing with Postman**

1. **Set Headers:**
   ```
   X-API-Token: 4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI=
   Content-Type: application/json
   ```

2. **Test Sequence:**
   - Send `driving_start` event
   - Send multiple `driving_data` events
   - Send `driving_stop` event

3. **Verify Responses:**
   - Check `trip_id` consistency
   - Verify `request_id` in all responses
   - Monitor for warnings/errors

## 🔒 **Security Features**

- ✅ Bearer token authentication with shared hosting fallback
- ✅ Request size limits (128KB max)
- ✅ Input validation and sanitization
- ✅ Security event logging
- ✅ CORS protection
- ✅ Rate limiting through authentication

Your driving API is now fully secured and ready for production use! 🚀
