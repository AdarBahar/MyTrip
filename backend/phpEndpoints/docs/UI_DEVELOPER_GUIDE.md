# 📱 UI Developer Guide - New API Endpoints

## 🎯 Overview

Three new **read-only GET endpoints** have been added to replace direct database access in the dashboard. These endpoints provide secure, authenticated access to user, location, and driving data with comprehensive filtering and pagination support.

---

## 🔐 Authentication

All endpoints require authentication using one of these methods:

### Method 1: Bearer Token (Recommended)
```javascript
headers: {
    'Authorization': 'Bearer YOUR_API_TOKEN'
}
```

### Method 2: X-API-Token Header
```javascript
headers: {
    'X-API-Token': 'YOUR_API_TOKEN'
}
```

### Method 3: X-Auth-Token Header
```javascript
headers: {
    'X-Auth-Token': 'YOUR_API_TOKEN'
}
```

**Get your API token from:** `.env` file → `LOC_API_TOKEN` variable

---

## 📍 Base URLs

- **Production:** `https://www.bahar.co.il/location/api`
- **Local (MAMP):** `http://localhost:8888/location/api`

---

## 🔗 Endpoints

### **Data Retrieval Endpoints**

### 1️⃣ **GET /users.php** - Get Users with Location Data

Returns a list of users who have location data, with optional counts and metadata.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `with_location_data` | boolean | `true` | Only return users with location records |
| `include_counts` | boolean | `false` | Include location_count and driving_count |
| `include_metadata` | boolean | `false` | Include last_location_time and last_driving_time |

#### **Example Request:**

```javascript
// Basic request - get all users with location data
const response = await fetch('https://www.bahar.co.il/location/api/users.php', {
    headers: {
        'Authorization': 'Bearer YOUR_API_TOKEN'
    }
});
const data = await response.json();
```

```javascript
// With counts and metadata
const response = await fetch(
    'https://www.bahar.co.il/location/api/users.php?include_counts=true&include_metadata=true',
    {
        headers: {
            'Authorization': 'Bearer YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

#### **Response Format:**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "username": "john_doe",
            "display_name": "John Doe",
            "created_at": "2024-01-15 10:30:00",
            "location_count": 1250,
            "driving_count": 45,
            "last_location_time": "2024-10-26 14:30:00",
            "last_driving_time": "2024-10-25 09:15:00"
        }
    ],
    "count": 5,
    "source": "database",
    "timestamp": "2024-10-27T10:30:00Z"
}
```

---

### 2️⃣ **GET /locations.php** - Get Location Records with Filters

Returns location records with comprehensive filtering options including date range, accuracy, anomaly status, and geographic radius search.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Filter by username |
| `date_from` | datetime | - | Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) |
| `date_to` | datetime | - | End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) |
| `accuracy_max` | float | - | Maximum accuracy in meters |
| `anomaly_status` | enum | - | Filter by status: `marked`, `suspected`, `normal`, `confirmed` |
| `lat` | float | - | Latitude for radius search |
| `lng` | float | - | Longitude for radius search |
| `radius` | float | `100` | Search radius in meters (requires lat/lng) |
| `limit` | integer | `1000` | Max records to return (max: 10000) |
| `offset` | integer | `0` | Pagination offset |
| `include_anomaly_status` | boolean | `true` | Include anomaly information |

#### **Example Requests:**

```javascript
// Get all locations for a specific user
const response = await fetch(
    'https://www.bahar.co.il/location/api/locations.php?user=john_doe',
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Get locations with date range and accuracy filter
const params = new URLSearchParams({
    user: 'john_doe',
    date_from: '2024-10-01',
    date_to: '2024-10-27',
    accuracy_max: '20',
    limit: '500'
});

const response = await fetch(
    `https://www.bahar.co.il/location/api/locations.php?${params}`,
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Geographic radius search - find locations within 500m of a point
const params = new URLSearchParams({
    lat: '32.0853',
    lng: '34.7818',
    radius: '500',
    limit: '100'
});

