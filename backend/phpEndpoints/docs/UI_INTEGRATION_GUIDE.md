# UI Integration Guide - Enhanced Real-Time Location Streaming

## 🎯 Overview

This guide shows how to integrate the new enhanced real-time location streaming features into your web UI. The system provides:

- **Server-Sent Events (SSE)** for push-based real-time updates
- **JWT Session Management** for secure streaming connections
- **Change Detection** to reduce bandwidth and unnecessary updates
- **Dwell/Drive Analytics** for movement pattern analysis
- **Route Simplification** for efficient map rendering

---

## 🚀 Quick Start

### 1. Create a Streaming Session

Before connecting to the SSE stream, create a session to get a JWT token:

```javascript
async function createStreamingSession(deviceIds = [], duration = 3600) {
  const response = await fetch('/api/live/session', {
    method: 'POST',
    headers: {
      'X-API-Token': 'YOUR_API_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      device_ids: deviceIds,  // Empty array = all devices
      duration: duration      // Session duration in seconds (default: 1 hour)
    })
  });
  
  const result = await response.json();
  
  if (result.status === 'success') {
    return {
      sessionId: result.data.session_id,
      token: result.data.session_token,
      expiresAt: result.data.expires_at,
      streamUrl: result.data.stream_url
    };
  } else {
    throw new Error(result.message || 'Failed to create session');
  }
}
```

### 2. Connect to SSE Stream

Use the JWT token to establish a real-time connection:

```javascript
class LocationStreamClient {
  constructor(jwtToken) {
    this.token = jwtToken;
    this.eventSource = null;
    this.handlers = {
      connected: [],
      location: [],
      noChange: [],
      bye: [],
      error: []
    };
  }
  
  connect() {
    // Create EventSource with JWT token
    this.eventSource = new EventSource(
      `/api/live/stream-sse.php?token=${this.token}`
    );
    
    // Handle connection established
    this.eventSource.addEventListener('connected', (e) => {
      const data = JSON.parse(e.data);
      console.log('✅ Connected to stream:', data);
      this.handlers.connected.forEach(handler => handler(data));
    });
    
    // Handle location updates
    this.eventSource.addEventListener('loc', (e) => {
      const location = JSON.parse(e.data);
      console.log('📍 Location update:', location);
      this.handlers.location.forEach(handler => handler(location));
    });
    
    // Handle heartbeat (no change)
    this.eventSource.addEventListener('no_change', (e) => {
      const data = JSON.parse(e.data);
      console.log('💓 Heartbeat:', data);
      this.handlers.noChange.forEach(handler => handler(data));
    });
    
    // Handle connection close
    this.eventSource.addEventListener('bye', (e) => {
      const data = JSON.parse(e.data);
      console.log('👋 Connection closed:', data);
      this.handlers.bye.forEach(handler => handler(data));
      this.disconnect();
    });
    
    // Handle errors
    this.eventSource.onerror = (error) => {
      console.error('❌ Stream error:', error);
      this.handlers.error.forEach(handler => handler(error));
    };
  }
  
  on(event, handler) {
    if (this.handlers[event]) {
      this.handlers[event].push(handler);
    }
  }
  
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

### 3. Complete Example - Live Tracking Map

```javascript
// Global variables
let streamClient = null;
let sessionData = null;
let markers = {};  // Store markers by device_id

// Initialize live tracking
async function startLiveTracking(deviceIds = []) {
  try {
    // Step 1: Create session
    console.log('Creating streaming session...');
    sessionData = await createStreamingSession(deviceIds, 3600);
    console.log('Session created:', sessionData.sessionId);
    
    // Step 2: Connect to stream
    console.log('Connecting to SSE stream...');
    streamClient = new LocationStreamClient(sessionData.token);
    
    // Step 3: Handle events
    streamClient.on('connected', (data) => {
      showNotification('✅ Live tracking started', 'success');
      updateStatusIndicator('connected', data.device_ids.length);
    });
    
    streamClient.on('location', (location) => {
      updateMarkerOnMap(location);
      updateLocationList(location);
      showChangeReason(location);
    });
    
    streamClient.on('noChange', (data) => {
      updateStatusIndicator('active', data.active_devices);
    });
    
    streamClient.on('bye', (data) => {
      showNotification(`Connection closed: ${data.reason}`, 'info');
      updateStatusIndicator('disconnected');
    });
    
    streamClient.on('error', (error) => {
      showNotification('Stream error - reconnecting...', 'error');
      // Implement reconnection logic here
    });
    
    // Step 4: Connect
    streamClient.connect();
    
  } catch (error) {
    console.error('Failed to start live tracking:', error);
    showNotification('Failed to start live tracking', 'error');
  }
}

