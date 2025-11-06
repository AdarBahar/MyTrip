# 🔴 Live Tracking API - Complete Guide

## 🎯 Overview

The Live Tracking API provides real-time location tracking capabilities with support for single or multiple users. Built on top of the existing real-time tracking infrastructure, these endpoints enable efficient polling-based live tracking dashboards.

---

## 🏗️ Architecture

### **Data Flow**

```
Mobile App
    ↓ POST /api/getloc.php
    ↓
Location API
    ├─→ Insert into location_records (permanent storage)
    └─→ Update device_last_position (latest position)
        └─→ Insert into location_history_cache (recent history, 24h TTL)
    
Dashboard/UI
    ↓ Poll every 3-5 seconds
    ↓ GET /api/live/stream.php?since=CURSOR
    ↓
Streaming API
    ├─→ Query location_history_cache
    └─→ Return new points since cursor
    
Dashboard/UI
    └─→ Display points on map in real-time
```

### **Database Tables**

1. **`device_last_position`** - Stores the most recent location for each device
2. **`location_history_cache`** - Stores recent locations (24-hour rolling window)
3. **`streaming_sessions`** - Tracks active streaming sessions (optional)

---

## 📍 Endpoints

### **1. GET /live/latest.php** - Latest Locations

Get the most recent location for specified user(s) or device(s).

**Use Cases:**
- "Where is everyone now" dashboard
- Fleet management overview
- User status indicators

**Parameters:**
- `user` - Single username or comma-separated list
- `users[]` - Array of usernames
- `device` - Single device ID or comma-separated list
- `devices[]` - Array of device IDs
- `all` - Get all active users (boolean)
- `max_age` - Maximum age in seconds (default: 3600)
- `include_inactive` - Include users with no recent location (boolean)

**Example:**
```javascript
// Get latest for multiple users
const response = await fetch(
    '/api/live/latest.php?user=john_doe,jane_smith&max_age=300',
    { headers: { 'Authorization': 'Bearer TOKEN' } }
);
```

---

### **2. GET /live/stream.php** - Location Stream (Polling)

Get new location updates since a cursor timestamp. Designed for efficient polling.

**Use Cases:**
- Real-time tracking dashboards
- Live map updates
- Activity monitoring

**Parameters:**
- `user` - Single username or comma-separated list
- `users[]` - Array of usernames
- `device` - Single device ID or comma-separated list
- `devices[]` - Array of device IDs
- `all` - Stream all users (boolean)
- `since` - Cursor timestamp in milliseconds (default: 0)
- `limit` - Max records (default: 100, max: 500)
- `session_id` - Optional session tracking ID

**Polling Pattern:**
```javascript
let cursor = 0;

async function poll() {
    const response = await fetch(
        `/api/live/stream.php?user=john_doe&since=${cursor}`,
        { headers: { 'Authorization': 'Bearer TOKEN' } }
    );
    
    const data = await response.json();
    
    if (data.success && data.data.points.length > 0) {
        // Process new points
        updateMap(data.data.points);
        
        // Update cursor for next poll
        cursor = data.data.cursor;
    }
}

// Poll every 3 seconds
setInterval(poll, 3000);
```

---

### **3. GET /live/history.php** - Tracking History

Get recent tracking history from the cache table.

**Use Cases:**
- Route replay
- Recent path visualization
- Historical analysis (last 24 hours)

**Parameters:**
- `user` - Single username or comma-separated list
- `users[]` - Array of usernames
- `device` - Single device ID or comma-separated list
- `devices[]` - Array of device IDs
- `all` - Get all users (boolean)
- `duration` - Time window in seconds (default: 3600, max: 86400)
- `limit` - Max records (default: 500, max: 5000)
- `offset` - Pagination offset (default: 0)

**Example:**
```javascript
// Get last 6 hours for a user
const response = await fetch(
    '/api/live/history.php?user=john_doe&duration=21600',
    { headers: { 'Authorization': 'Bearer TOKEN' } }
);
```

---

## 🚀 Implementation Examples

### **Example 1: Simple Live Tracker**