const response = await fetch(
    `https://www.bahar.co.il/location/api/locations.php?${params}`,
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Filter by anomaly status
const response = await fetch(
    'https://www.bahar.co.il/location/api/locations.php?anomaly_status=marked&user=john_doe',
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

#### **Response Format:**

```json
{
    "success": true,
    "data": [
        {
            "id": 12345,
            "device_id": "device-12345",
            "user_id": 1,
            "username": "john_doe",
            "display_name": "John Doe",
            "server_time": "2024-10-27 10:30:00",
            "client_time": 1726588200000,
            "latitude": 32.0853,
            "longitude": 34.7818,
            "accuracy": 5.0,
            "altitude": 100.5,
            "speed": 25.3,
            "bearing": 180.0,
            "battery_level": 85,
            "anomaly_status": "normal",
            "marked_by_user": 0
        }
    ],
    "count": 100,
    "total": 1250,
    "limit": 1000,
    "offset": 0,
    "source": "database",
    "timestamp": "2024-10-27T10:30:00Z"
}
```

---

### 3️⃣ **GET /driving-records.php** - Get Driving Records with Filters

Returns driving records with filtering by user, date range, event type, and trip ID.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Filter by username |
| `date_from` | datetime | - | Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) |
| `date_to` | datetime | - | End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) |
| `event_type` | enum | - | Filter by type: `start`, `data`, `stop` |
| `trip_id` | string | - | Filter by specific trip ID |
| `limit` | integer | `1000` | Max records to return (max: 10000) |
| `offset` | integer | `0` | Pagination offset |

#### **Example Requests:**