// Stop live tracking
async function stopLiveTracking() {
  if (streamClient) {
    streamClient.disconnect();
    streamClient = null;
  }
  
  if (sessionData) {
    // Revoke session
    try {
      await fetch(`/api/live/session/${sessionData.sessionId}`, {
        method: 'DELETE',
        headers: {
          'X-API-Token': 'YOUR_API_TOKEN'
        }
      });
      console.log('Session revoked');
    } catch (error) {
      console.error('Failed to revoke session:', error);
    }
    sessionData = null;
  }
  
  updateStatusIndicator('disconnected');
  showNotification('Live tracking stopped', 'info');
}

// Update marker on map
function updateMarkerOnMap(location) {
  const deviceId = location.device_id;
  
  // Create or update marker
  if (!markers[deviceId]) {
    markers[deviceId] = L.marker([location.latitude, location.longitude], {
      icon: createDeviceIcon(location),
      title: location.username || deviceId
    }).addTo(map);
    
    // Add popup
    markers[deviceId].bindPopup(createPopupContent(location));
  } else {
    // Update existing marker
    markers[deviceId].setLatLng([location.latitude, location.longitude]);
    markers[deviceId].setIcon(createDeviceIcon(location));
    markers[deviceId].getPopup().setContent(createPopupContent(location));
  }
  
  // Animate marker
  markers[deviceId].setOpacity(0.5);
  setTimeout(() => markers[deviceId].setOpacity(1), 300);
  
  // Show change reason badge
  if (location.change_reason) {
    showChangeBadge(deviceId, location.change_reason, location.change_metrics);
  }
}

