# 📋 **UI Implementation Guide: User Location History**

## **Overview**
Implement a location history viewer that allows users to select different time ranges and view historical location data. The UI should intelligently use two different API endpoints based on the selected time range.

---

## **🎯 Time Range Options**

The UI should provide these 5 options:

| Option | Duration | Endpoint to Use | Notes |
|--------|----------|----------------|-------|
| **Last Hour** | 3,600 seconds | `/live/history.php` | Fast cache-based |
| **Last 24 Hours** | 86,400 seconds | `/live/history.php` | Fast cache-based (max for this endpoint) |
| **Last Week** | 7 days | `/locations.php` | Full database query |
| **Last Month** | 30 days | `/locations.php` | Full database query |
| **All** | All time | `/locations.php` | Full database query |

---

## **📡 API Endpoint Selection Logic**

```javascript
function getHistoryEndpoint(timeRange) {
    // Use fast cache endpoint for recent data (≤24 hours)
    if (timeRange === 'last_hour' || timeRange === 'last_24_hours') {
        return '/live/history.php';
    }
    
    // Use full database endpoint for older data (>24 hours)
    return '/locations.php';
}
```

---

## **🔧 Implementation Examples**

### **1. Last Hour (using `/live/history.php`)**

```javascript
async function getLastHourHistory(username) {
    const params = new URLSearchParams({
        user: username,
        duration: '3600',      // 1 hour in seconds
        limit: '500',          // Default: 500, max: 5000
        offset: '0'            // For pagination
    });
    
    const response = await fetch(
        `https://www.bahar.co.il/location/api/live/history.php?${params}`,
        {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN'
            }
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        return {
            points: data.data.points,
            count: data.data.count,
            total: data.data.total,
            source: 'cache'  // Fast cache-based query
        };
    }
}
```

**Response Structure:**
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
                "accuracy": 10.5,
                "altitude": 50.0,
                "speed": 0,
                "bearing": null,
                "battery_level": 85,
                "recorded_at": 1761652190907,
                "server_time": "2025-10-28 14:30:00"
            }
        ],
        "count": 150,
        "total": 150,
        "duration": 3600,
        "source": "cache"
    }
}
```

---

### **2. Last 24 Hours (using `/live/history.php`)**

```javascript
async function getLast24HoursHistory(username) {
    const params = new URLSearchParams({
        user: username,
        duration: '86400',     // 24 hours in seconds (MAX for this endpoint)
        limit: '1000',         // Increase limit for more data
        offset: '0'
    });
    
    const response = await fetch(
        `https://www.bahar.co.il/location/api/live/history.php?${params}`,
        {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN'
            }
        }
    );
    
    return await response.json();
}
```

---

### **3. Last Week (using `/locations.php`)**

```javascript
async function getLastWeekHistory(username) {
    // Calculate date range
    const now = new Date();
    const weekAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));
    
    const params = new URLSearchParams({
        user: username,
        date_from: weekAgo.toISOString().split('T')[0],  // YYYY-MM-DD
        date_to: now.toISOString().split('T')[0],        // YYYY-MM-DD
        limit: '1000',         // Default: 1000, max: 10000
        offset: '0',
        include_anomaly_status: 'true'  // Include anomaly info
    });
    
    const response = await fetch(
        `https://www.bahar.co.il/location/api/locations.php?${params}`,
        {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN'
            }
        }
    );
    
    const data = await response.json();
    
    if (data.success) {
        return {
            points: data.data,     // Note: different structure than history.php
            count: data.count,
            total: data.total,
            source: 'database'     // Full database query
        };
    }
}
```

**Response Structure:**
```json
{
    "success": true,
    "data": [
        {
            "id": 12345,
            "user_id": 1,
            "username": "john_doe",
            "display_name": "John Doe",
            "device_id": "device-12345",
            "latitude": 32.0853,
            "longitude": 34.7818,
            "accuracy": 10.5,
            "altitude": 50.0,
            "speed": null,
            "bearing": null,
            "battery_level": 85,
            "server_time": "2025-10-21 14:30:00",
            "client_time": 1761652190907,
            "anomaly_status": "normal",
            "marked_by_user": 0
        }
    ],
    "count": 1000,
    "total": 5432
}
```

---

### **4. Last Month (using `/locations.php`)**

```javascript
async function getLastMonthHistory(username) {
    const now = new Date();
    const monthAgo = new Date(now.getTime() - (30 * 24 * 60 * 60 * 1000));
    
    const params = new URLSearchParams({
        user: username,
        date_from: monthAgo.toISOString().split('T')[0],
        date_to: now.toISOString().split('T')[0],
        limit: '1000',
        offset: '0'
    });
    
    const response = await fetch(
        `https://www.bahar.co.il/location/api/locations.php?${params}`,
        {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN'
            }
        }
    );
    
    return await response.json();
}
```

---

### **5. All Time (using `/locations.php`)**

```javascript
async function getAllTimeHistory(username) {
    const params = new URLSearchParams({
        user: username,
        // No date filters = all time
        limit: '1000',
        offset: '0',
        include_anomaly_status: 'true'
    });
    
    const response = await fetch(
        `https://www.bahar.co.il/location/api/locations.php?${params}`,
        {
            headers: {
                'Authorization': 'Bearer YOUR_API_TOKEN'
            }
        }
    );
    
    return await response.json();
}
```

---

## **🎨 Complete UI Implementation**

```javascript
class LocationHistoryViewer {
    constructor(apiToken) {
        this.apiToken = apiToken;
        this.baseUrl = 'https://www.bahar.co.il/location/api';
    }
    
