# 🚀 API Quick Reference Card

## 🔐 Authentication
```javascript
headers: { 'Authorization': 'Bearer YOUR_API_TOKEN' }
```

## 📍 Base URL
**Production:** `https://www.bahar.co.il/location/api`

---

## 1️⃣ GET /users.php

**Get users with location data**

```javascript
// Basic
GET /users.php

// With counts and metadata
GET /users.php?include_counts=true&include_metadata=true
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "username": "john_doe",
      "display_name": "John Doe",
      "location_count": 1250,
      "last_location_time": "2024-10-26 14:30:00"
    }
  ],
  "count": 5
}
```

---

## 2️⃣ GET /locations.php

**Get location records with filters**

```javascript
// By user
GET /locations.php?user=john_doe

// Date range
GET /locations.php?user=john_doe&date_from=2024-10-01&date_to=2024-10-27

// Accuracy filter
GET /locations.php?user=john_doe&accuracy_max=20

// Anomaly status
GET /locations.php?anomaly_status=marked

// Geographic radius (500m around point)
GET /locations.php?lat=32.0853&lng=34.7818&radius=500

// Pagination
GET /locations.php?user=john_doe&limit=100&offset=0
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "username": "john_doe",
      "latitude": 32.0853,
      "longitude": 34.7818,
      "accuracy": 5.0,
      "server_time": "2024-10-27 10:30:00",
      "anomaly_status": "normal"
    }
  ],
  "count": 100,
  "total": 1250,
  "limit": 100,
  "offset": 0
}
```

---

## 3️⃣ GET /driving-records.php

**Get driving records with filters**

```javascript
// By user
GET /driving-records.php?user=john_doe

// Date range
GET /driving-records.php?user=john_doe&date_from=2024-10-01&date_to=2024-10-27

// Event type
GET /driving-records.php?event_type=start

// Specific trip
GET /driving-records.php?trip_id=trip-abc123

// Pagination
GET /driving-records.php?user=john_doe&limit=50&offset=0
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 456,
      "username": "john_doe",
      "event_type": "start",
      "trip_id": "trip-abc123",
      "latitude": 32.0853,
      "longitude": 34.7818,
      "server_time": "2024-10-27 10:30:00"
    }
  ],
  "count": 50,
  "total": 150
}
```

---

## 4️⃣ GET /live/latest.php

**Get latest locations for user(s)**

```javascript
// Single user
GET /live/latest.php?user=john_doe

// Multiple users
GET /live/latest.php?user=john_doe,jane_smith

// All users (last 5 minutes)
GET /live/latest.php?all=true&max_age=300
```

**Response:**
```json
{
  "success": true,
  "data": {
    "locations": [
      {
        "username": "john_doe",
        "latitude": 32.0853,
        "longitude": 34.7818,
        "server_time": "2024-10-27 14:30:00",
        "age_seconds": 120,
        "is_recent": true
      }
    ],
    "count": 1
  }
}
```

---

## 5️⃣ GET /live/stream.php

**Real-time location streaming (polling)**

```javascript
// Initial request
let cursor = 0;
GET /live/stream.php?user=john_doe&since=0

// Subsequent polls (every 3 seconds)
GET /live/stream.php?user=john_doe&since=${cursor}

// Multiple users
GET /live/stream.php?user=john_doe,jane_smith&since=${cursor}

// All users
GET /live/stream.php?all=true&since=${cursor}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "points": [...],
    "cursor": 1729950600000,
    "has_more": false,
    "count": 5
  }
}
```

---

## 6️⃣ GET /live/history.php

**Recent tracking history**

```javascript
// Last hour
GET /live/history.php?user=john_doe&duration=3600

// Last 6 hours
GET /live/history.php?user=john_doe&duration=21600

// Last 24 hours (paginated)
GET /live/history.php?user=john_doe&duration=86400&limit=100&offset=0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "points": [...],
    "count": 100,
    "total": 450,
    "duration": 3600
  }
}
```

---

## 📊 Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `user` | string | - | Filter by username |
| `date_from` | datetime | - | Start date (YYYY-MM-DD) |
| `date_to` | datetime | - | End date (YYYY-MM-DD) |
| `limit` | integer | 1000 | Max records (max: 10000) |
| `offset` | integer | 0 | Pagination offset |

---

## ⚠️ Error Response

```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2024-10-27T10:30:00Z"
}
```

**Status Codes:**
- `200` ✅ Success
- `400` ❌ Bad Request
- `401` 🔒 Unauthorized
- `429` ⏱️ Rate Limit (1000/hour)
- `500` 💥 Server Error

---

## 🧪 Testing

**Data Endpoints Tester:**
https://www.bahar.co.il/location/api/test-endpoints.html

**Live Tracking Tester:**
https://www.bahar.co.il/location/api/test-live-endpoints.html

**Swagger Docs:**
https://www.bahar.co.il/location/api/docs/

---

## 💡 Quick Example

```javascript
const API_TOKEN = 'your_token_here';
const BASE_URL = 'https://www.bahar.co.il/location/api';

async function getLocations(username) {
  const response = await fetch(
    `${BASE_URL}/locations.php?user=${username}&limit=100`,
    {
      headers: {
        'Authorization': `Bearer ${API_TOKEN}`
      }
    }
  );
  
  const data = await response.json();
  
  if (data.success) {
    return data.data;
  } else {
    throw new Error(data.error);
  }
}

// Usage
getLocations('john_doe')
  .then(locations => console.log(locations))
  .catch(error => console.error(error));
```

---

**Full Documentation:** See `UI_DEVELOPER_GUIDE.md`