// Create popup content
function createPopupContent(location) {
  const speed = location.speed ? `${location.speed.toFixed(1)} km/h` : 'N/A';
  const bearing = location.bearing ? `${location.bearing.toFixed(0)}°` : 'N/A';
  const battery = location.battery_level ? `${location.battery_level}%` : 'N/A';
  const age = location.age_seconds ? `${location.age_seconds}s ago` : 'Just now';
  
  return `
    <div class="location-popup">
      <h3>${location.username || location.device_id}</h3>
      <div class="location-details">
        <div><strong>Speed:</strong> ${speed}</div>
        <div><strong>Bearing:</strong> ${bearing}</div>
        <div><strong>Battery:</strong> ${battery}</div>
        <div><strong>Updated:</strong> ${age}</div>
        ${location.change_reason ? `
          <div class="change-reason">
            <strong>Change:</strong> ${location.change_reason}
            ${formatChangeMetrics(location.change_metrics)}
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

// Format change metrics
function formatChangeMetrics(metrics) {
  if (!metrics) return '';
  
  const parts = [];
  if (metrics.distance_meters) {
    parts.push(`${metrics.distance_meters.toFixed(0)}m`);
  }
  if (metrics.time_diff_seconds) {
    parts.push(`${metrics.time_diff_seconds}s`);
  }
  if (metrics.speed_change_kmh) {
    parts.push(`Δ${metrics.speed_change_kmh.toFixed(1)} km/h`);
  }
  
  return parts.length > 0 ? `<br><small>(${parts.join(', ')})</small>` : '';
}

// Show change reason badge
function showChangeBadge(deviceId, reason, metrics) {
  const badge = document.createElement('div');
  badge.className = `change-badge change-${reason}`;
  badge.textContent = reason.toUpperCase();
  badge.style.cssText = `
    position: absolute;
    top: -30px;
    left: 50%;
    transform: translateX(-50%);
    background: #4CAF50;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    white-space: nowrap;
    z-index: 1000;
    animation: fadeOut 3s forwards;
  `;
  
  const markerElement = markers[deviceId].getElement();
  if (markerElement) {
    markerElement.style.position = 'relative';
    markerElement.appendChild(badge);
    setTimeout(() => badge.remove(), 3000);
  }
}

// Update status indicator
function updateStatusIndicator(status, deviceCount = 0) {
  const indicator = document.getElementById('status-indicator');
  if (!indicator) return;
  
  const statusConfig = {
    connected: { color: '#4CAF50', text: `🟢 Live (${deviceCount} devices)` },
    active: { color: '#4CAF50', text: `🟢 Active (${deviceCount} devices)` },
    disconnected: { color: '#9E9E9E', text: '⚫ Disconnected' },
    error: { color: '#F44336', text: '🔴 Error' }
  };
  
  const config = statusConfig[status] || statusConfig.disconnected;
  indicator.style.color = config.color;
  indicator.textContent = config.text;
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#F44336' : '#2196F3'};
    color: white;
    padding: 12px 20px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    z-index: 10000;
    animation: slideIn 0.3s, slideOut 0.3s 2.7s;
  `;
  
  document.body.appendChild(notification);
  setTimeout(() => notification.remove(), 3000);
}
```

---

## 📊 Get History with Analytics

Fetch historical data with dwell/drive segmentation:

```javascript
async function getLocationHistory(deviceId, duration = 86400, includeSegments = true) {
  const params = new URLSearchParams({
    device: deviceId,
    duration: duration,
    segments: includeSegments ? 'true' : 'false',
    limit: 1000
  });
  
  const response = await fetch(`/api/live/history.php?${params}`, {
    headers: {
      'X-API-Token': 'YOUR_API_TOKEN'
    }
  });
  
  const result = await response.json();
  
  if (result.status === 'success') {
    return {
      points: result.data.points,
      segments: result.data.segments || null,
      count: result.data.count
    };
  } else {
    throw new Error(result.message || 'Failed to fetch history');
  }
}

// Display history on map
async function showHistoryOnMap(deviceId) {
  try {
    const history = await getLocationHistory(deviceId, 86400, true);
    
    // Draw route
    const coordinates = history.points.map(p => [p.latitude, p.longitude]);
    const polyline = L.polyline(coordinates, {
      color: '#2196F3',
      weight: 3,
      opacity: 0.7
    }).addTo(map);
    
    // Show dwells
    if (history.segments && history.segments.dwells) {
      history.segments.dwells.forEach(dwell => {
        const circle = L.circle(
          [dwell.center.latitude, dwell.center.longitude],
          {
            radius: dwell.radius_meters,
            color: '#FF9800',
            fillColor: '#FF9800',
            fillOpacity: 0.2
          }
        ).addTo(map);
        
        circle.bindPopup(`
          <strong>Dwell</strong><br>
          Duration: ${formatDuration(dwell.duration_seconds)}<br>
          Points: ${dwell.point_count}
        `);
      });
    }
    
    // Show drives
    if (history.segments && history.segments.drives) {
      history.segments.drives.forEach(drive => {
        // Use simplified points for better performance
        const driveCoords = drive.simplified_points.map(p => 
          [p.latitude, p.longitude]
        );
        
        const driveLine = L.polyline(driveCoords, {
          color: '#4CAF50',
          weight: 4,
          opacity: 0.8
        }).addTo(map);
        
        driveLine.bindPopup(`
          <strong>Drive</strong><br>
          Distance: ${(drive.distance_meters / 1000).toFixed(2)} km<br>
          Avg Speed: ${drive.avg_speed_kmh.toFixed(1)} km/h<br>
          Duration: ${formatDuration(drive.duration_seconds)}<br>
          Points: ${drive.point_count} → ${drive.simplified_point_count} (simplified)
        `);
      });
    }
    
    // Fit map to route
    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    
  } catch (error) {
    console.error('Failed to load history:', error);
    showNotification('Failed to load history', 'error');
  }
}

function formatDuration(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}
```

---

## 🎨 UI Components

### HTML Structure

```html
<!-- Live Tracking Controls -->
<div class="live-tracking-controls">
  <div class="status-bar">
    <span id="status-indicator">⚫ Disconnected</span>
    <button id="toggle-tracking" onclick="toggleLiveTracking()">
      📡 Start Live Tracking
    </button>
  </div>
  
  <div class="device-filter" style="display: none;">
    <label>Filter Devices:</label>
    <input type="text" id="device-filter-input" placeholder="device_1, device_2, ...">
    <button onclick="applyDeviceFilter()">Apply</button>
  </div>
</div>

<!-- History Controls -->
<div class="history-controls">
  <button onclick="showHistoryOnMap(currentDeviceId)">
    📊 Show History (24h)
  </button>
  <button onclick="clearHistory()">
    🗑️ Clear History
  </button>
</div>
```

### CSS Styles

```css
/* Live Tracking Controls */
.live-tracking-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1000;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

#status-indicator {
  font-weight: bold;
  font-size: 14px;
}

#toggle-tracking {
  background: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

#toggle-tracking:hover {
  background: #1976D2;
}

#toggle-tracking.active {
  background: #F44336;
}

/* Change Badge Animation */
@keyframes fadeOut {
  0% { opacity: 1; transform: translateX(-50%) translateY(0); }
  70% { opacity: 1; }
  100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
}

/* Notification Animation */
@keyframes slideIn {
  from { transform: translateX(400px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(400px); opacity: 0; }
}

/* Location Popup */
.location-popup h3 {
  margin: 0 0 10px 0;
  color: #2196F3;
}

.location-details {
  font-size: 13px;
  line-height: 1.6;
}

.change-reason {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  color: #4CAF50;
}
```

---

## 🔧 Helper Functions

```javascript
// Toggle live tracking
async function toggleLiveTracking() {
  const button = document.getElementById('toggle-tracking');
  
  if (streamClient) {
    // Stop tracking
    await stopLiveTracking();
    button.textContent = '📡 Start Live Tracking';
    button.classList.remove('active');
  } else {
    // Start tracking
    const deviceFilter = document.getElementById('device-filter-input').value;
    const deviceIds = deviceFilter ? deviceFilter.split(',').map(s => s.trim()) : [];
    
    await startLiveTracking(deviceIds);
    button.textContent = '⏹️ Stop Live Tracking';
    button.classList.add('active');
  }
}

// Create device icon based on movement
function createDeviceIcon(location) {
  const speed = location.speed || 0;
  const isMoving = speed > 5; // km/h
  
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div class="marker-icon ${isMoving ? 'moving' : 'stationary'}">
        <div class="marker-arrow" style="transform: rotate(${location.bearing || 0}deg)">
          ${isMoving ? '▲' : '●'}
        </div>
      </div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  });
}

// Auto-reconnect on error
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

streamClient.on('error', async (error) => {
  if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
    
    console.log(`Reconnecting in ${delay/1000}s (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
    showNotification(`Reconnecting... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`, 'info');
    
    setTimeout(async () => {
      try {
        streamClient.disconnect();
        sessionData = await createStreamingSession([], 3600);
        streamClient = new LocationStreamClient(sessionData.token);
        streamClient.connect();
        reconnectAttempts = 0; // Reset on success
      } catch (err) {
        console.error('Reconnection failed:', err);
      }
    }, delay);
  } else {
    showNotification('Max reconnection attempts reached', 'error');
    await stopLiveTracking();
  }
});
```

---

## 📱 Mobile Optimization

```javascript
// Detect mobile and adjust update frequency
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

if (isMobile) {
  // Reduce marker animations on mobile
  function updateMarkerOnMap(location) {
    // ... simplified version without animations
  }
  
  // Use geolocation to center map
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition((position) => {
      map.setView([position.coords.latitude, position.coords.longitude], 13);
    });
  }
}
```

---

## 🎯 Best Practices

1. **Session Management**
   - Create session only when needed
   - Revoke session when done
   - Handle session expiration gracefully

2. **Error Handling**
   - Implement auto-reconnect with exponential backoff
   - Show user-friendly error messages
   - Log errors for debugging

3. **Performance**
   - Use simplified routes for historical data
   - Limit number of markers on map
   - Debounce rapid updates

4. **User Experience**
   - Show connection status clearly
   - Animate marker updates smoothly
   - Display change reasons for transparency

5. **Security**
   - Never expose API tokens in client code
   - Validate JWT tokens server-side
   - Use HTTPS for all connections

---

## 📚 API Reference

See complete API documentation:
- **Architecture:** `docs/ENHANCED_REALTIME_ARCHITECTURE.md`
- **Setup Guide:** `docs/ENHANCED_STREAMING_SETUP.md`
- **Swagger UI:** `https://www.bahar.co.il/location/api/docs/`