    /**
     * Main method to fetch history based on time range selection
     */
    async fetchHistory(username, timeRange) {
        switch(timeRange) {
            case 'last_hour':
                return await this.fetchRecentHistory(username, 3600);

            case 'last_24_hours':
                return await this.fetchRecentHistory(username, 86400);

            case 'last_week':
                return await this.fetchDatabaseHistory(username, 7);

            case 'last_month':
                return await this.fetchDatabaseHistory(username, 30);

            case 'all':
                return await this.fetchDatabaseHistory(username, null);

            default:
                throw new Error(`Invalid time range: ${timeRange}`);
        }
    }

    /**
     * Fetch recent history using cache endpoint (≤24 hours)
     */
    async fetchRecentHistory(username, durationSeconds) {
        const params = new URLSearchParams({
            user: username,
            duration: durationSeconds.toString(),
            limit: '1000',
            offset: '0'
        });

        const response = await fetch(
            `${this.baseUrl}/live/history.php?${params}`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiToken}`
                }
            }
        );

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch history');
        }

        // Normalize response format
        return {
            locations: data.data.points,
            count: data.data.count,
            total: data.data.total,
            source: 'cache',
            hasMore: data.data.total > data.data.count
        };
    }

    /**
     * Fetch older history using database endpoint (>24 hours or all time)
     */
    async fetchDatabaseHistory(username, daysAgo = null) {
        const params = new URLSearchParams({
            user: username,
            limit: '1000',
            offset: '0',
            include_anomaly_status: 'true'
        });

        // Add date range if specified
        if (daysAgo !== null) {
            const now = new Date();
            const pastDate = new Date(now.getTime() - (daysAgo * 24 * 60 * 60 * 1000));

            params.append('date_from', pastDate.toISOString().split('T')[0]);
            params.append('date_to', now.toISOString().split('T')[0]);
        }

        const response = await fetch(
            `${this.baseUrl}/locations.php?${params}`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiToken}`
                }
            }
        );

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Failed to fetch history');
        }

        // Normalize response format
        return {
            locations: data.data,
            count: data.count,
            total: data.total,
            source: 'database',
            hasMore: data.total > data.count
        };
    }

    /**
     * Fetch paginated data (for "Load More" functionality)
     */
    async fetchMoreHistory(username, timeRange, offset) {
        const isRecent = (timeRange === 'last_hour' || timeRange === 'last_24_hours');
        const endpoint = isRecent ? '/live/history.php' : '/locations.php';

        const params = new URLSearchParams({
            user: username,
            limit: '1000',
            offset: offset.toString()
        });

        if (isRecent) {
            const duration = timeRange === 'last_hour' ? 3600 : 86400;
            params.append('duration', duration.toString());
        } else {
            // Add date range for database queries
            if (timeRange === 'last_week') {
                const weekAgo = new Date(Date.now() - (7 * 24 * 60 * 60 * 1000));
                params.append('date_from', weekAgo.toISOString().split('T')[0]);
            } else if (timeRange === 'last_month') {
                const monthAgo = new Date(Date.now() - (30 * 24 * 60 * 60 * 1000));
                params.append('date_from', monthAgo.toISOString().split('T')[0]);
            }
            params.append('include_anomaly_status', 'true');
        }

        const response = await fetch(
            `${this.baseUrl}${endpoint}?${params}`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiToken}`
                }
            }
        );

        return await response.json();
    }
}
```

---

## **🖥️ HTML UI Example**

```html
<div class="history-viewer">
    <!-- Time Range Selector -->
    <div class="time-range-selector">
        <label>Select Time Range:</label>
        <select id="timeRangeSelect" onchange="loadHistory()">
            <option value="last_hour">Last Hour</option>
            <option value="last_24_hours" selected>Last 24 Hours</option>
            <option value="last_week">Last Week</option>
            <option value="last_month">Last Month</option>
            <option value="all">All Time</option>
        </select>
    </div>

    <!-- User Selector -->
    <div class="user-selector">
        <label>User:</label>
        <select id="userSelect">
            <option value="john_doe">John Doe</option>
            <option value="jane_smith">Jane Smith</option>
        </select>
    </div>

    <!-- Load Button -->
    <button onclick="loadHistory()">Load History</button>

    <!-- Results Display -->
    <div id="historyResults">
        <div id="loadingIndicator" style="display:none;">Loading...</div>
        <div id="historyMap"></div>
        <div id="historyStats"></div>
        <div id="locationList"></div>
    </div>

    <!-- Pagination -->
    <div id="pagination" style="display:none;">
        <button onclick="loadMore()">Load More</button>
        <span id="paginationInfo"></span>
    </div>
</div>

<script>
const viewer = new LocationHistoryViewer('YOUR_API_TOKEN');
let currentOffset = 0;
let currentTimeRange = 'last_24_hours';
let currentUsername = 'john_doe';

async function loadHistory() {
    currentTimeRange = document.getElementById('timeRangeSelect').value;
    currentUsername = document.getElementById('userSelect').value;
    currentOffset = 0;

    document.getElementById('loadingIndicator').style.display = 'block';

    try {
        const result = await viewer.fetchHistory(currentUsername, currentTimeRange);

        displayResults(result);

        // Show pagination if there's more data
        if (result.hasMore) {
            document.getElementById('pagination').style.display = 'block';
            document.getElementById('paginationInfo').textContent =
                `Showing ${result.count} of ${result.total} locations`;
        } else {
            document.getElementById('pagination').style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading history:', error);
        alert('Failed to load history: ' + error.message);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
}

async function loadMore() {
    currentOffset += 1000;

    try {
        const result = await viewer.fetchMoreHistory(
            currentUsername,
            currentTimeRange,
            currentOffset
        );

        appendResults(result);

    } catch (error) {
        console.error('Error loading more:', error);
    }
}

function displayResults(result) {
    // Display locations on map
    // Display statistics
    // Display location list
    console.log(`Loaded ${result.count} locations from ${result.source}`);
    console.log('Locations:', result.locations);
}

function appendResults(result) {
    // Append more locations to existing display
}
</script>
```

---

## **📊 Key Differences Between Endpoints**

| Feature | `/live/history.php` | `/locations.php` |
|---------|-------------------|------------------|
| **Max Time Range** | 24 hours | Unlimited |
| **Data Source** | `location_history_cache` (fast) | `location_records` (complete) |
| **Max Limit** | 5,000 | 10,000 |
| **Default Limit** | 500 | 1,000 |
| **Anomaly Status** | ❌ Not included | ✅ Included |
| **Response Field** | `data.points` | `data` (array) |
| **Best For** | Recent tracking, replay | Historical analysis, reports |

---

## **⚡ Performance Tips**

1. **Use cache endpoint for recent data** - It's much faster for last hour/24 hours
2. **Implement pagination** - Don't load all data at once for large time ranges
3. **Show loading indicators** - Database queries can take longer
4. **Cache results client-side** - Avoid re-fetching the same data
5. **Use appropriate limits** - Start with 500-1000, load more on demand

---

## **🎯 Summary**

- **Last Hour & Last 24 Hours** → Use `/live/history.php` with `duration` parameter
- **Last Week, Last Month, All Time** → Use `/locations.php` with `date_from`/`date_to` parameters
- Both endpoints support pagination via `limit` and `offset`
- Normalize the response format in your code to handle both endpoint structures
- Display total count and implement "Load More" for large datasets

This approach gives you the best performance for recent data while maintaining access to complete historical records! 🚀

