# Short Format API Documentation

## Overview

The short format provides a compact representation of trips with essential information and day-by-day summaries. This format is optimized for mobile applications and overview interfaces where you need trip structure information without full details.

## Endpoint

### GET /trips?format=short
**Get trips in compact format with day summaries**

---

## 📋 Request Format

### URL
```
GET /trips?format=short
```

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `format` | string | Yes | - | Must be "short" |
| `status` | string | No | - | Filter by trip status (draft, active, completed, archived) |
| `owner` | string | No | current user | Filter by owner ID |
| `page` | integer | No | 1 | Page number (starts at 1) |
| `size` | integer | No | 20 | Number of trips per page (1-100) |
| `sort_by` | string | No | created_at:desc | Sort by field:direction |

### Example Request
```bash
curl -X GET "https://api.example.com/trips?format=short&page=1&size=10" \
  -H "Authorization: Bearer your-token"
```

---

## 📋 Response Format

### Response Schema
```json
{
  "data": [
    {
      "slug": "summer-road-trip-2024",
      "title": "Summer Road Trip 2024",
      "destination": "Europe",
      "start_date": "2024-07-15",
      "timezone": "Europe/London",
      "status": "active",
      "is_published": false,
      "created_by": "01K5P68329YFSCTV777EB4GM9P",
      "members": [],
      "total_days": 3,
      "days": [
        {
          "day": 1,
          "start": true,
          "stops": 4,
          "end": true
        },
        {
          "day": 2,
          "start": true,
          "stops": 3,
          "end": true
        },
        {
          "day": 3,
          "start": true,
          "stops": 2,
          "end": true
        }
      ]
    }
  ],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false,
    "from_item": 1,
    "to_item": 1
  },
  "links": {
    "first": "/trips?format=short&page=1",
    "last": "/trips?format=short&page=1",
    "prev": null,
    "next": null
  }
}
```

---

## 🔧 Field Descriptions

### Trip Fields
| Field | Type | Description |
|-------|------|-------------|
| `slug` | string | URL-friendly trip identifier |
| `title` | string | Trip title |
| `destination` | string\|null | Trip destination |
| `start_date` | string\|null | Trip start date (ISO-8601) |
| `timezone` | string\|null | Trip timezone |
| `status` | string | Trip status (draft, active, completed, archived) |
| `is_published` | boolean | Whether trip is published |
| `created_by` | string | User ID who created the trip |
| `members` | array | List of member user IDs |
| `total_days` | integer | Total number of days in the trip |
| `days` | array | Day summaries (see below) |

### Day Summary Fields
| Field | Type | Description |
|-------|------|-------------|
| `day` | integer | Day sequence number (1, 2, 3...) |
| `start` | boolean | Whether day has a start stop |
| `stops` | integer | Total number of stops in this day |
| `end` | boolean | Whether day has an end stop |

---

## 🎯 Use Cases

### Mobile Applications
- **Trip List View**: Show trip cards with day counts and structure
- **Quick Overview**: Instant visibility into trip planning status
- **Reduced Bandwidth**: Smaller payload for mobile networks
- **Offline Sync**: Compact data for offline storage

### Dashboard Interfaces
- **Trip Management**: Overview of all trips with planning status
- **Progress Tracking**: See which days have start/end stops configured
- **Planning Status**: Identify incomplete trip planning

### API Integration
- **Third-party Apps**: Provide trip summaries to external services
- **Reporting**: Generate trip statistics and summaries
- **Data Export**: Compact format for data exports

---

## 🔄 Format Comparison

### Short vs Modern vs Legacy

| Feature | Short | Modern | Legacy |
|---------|-------|--------|--------|
| **Trip Basic Info** | ✅ | ✅ | ✅ |
| **Day Summaries** | ✅ | ❌ | ❌ |
| **Stop Details** | ❌ | ❌ | ❌ |
| **Pagination** | ✅ | ✅ | ✅ |
| **Navigation Links** | ✅ | ✅ | ❌ |
| **Payload Size** | Small | Medium | Medium |
| **Use Case** | Overview | General | Legacy |

### Example Comparison

#### Short Format
```json
{
  "title": "Summer Trip",
  "total_days": 2,
  "days": [
    {"day": 1, "start": true, "stops": 3, "end": true},
    {"day": 2, "start": true, "stops": 2, "end": false}
  ]
}
```

#### Modern Format
```json
{
  "title": "Summer Trip",
  "start_date": "2024-07-15",
  "status": "active"
  // No day information
}
```

---

## 📊 Response Examples

### Single Trip Response
```json
{
  "data": [
    {
      "slug": "weekend-getaway",
      "title": "Weekend Getaway",
      "destination": "Napa Valley",
      "start_date": "2024-08-15",
      "timezone": "America/Los_Angeles",
      "status": "active",
      "is_published": false,
      "created_by": "01K5P68329YFSCTV777EB4GM9P",
      "members": [],
      "total_days": 2,
      "days": [
        {
          "day": 1,
          "start": true,
          "stops": 5,
          "end": true
        },
        {
          "day": 2,
          "start": true,
          "stops": 3,
          "end": true
        }
      ]
    }
  ]
}
```

### Empty Response
```json
{
  "data": [],
  "meta": {
    "current_page": 1,
    "per_page": 20,
    "total_items": 0,
    "total_pages": 0
  }
}
```

### Trip with No Days
```json
{
  "data": [
    {
      "slug": "new-trip",
      "title": "New Trip",
      "destination": null,
      "start_date": null,
      "timezone": null,
      "status": "draft",
      "is_published": false,
      "created_by": "01K5P68329YFSCTV777EB4GM9P",
      "members": [],
      "total_days": 0,
      "days": []
    }
  ]
}
```

---

## 🚨 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid format parameter. Must be 'legacy', 'modern', or 'short'"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

---

## 🔧 Implementation Notes

### Performance
- Single database query with optimized joins
- Efficient grouping of stops by day
- Minimal data transfer for mobile applications

### Data Consistency
- Day summaries reflect current database state
- Start/end status based on actual stop kinds
- Stop counts include all stop types

### Ordering
- Days ordered by sequence (1, 2, 3...)
- Consistent with other API endpoints
- Predictable response structure

---

## 🧪 Testing

Use the provided test script to verify the short format:

```bash
# Test short format endpoint
python3 test_short_format.py --api-base http://localhost:8000

# Example API call
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/trips?format=short&size=5"
```

The short format provides an efficient way to get trip overviews with day structure information in a single API call! 🎉
