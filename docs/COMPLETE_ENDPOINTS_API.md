# Complete Data Endpoints API Documentation

## Overview

Two new endpoints provide comprehensive nested data structures for trips, days, and stops in single API calls, eliminating the need for multiple requests.

## Endpoints

### 1. GET /trips/{trip_id}/days/complete
**Get all days with all stops for a trip**

### 2. GET /trips/{trip_id}/complete
**Get complete trip data including trip details, days, and stops**

---

## 📋 Endpoint 1: GET /trips/{trip_id}/days/complete

### Description
Returns all days for a trip with complete stops information in a single request.

### URL
```
GET /trips/{trip_id}/days/complete
```

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_place` | boolean | No | false | Include place details with stops |
| `include_route_info` | boolean | No | false | Include route information |
| `status` | string | No | - | Filter days by status (active, completed, etc.) |
| `day_limit` | integer | No | - | Limit number of days returned (1-50) |

### Response Schema
```json
{
  "trip_id": "string",
  "days": [
    {
      "id": "string",
      "trip_id": "string",
      "seq": 1,
      "status": "active",
      "rest_day": false,
      "notes": {},
      "trip_start_date": "2024-07-15",
      "calculated_date": "2024-07-15",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "deleted_at": null,
      "stops": [
        {
          "id": "string",
          "day_id": "string",
          "trip_id": "string",
          "place_id": "string",
          "seq": 1,
          "kind": "start",
          "fixed": true,
          "stop_type": "ACCOMMODATION",
          "arrival_time": "15:00:00",
          "departure_time": "09:00:00",
          "duration_minutes": 720,
          "priority": 1,
          "notes": "Hotel check-in",
          "place": {
            "id": "string",
            "name": "Grand Hotel",
            "address": "123 Main St, Tel Aviv",
            "latitude": 32.0853,
            "longitude": 34.7818
          },
          "created_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      ],
      "stops_count": 3,
      "has_route": true
    }
  ],
  "total_days": 2,
  "total_stops": 4
}
```

### Example Request
```bash
curl -X GET "https://api.example.com/trips/01K4J0CYB3YSGWDZB9N92V3ZQ4/days/complete?include_place=true" \
  -H "Authorization: Bearer your-token"
```

---

## 📋 Endpoint 2: GET /trips/{trip_id}/complete

### Description
Returns comprehensive trip information including trip details, all days, and all stops.

### URL
```
GET /trips/{trip_id}/complete
```

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_place` | boolean | No | false | Include place details with stops |
| `include_route_info` | boolean | No | false | Include route information |
| `status` | string | No | - | Filter days by status |
| `day_limit` | integer | No | - | Limit number of days returned (1-50) |

### Response Schema
```json
{
  "trip": {
    "id": "string",
    "slug": "summer-road-trip-2024",
    "title": "Summer Road Trip 2024",
    "destination": "Israel",
    "start_date": "2024-07-15",
    "timezone": "Asia/Jerusalem",
    "status": "active",
    "is_published": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "created_by_user": {
      "id": "string",
      "email": "user@example.com",
      "name": "John Doe"
    }
  },
  "days": [
    {
      "id": "string",
      "seq": 1,
      "status": "active",
      "calculated_date": "2024-07-15",
      "stops": [
        {
          "seq": 1,
          "kind": "start",
          "stop_type": "ACCOMMODATION",
          "place": {
            "name": "Grand Hotel",
            "address": "123 Main St, Tel Aviv"
          }
        }
      ],
      "stops_count": 3,
      "has_route": true
    }
  ],
  "summary": {
    "total_days": 2,
    "total_stops": 4,
    "trip_duration_days": 7,
    "status_breakdown": {
      "active": 2,
      "completed": 0
    },
    "stop_type_breakdown": {
      "ACCOMMODATION": 2,
      "ATTRACTION": 1,
      "RESTAURANT": 1
    }
  }
}
```

### Example Request
```bash
curl -X GET "https://api.example.com/trips/01K4J0CYB3YSGWDZB9N92V3ZQ4/complete?include_place=true" \
  -H "Authorization: Bearer your-token"
```

---

## 🔧 Features

### Data Ordering
- **Days**: Ordered by sequence (1, 2, 3, ...)
- **Stops**: Ordered by sequence within each day (START → VIA → END)

### Performance Optimizations
- Single database queries with eager loading
- Efficient joins for place information
- Optimized data grouping and processing

### Filtering Options
- Filter days by status
- Limit number of days returned
- Optional place information inclusion
- Optional route information inclusion

### Response Features
- Complete nested data structure
- Summary statistics and breakdowns
- Proper ISO-8601 datetime formatting
- Comprehensive error handling

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid day status: invalid_status"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Trip not found"
}
```

---

## 🎯 Use Cases

### Frontend Applications
- Display complete trip overview in single request
- Render trip timeline with all stops
- Show trip summary statistics
- Build trip planning interfaces

### Mobile Applications
- Reduce network requests for better performance
- Offline-capable trip data caching
- Complete trip synchronization

### Data Export/Reporting
- Generate comprehensive trip reports
- Export complete trip data
- Analytics and statistics generation

---

## 🔄 Migration from Multiple Endpoints

### Before (Multiple Requests)
```bash
# Get trip details
GET /trips/{trip_id}

# Get all days
GET /trips/{trip_id}/days

# Get stops for each day
GET /trips/{trip_id}/days/{day_1_id}/stops
GET /trips/{trip_id}/days/{day_2_id}/stops
GET /trips/{trip_id}/days/{day_3_id}/stops
```

### After (Single Request)
```bash
# Get everything in one request
GET /trips/{trip_id}/complete?include_place=true
```

### Benefits
- **Reduced Network Requests**: 1 request instead of N+2
- **Better Performance**: Single optimized query
- **Atomic Data**: Consistent snapshot of trip data
- **Simplified Client Code**: No complex data merging logic