```javascript
class SimpleLiveTracker {
    constructor(apiToken, baseUrl = '/api') {
        this.apiToken = apiToken;
        this.baseUrl = baseUrl;
        this.cursor = 0;
        this.interval = null;
    }
    
    async getLatest(users) {
        const userList = Array.isArray(users) ? users.join(',') : users;
        const response = await fetch(
            `${this.baseUrl}/live/latest.php?user=${userList}`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );
        return response.json();
    }
    
    async poll(users) {
        const userList = Array.isArray(users) ? users.join(',') : users;
        const response = await fetch(
            `${this.baseUrl}/live/stream.php?user=${userList}&since=${this.cursor}`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );
        
        const data = await response.json();
        
        if (data.success && data.data.points.length > 0) {
            this.cursor = data.data.cursor;
            return data.data.points;
        }
        
        return [];
    }
    
    startPolling(users, callback, interval = 3000) {
        this.interval = setInterval(async () => {
            const points = await this.poll(users);
            if (points.length > 0) {
                callback(points);
            }
        }, interval);
    }
    
    stopPolling() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Usage
const tracker = new SimpleLiveTracker('YOUR_API_TOKEN');

// Get initial latest positions
tracker.getLatest(['john_doe', 'jane_smith'])
    .then(data => {
        console.log('Latest positions:', data.data.locations);
    });

// Start live tracking
tracker.startPolling(['john_doe', 'jane_smith'], (points) => {
    console.log('New points:', points);
    // Update your map here
});

// Stop when done
// tracker.stopPolling();
```

---

### **Example 2: Multi-User Map Tracker**

```javascript
class MultiUserMapTracker {
    constructor(apiToken, map) {
        this.apiToken = apiToken;
        this.map = map;
        this.markers = new Map(); // user_id -> marker
        this.paths = new Map(); // user_id -> polyline
        this.cursor = 0;
        this.interval = null;
    }
    
    async initialize(users) {
        // Get latest positions for all users
        const response = await fetch(
            `/api/live/latest.php?user=${users.join(',')}&max_age=3600`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );
        
        const data = await response.json();
        
        if (data.success) {
            data.data.locations.forEach(loc => {
                this.updateMarker(loc);
            });
        }
        
        // Get recent history for paths
        const historyResponse = await fetch(
            `/api/live/history.php?user=${users.join(',')}&duration=3600`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );
        
        const historyData = await historyResponse.json();
        
        if (historyData.success) {
            this.updatePaths(historyData.data.points);
        }
    }
    
    updateMarker(location) {
        const userId = location.user_id;
        
        if (this.markers.has(userId)) {
            // Update existing marker
            const marker = this.markers.get(userId);
            marker.setLatLng([location.latitude, location.longitude]);
        } else {
            // Create new marker
            const marker = L.marker([location.latitude, location.longitude], {
                title: location.display_name
            }).addTo(this.map);
            
            marker.bindPopup(`
                <b>${location.display_name}</b><br>
                Speed: ${location.speed || 0} km/h<br>
                Battery: ${location.battery_level || 'N/A'}%<br>
                Updated: ${location.age_seconds}s ago
            `);
            
            this.markers.set(userId, marker);
        }
    }
    
    updatePaths(points) {
        // Group points by user
        const userPoints = new Map();
        
        points.forEach(point => {
            if (!userPoints.has(point.user_id)) {
                userPoints.set(point.user_id, []);
            }
            userPoints.get(point.user_id).push([point.latitude, point.longitude]);
        });
        
        // Update polylines
        userPoints.forEach((coords, userId) => {
            if (this.paths.has(userId)) {
                this.paths.get(userId).setLatLngs(coords);
            } else {
                const polyline = L.polyline(coords, {
                    color: this.getUserColor(userId),
                    weight: 3
                }).addTo(this.map);
                
                this.paths.set(userId, polyline);
            }
        });
    }
    
    getUserColor(userId) {
        const colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF'];
        return colors[userId % colors.length];
    }
    
    async poll(users) {
        const response = await fetch(
            `/api/live/stream.php?user=${users.join(',')}&since=${this.cursor}`,
            {
                headers: { 'Authorization': `Bearer ${this.apiToken}` }
            }
        );
        
        const data = await response.json();
        
        if (data.success && data.data.points.length > 0) {
            this.cursor = data.data.cursor;
            
            // Update markers and paths
            data.data.points.forEach(point => {
                this.updateMarker(point);
            });
            
            this.updatePaths(data.data.points);
        }
    }
    
    start(users, interval = 3000) {
        this.interval = setInterval(() => this.poll(users), interval);
    }
    
    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Usage with Leaflet
const map = L.map('map').setView([32.0853, 34.7818], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

const tracker = new MultiUserMapTracker('YOUR_API_TOKEN', map);

// Initialize and start tracking
tracker.initialize(['john_doe', 'jane_smith', 'bob_wilson'])
    .then(() => {
        tracker.start(['john_doe', 'jane_smith', 'bob_wilson']);
    });

// Stop when done
// tracker.stop();
```