```javascript
// Get all driving records for a user
const response = await fetch(
    'https://www.bahar.co.il/location/api/driving-records.php?user=john_doe',
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Get driving records with date range
const params = new URLSearchParams({
    user: 'john_doe',
    date_from: '2024-10-01',
    date_to: '2024-10-27',
    limit: '500'
});

const response = await fetch(
    `https://www.bahar.co.il/location/api/driving-records.php?${params}`,
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Get only trip start events
const response = await fetch(
    'https://www.bahar.co.il/location/api/driving-records.php?user=john_doe&event_type=start',
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

```javascript
// Get all records for a specific trip
const response = await fetch(
    'https://www.bahar.co.il/location/api/driving-records.php?trip_id=trip-abc123',
    {
        headers: {
            'X-API-Token': 'YOUR_API_TOKEN'
        }
    }
);
const data = await response.json();
```

#### **Response Format:**

```json
{
    "success": true,
    "data": [
        {
            "id": 456,
            "device_id": "device-12345",
            "user_id": 1,
            "username": "john_doe",
            "display_name": "John Doe",
            "server_time": "2024-10-27 10:30:00",
            "client_time": 1726588200000,
            "event_type": "start",
            "trip_id": "trip-abc123",
            "latitude": 32.0853,
            "longitude": 34.7818,
            "accuracy": 5.0,
            "speed": 25.3,
            "bearing": 180.0
        }
    ],
    "count": 50,
    "total": 150,
    "limit": 1000,
    "offset": 0,
    "source": "database",
    "timestamp": "2024-10-27T10:30:00Z"
}
```

---

### **Live Tracking Endpoints**

### 4️⃣ **GET /live/latest.php** - Get Latest Locations

Returns the most recent location for specified user(s) or device(s). Perfect for "where is everyone now" dashboards.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Single username or comma-separated list |
| `users[]` | array | - | Array of usernames |
| `device` | string | - | Single device ID or comma-separated list |
| `devices[]` | array | - | Array of device IDs |
| `all` | boolean | `false` | Get latest for all active users |
| `max_age` | integer | `3600` | Maximum age in seconds (default: 1 hour) |
| `include_inactive` | boolean | `false` | Include users with no recent location |

#### **Example Requests:**

```javascript
// Get latest location for single user
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/latest.php?user=john_doe',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
const data = await response.json();
```

```javascript
// Get latest for multiple users
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/latest.php?user=john_doe,jane_smith',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
```

```javascript
// Get latest for all users (last 5 minutes)
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/latest.php?all=true&max_age=300',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
```

#### **Response Format:**

```json
{
  "success": true,
  "data": {
    "locations": [
      {
        "device_id": "device-12345",
        "user_id": 1,
        "username": "john_doe",
        "display_name": "John Doe",
        "latitude": 32.0853,
        "longitude": 34.7818,
        "accuracy": 5.0,
        "speed": 25.3,
        "battery_level": 85,
        "server_time": "2024-10-27 14:30:00",
        "age_seconds": 120,
        "is_recent": true
      }
    ],
    "count": 1,
    "max_age": 3600
  }
}
```

---

### 5️⃣ **GET /live/stream.php** - Live Location Stream (Polling)

Returns new location updates since a given cursor. Designed for efficient polling (every 3-5 seconds) to build real-time tracking dashboards.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Single username or comma-separated list |
| `users[]` | array | - | Array of usernames |
| `device` | string | - | Single device ID or comma-separated list |
| `devices[]` | array | - | Array of device IDs |
| `all` | boolean | `false` | Stream all users |
| `since` | integer | `0` | Cursor timestamp in milliseconds |
| `limit` | integer | `100` | Max records (max: 500) |
| `session_id` | string | - | Optional session tracking ID |

#### **Example Requests:**

```javascript
// Initial request - get all points
let cursor = 0;
const response = await fetch(
    `https://www.bahar.co.il/location/api/live/stream.php?user=john_doe&since=${cursor}`,
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
const data = await response.json();

// Update cursor for next poll
cursor = data.data.cursor;
```

```javascript
// Polling implementation
class LiveTracker {
    constructor(apiToken, users) {
        this.apiToken = apiToken;
        this.users = users.join(',');
        this.cursor = 0;
        this.interval = null;
    }

    async poll() {
        const response = await fetch(
            `https://www.bahar.co.il/location/api/live/stream.php?user=${this.users}&since=${this.cursor}`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );

        const data = await response.json();

        if (data.success && data.data.points.length > 0) {
            // Process new points
            this.onNewPoints(data.data.points);

            // Update cursor
            this.cursor = data.data.cursor;
        }
    }

    start(onNewPoints) {
        this.onNewPoints = onNewPoints;
        this.interval = setInterval(() => this.poll(), 3000); // Poll every 3 seconds
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Usage
const tracker = new LiveTracker('YOUR_API_TOKEN', ['john_doe', 'jane_smith']);
tracker.start((points) => {
    console.log('New points:', points);
    // Update map with new points
});

// Stop tracking when done
// tracker.stop();
```

#### **Response Format:**

```json
{
  "success": true,
  "data": {
    "points": [
      {
        "device_id": "device-12345",
        "user_id": 1,
        "username": "john_doe",
        "latitude": 32.0853,
        "longitude": 34.7818,
        "accuracy": 5.0,
        "server_time": "2024-10-27 14:30:00",
        "server_timestamp": 1729950600000
      }
    ],
    "cursor": 1729950600000,
    "has_more": false,
    "count": 1
  }
}
```

---

### 6️⃣ **GET /live/history.php** - Tracking History

Returns recent tracking history from the cache table. Useful for "replay" functionality or showing recent path.

#### **Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Single username or comma-separated list |
| `users[]` | array | - | Array of usernames |
| `device` | string | - | Single device ID or comma-separated list |
| `devices[]` | array | - | Array of device IDs |
| `all` | boolean | `false` | Get history for all users |
| `duration` | integer | `3600` | Time window in seconds (max: 86400 = 24h) |
| `limit` | integer | `500` | Max records (max: 5000) |
| `offset` | integer | `0` | Pagination offset |

#### **Example Requests:**

```javascript
// Get last hour of tracking for a user
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/history.php?user=john_doe&duration=3600',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
const data = await response.json();
```

```javascript
// Get last 6 hours for multiple users
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/history.php?user=john_doe,jane_smith&duration=21600',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
```

```javascript
// Paginated history
const response = await fetch(
    'https://www.bahar.co.il/location/api/live/history.php?user=john_doe&duration=86400&limit=100&offset=0',
    {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    }
);
```

#### **Response Format:**

```json
{
  "success": true,
  "data": {
    "points": [
      {
        "device_id": "device-12345",
        "user_id": 1,
        "username": "john_doe",
        "latitude": 32.0853,
        "longitude": 34.7818,
        "server_time": "2024-10-27 14:30:00"
      }
    ],
    "count": 100,
    "total": 450,
    "limit": 100,
    "offset": 0,
    "duration": 3600,
    "source": "cache"
  }
}
```

---

## 🔄 Pagination

All endpoints support pagination using `limit` and `offset` parameters:

```javascript
// Get first page (records 0-99)
const page1 = await fetch(
    'https://www.bahar.co.il/location/api/locations.php?user=john_doe&limit=100&offset=0',
    { headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' } }
);

// Get second page (records 100-199)
const page2 = await fetch(
    'https://www.bahar.co.il/location/api/locations.php?user=john_doe&limit=100&offset=100',
    { headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' } }
);
```

**Response includes pagination info:**
- `count`: Number of records in current response
- `total`: Total records matching filters
- `limit`: Current limit value
- `offset`: Current offset value

---

## ⚠️ Error Handling

All endpoints return standardized error responses:

```json
{
    "success": false,
    "error": "Error message here",
    "timestamp": "2024-10-27T10:30:00Z"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (missing or invalid API token)
- `429` - Rate Limit Exceeded (max 1000 requests/hour)
- `500` - Internal Server Error
- `503` - Service Unavailable (database not available)

**Example Error Handling:**

```javascript
try {
    const response = await fetch(url, {
        headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
    });
    
    const data = await response.json();
    
    if (!response.ok || !data.success) {
        console.error('API Error:', data.error);
        // Handle error
        return;
    }
    
    // Process successful response
    console.log('Data:', data.data);
    
} catch (error) {
    console.error('Network Error:', error);
    // Handle network error
}
```

---

## 🧪 Testing

### Interactive Testing Interfaces

#### **Data Retrieval Endpoints**
Use the web-based testing interface to explore the data endpoints:

- **Production:** https://www.bahar.co.il/location/api/test-endpoints.html
- **Local:** http://localhost:8888/location/api/test-endpoints.html

#### **Live Tracking Endpoints**
Use the live tracking test interface with auto-polling functionality:

- **Production:** https://www.bahar.co.il/location/api/test-live-endpoints.html
- **Local:** http://localhost:8888/location/api/test-live-endpoints.html

### Swagger UI Documentation

Full interactive API documentation with "Try it out" functionality:

- **Production:** https://www.bahar.co.il/location/api/docs/
- **Local:** http://localhost:8888/location/api/docs/

---

## 📊 Rate Limiting

- **Limit:** 1000 requests per hour per IP address
- **Applies to:** All read endpoints (users, locations, driving-records)
- **Response when exceeded:** HTTP 429 with error message

**Best Practices:**
- Cache responses when possible
- Use pagination to reduce request size
- Implement exponential backoff on rate limit errors

---

## 🚀 Complete Example - Building a User Dashboard

```javascript
class LocationDashboard {
    constructor(apiToken, baseUrl = 'https://www.bahar.co.il/location/api') {
        this.apiToken = apiToken;
        this.baseUrl = baseUrl;
    }
    
    async fetchWithAuth(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `${this.baseUrl}${endpoint}${queryString ? '?' + queryString : ''}`;

        const response = await fetch(url, {
            headers: {
                'X-API-Token': this.apiToken
            }
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'API request failed');
        }

        return data;
    }
    
    async getUsers(options = {}) {
        return this.fetchWithAuth('/users.php', options);
    }
    
    async getLocations(filters = {}) {
        return this.fetchWithAuth('/locations.php', filters);
    }
    
    async getDrivingRecords(filters = {}) {
        return this.fetchWithAuth('/driving-records.php', filters);
    }
    
    async getUserDashboard(username) {
        // Get user with counts
        const users = await this.getUsers({
            include_counts: true,
            include_metadata: true
        });
        
        const user = users.data.find(u => u.username === username);
        
        if (!user) {
            throw new Error('User not found');
        }
        
        // Get recent locations (last 100)
        const locations = await this.getLocations({
            user: username,
            limit: 100,
            offset: 0
        });
        
        // Get recent driving records
        const drivingRecords = await this.getDrivingRecords({
            user: username,
            limit: 50,
            offset: 0
        });
        
        return {
            user,
            recentLocations: locations.data,
            recentDriving: drivingRecords.data,
            stats: {
                totalLocations: user.location_count,
                totalDriving: user.driving_count,
                lastSeen: user.last_location_time
            }
        };
    }
}

// Usage
const dashboard = new LocationDashboard('YOUR_API_TOKEN');

dashboard.getUserDashboard('john_doe')
    .then(data => {
        console.log('User Dashboard:', data);
        // Render UI with data
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

---

## 📝 Migration from Direct Database Access

If you're currently using direct database queries in the dashboard, replace them with API calls:

### Before (Direct Database):
```php
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$userId]);
$users = $stmt->fetchAll(PDO::FETCH_ASSOC);
```

### After (API):
```javascript
const response = await fetch(
    'https://www.bahar.co.il/location/api/users.php?include_counts=true',
    {
        headers: { 'X-API-Token': 'YOUR_API_TOKEN' }
    }
);
const data = await response.json();
const users = data.data;
```

---

## 🔒 Security Notes

1. **Never expose API token in client-side code** - Store it securely on the server
2. **Use HTTPS** - All production requests must use HTTPS
3. **Validate responses** - Always check `success` field before using data
4. **Handle errors gracefully** - Implement proper error handling for all requests
5. **Respect rate limits** - Implement caching and request throttling

---

## 📞 Support

- **API Documentation:** https://www.bahar.co.il/location/api/docs/
- **Test Interface:** https://www.bahar.co.il/location/api/test-endpoints.html
- **Issues:** Contact backend team

---

**Last Updated:** 2024-10-27  
**API Version:** 2.0.0

