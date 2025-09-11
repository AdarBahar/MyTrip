# 🛣️ **Day Route Breakdown API**

## 📋 **Overview**

The Day Route Breakdown API provides detailed segment-by-segment routing information for a complete day's journey. It breaks down the route into individual segments and provides comprehensive routing data for each part of the journey.

## 🎯 **Endpoint**

```
POST /routing/days/route-breakdown
```

## 📥 **Request Format**

### **Request Body**
```json
{
  "trip_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
  "day_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4", 
  "start": {
    "lat": 32.0853,
    "lon": 34.7818,
    "name": "Hotel Start"
  },
  "stops": [
    {
      "lat": 32.0944,
      "lon": 34.7806,
      "name": "Museum"
    },
    {
      "lat": 32.0892,
      "lon": 34.7751,
      "name": "Restaurant"
    }
  ],
  "end": {
    "lat": 32.0823,
    "lon": 34.7789,
    "name": "Hotel End"
  },
  "profile": "car",
  "options": {
    "avoid_highways": false,
    "avoid_tolls": false
  }
}
```

### **Request Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trip_id` | string | ✅ | ID of the trip |
| `day_id` | string | ✅ | ID of the day |
| `start` | RoutePoint | ✅ | Starting point of the day |
| `stops` | RoutePoint[] | ✅ | Ordered list of stops to visit |
| `end` | RoutePoint | ✅ | Ending point of the day |
| `profile` | string | ❌ | Routing profile: `car`, `motorcycle`, `bike` (default: `car`) |
| `options` | RouteOptions | ❌ | Additional routing options |

### **RoutePoint Object**
```json
{
  "lat": 32.0853,
  "lon": 34.7818,
  "name": "Optional location name"
}
```

## 📤 **Response Format**

### **Success Response (200)**
```json
{
  "trip_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
  "day_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
  "total_distance_km": 15.7,
  "total_duration_min": 28.5,
  "computed_at": "2025-09-07T14:30:00Z",
  "segments": [
    {
      "from_point": {
        "lat": 32.0853,
        "lon": 34.7818,
        "name": "Hotel Start"
      },
      "to_point": {
        "lat": 32.0944,
        "lon": 34.7806,
        "name": "Museum"
      },
      "distance_km": 1.2,
      "duration_min": 3.5,
      "segment_type": "start_to_stop",
      "segment_index": 0,
      "geometry": {
        "type": "LineString",
        "coordinates": [[34.7818, 32.0853], [34.7806, 32.0944]]
      },
      "instructions": [
        {
          "text": "Head north on Main Street",
          "distance": 500,
          "time": 60,
          "sign": 0
        }
      ]
    },
    {
      "from_point": {
        "lat": 32.0944,
        "lon": 34.7806,
        "name": "Museum"
      },
      "to_point": {
        "lat": 32.0892,
        "lon": 34.7751,
        "name": "Restaurant"
      },
      "distance_km": 0.8,
      "duration_min": 2.1,
      "segment_type": "stop_to_stop",
      "segment_index": 1,
      "geometry": {
        "type": "LineString",
        "coordinates": [[34.7806, 32.0944], [34.7751, 32.0892]]
      },
      "instructions": [
        {
          "text": "Turn right onto Side Street",
          "distance": 300,
          "time": 45,
          "sign": 2
        }
      ]
    },
    {
      "from_point": {
        "lat": 32.0892,
        "lon": 34.7751,
        "name": "Restaurant"
      },
      "to_point": {
        "lat": 32.0823,
        "lon": 34.7789,
        "name": "Hotel End"
      },
      "distance_km": 0.9,
      "duration_min": 2.8,
      "segment_type": "stop_to_end",
      "segment_index": 2,
      "geometry": {
        "type": "LineString",
        "coordinates": [[34.7751, 32.0892], [34.7789, 32.0823]]
      },
      "instructions": [
        {
          "text": "Continue straight to destination",
          "distance": 400,
          "time": 50,
          "sign": 0
        }
      ]
    }
  ],
  "summary": {
    "total_segments": 3,
    "stops_count": 2,
    "profile_used": "car",
    "breakdown_by_type": {
      "start_to_stop": {
        "count": 1,
        "total_distance_km": 1.2,
        "total_duration_min": 3.5
      },
      "stop_to_stop": {
        "count": 1,
        "total_distance_km": 0.8,
        "total_duration_min": 2.1
      },
      "stop_to_end": {
        "count": 1,
        "total_distance_km": 0.9,
        "total_duration_min": 2.8
      }
    },
    "longest_segment": {
      "segment_index": 0,
      "segment_type": "start_to_stop",
      "distance_km": 1.2,
      "duration_min": 3.5,
      "from": "Hotel Start",
      "to": "Museum"
    },
    "shortest_segment": {
      "segment_index": 1,
      "segment_type": "stop_to_stop", 
      "distance_km": 0.8,
      "duration_min": 2.1,
      "from": "Museum",
      "to": "Restaurant"
    }
  }
}
```