---

## 🔒 Authentication & Rate Limiting

### **Authentication**
All endpoints require API token authentication:
```javascript
headers: {
    'Authorization': 'Bearer YOUR_API_TOKEN'
}
```

### **Rate Limits**
- `/live/latest.php` - 2000 requests/hour
- `/live/stream.php` - 3000 requests/hour (designed for polling)
- `/live/history.php` - 1000 requests/hour

---

## 📊 Performance Considerations

### **Polling Frequency**
- **Recommended:** 3-5 seconds
- **Minimum:** 2 seconds (to avoid rate limiting)
- **Maximum:** 10 seconds (for near real-time)

### **Cursor Management**
- Always use the returned `cursor` value for the next poll
- Don't reset cursor to 0 unless you want to re-fetch all data
- Cursor is a timestamp in milliseconds

### **Bandwidth Optimization**
- Use `max_age` parameter to filter old data
- Use `limit` parameter to control response size
- ETag support for 304 Not Modified responses

---

## 🧪 Testing

### **Interactive Test Interface**
https://www.bahar.co.il/location/api/test-live-endpoints.html

Features:
- Test all three endpoints
- Auto-polling functionality
- Multiple user support
- Visual JSON responses

### **Manual Testing**

```bash
# Get latest locations
curl "https://www.bahar.co.il/location/api/live/latest.php?user=john_doe" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Stream locations
curl "https://www.bahar.co.il/location/api/live/stream.php?user=john_doe&since=0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get history
curl "https://www.bahar.co.il/location/api/live/history.php?user=john_doe&duration=3600" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Troubleshooting

### **No points returned**

1. Check if user has recent location data:
   ```sql
   SELECT * FROM device_last_position WHERE user_id = (SELECT id FROM users WHERE username = 'john_doe');
   ```

2. Check cache table:
   ```sql
   SELECT * FROM location_history_cache WHERE user_id = (SELECT id FROM users WHERE username = 'john_doe') ORDER BY server_time DESC LIMIT 10;
   ```

3. Verify `max_age` parameter isn't too restrictive

### **Cursor not advancing**

- Make sure you're using the `cursor` value from the response
- Cursor is in milliseconds, not seconds
- Check if new data is actually being received

### **Rate limit errors**

- Reduce polling frequency
- Use multiple API tokens for different users
- Implement exponential backoff

---

## 📝 Best Practices

1. **Always handle errors gracefully**
   ```javascript
   try {
       const data = await tracker.poll(users);
   } catch (error) {
       console.error('Polling failed:', error);
       // Implement retry logic
   }
   ```

2. **Implement connection status indicators**
   - Show "Connected" / "Disconnected" status
   - Display last update time
   - Show number of active users

3. **Clean up on page unload**
   ```javascript
   window.addEventListener('beforeunload', () => {
       tracker.stop();
   });
   ```

4. **Use session IDs for analytics**
   - Track how long users are viewing live data
   - Monitor polling performance
   - Debug connection issues

---

## 🚀 Next Steps

1. **Deploy to production:** `./deploy_prod.sh`
2. **Test with real devices:** Use mobile app to send location data
3. **Build your dashboard:** Use the examples above as starting points
4. **Monitor performance:** Check rate limits and response times

---

**Last Updated:** 2025-10-27  
**API Version:** 2.0.0  
**Endpoints:** 3 (latest, stream, history)