## 🔧 **Segment Types**

| Type | Description |
|------|-------------|
| `start_to_stop` | From starting point to first stop |
| `stop_to_stop` | Between consecutive stops |
| `stop_to_end` | From last stop to ending point |
| `start_to_end` | Direct route (when no stops) |

## 📊 **Response Fields**

### **Main Response**
| Field | Type | Description |
|-------|------|-------------|
| `trip_id` | string | Trip identifier |
| `day_id` | string | Day identifier |
| `total_distance_km` | number | Total distance for entire day |
| `total_duration_min` | number | Total duration for entire day |
| `segments` | RouteSegment[] | Individual route segments |
| `summary` | object | Additional summary information |
| `computed_at` | datetime | When breakdown was computed |

### **RouteSegment**
| Field | Type | Description |
|-------|------|-------------|
| `from_point` | RoutePoint | Starting point of segment |
| `to_point` | RoutePoint | Ending point of segment |
| `distance_km` | number | Segment distance in kilometers |
| `duration_min` | number | Segment duration in minutes |
| `geometry` | GeoJSON | Route geometry (LineString) |
| `instructions` | object[] | Turn-by-turn instructions |
| `segment_type` | string | Type of segment |
| `segment_index` | number | Order index (0-based) |

## ❌ **Error Responses**

### **400 Bad Request**
```json
{
  "detail": "Start point is required"
}
```

### **404 Not Found**
```json
{
  "detail": "Day not found"
}
```

### **500 Internal Server Error**
```json
{
  "detail": "Failed to compute route breakdown: Routing service unavailable"
}
```

## 🧪 **Example Usage**

### **cURL Example**
```bash
curl -X POST "http://localhost:8000/routing/days/route-breakdown" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "trip_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
    "day_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
    "start": {"lat": 32.0853, "lon": 34.7818, "name": "Hotel"},
    "stops": [
      {"lat": 32.0944, "lon": 34.7806, "name": "Museum"},
      {"lat": 32.0892, "lon": 34.7751, "name": "Restaurant"}
    ],
    "end": {"lat": 32.0823, "lon": 34.7789, "name": "Hotel"},
    "profile": "car"
  }'
```

### **JavaScript Example**
```javascript
const response = await fetch('/routing/days/route-breakdown', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'
  },
  body: JSON.stringify({
    trip_id: '01K4J0CYB3YSGWDZB9N92V3ZQ4',
    day_id: '01K4J0CYB3YSGWDZB9N92V3ZQ4',
    start: { lat: 32.0853, lon: 34.7818, name: 'Hotel' },
    stops: [
      { lat: 32.0944, lon: 34.7806, name: 'Museum' },
      { lat: 32.0892, lon: 34.7751, name: 'Restaurant' }
    ],
    end: { lat: 32.0823, lon: 34.7789, name: 'Hotel' },
    profile: 'car'
  })
});

const breakdown = await response.json();
console.log(`Total: ${breakdown.total_distance_km}km, ${breakdown.total_duration_min}min`);
```

## 🎯 **Use Cases**

- **Detailed trip planning** with segment-by-segment analysis
- **Time and distance estimation** for each part of the journey
- **Route optimization** by analyzing individual segments
- **Navigation preparation** with turn-by-turn instructions
- **Travel cost calculation** based on distance breakdowns
- **Itinerary visualization** with complete route geometry

---

**This endpoint provides comprehensive routing information for complete day planning!** 🚀
