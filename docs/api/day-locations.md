# Adding Locations to a Day

This document describes how to add locations (start, end, or intermediate stops) to a day in a trip.

## Overview

To add a location to a day, you work with **Stops**. In your system:
- **START** = Day's starting location (seq=1, fixed=true)
- **END** = Day's ending location (fixed=true)
- **VIA** = Intermediate stops along the route

## Architecture

Days don't directly store start/end locations. Instead, they're represented as **Stops** with specific `kind` values:
- Each stop references a **Place** (via `place_id`)
- Places store the actual location data (name, address, lat/lon)
- Stops define the role and sequence of that place in the day's itinerary

### Stop Kinds

| Kind | Description | Constraints |
|------|-------------|-------------|
| `START` | Starting point of the route | Must be seq=1, fixed=true |
| `VIA` | Intermediate waypoint | Can be optimized (fixed=false) |
| `END` | Final destination | Must be fixed=true |

### Stop Types

Available stop types for categorization:
- `ACCOMMODATION` - Hotels, hostels, camping
- `FOOD` - Restaurants, cafes, food stops
- `ATTRACTION` - Museums, landmarks, tourist sites
- `SHOPPING` - Markets, malls, stores
- `TRANSPORT` - Airports, train stations, bus terminals
- `ACTIVITY` - Sports, adventures, experiences
- `SCENIC` - Viewpoints, photo spots, natural beauty
- `NIGHTLIFE` - Bars, clubs, entertainment venues
- `OTHER` - Miscellaneous stops

---

## Step-by-Step Flow

### Step 1: Create or Get the Place

First, ensure the location exists as a Place in the database.

#### Endpoint
```
POST /places
```

#### Request Body

```json
{
  "name": "Grand Hotel Tel Aviv",
  "address": "123 Main St, Tel Aviv, Israel",
  "lat": 32.0853,
  "lon": 34.7818,
  "meta": {
    "raw": {
      "id": "maptiler_feature_id_123",
      "place_id": "google_place_id_xyz"
    }
  }
}
```

#### Required Fields

| Field | Type | Range/Format | Description |
|-------|------|--------------|-------------|
| `name` | string | 1-255 chars | Place name |
| `lat` | float | -90 to 90 | Latitude |
| `lon` | float | -180 to 180 | Longitude |

#### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `address` | string (max 500 chars) | Human-readable address |
| `meta` | object | Additional metadata (provider IDs, raw data, etc.) |

#### Response

```json
{
  "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
  "name": "Grand Hotel Tel Aviv",
  "address": "123 Main St, Tel Aviv, Israel",
  "lat": 32.0853,
  "lon": 34.7818,
  "meta": { ... },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### Step 2: Create the Stop

Once you have the `place_id`, create a stop for the day.

#### Endpoint
```
POST /stops/{trip_id}/days/{day_id}/stops
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `trip_id` | string | Trip identifier |
| `day_id` | string | Day identifier |

#### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `place_id` | string | ID of the place from Step 1 | `"01K4AHPK4S1KVTYDB5ASTGTM8K"` |
| `seq` | integer (> 0) | Sequence number in the day | `1` |
| `kind` | enum | One of: `"start"`, `"via"`, `"end"` | `"start"` |

#### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `fixed` | boolean | Whether stop position is fixed (default: false) | `true` |
| `stop_type` | enum | Category of stop | `"accommodation"` |
| `arrival_time` | string (ISO-8601 time) | Planned arrival time | `"14:30:00"` |
| `departure_time` | string (ISO-8601 time) | Planned departure time | `"16:00:00"` |
| `duration_minutes` | integer (> 0) | Planned duration at stop | `90` |
| `priority` | integer (1-5) | Priority level (1=must-see, 5=backup) | `1` |
| `notes` | string | Free-text notes | `"Hotel check-in at 3 PM"` |
| `booking_info` | object | Reservation details | `{"confirmation": "ABC123"}` |
| `contact_info` | object | Phone, website, email | `{"phone": "+972-3-1234567"}` |
| `cost_info` | object | Estimated/actual costs | `{"amount": 150, "currency": "USD"}` |

---

## Examples

### Example 1: Add START Location (Day Beginning)

```json
POST /stops/{trip_id}/days/{day_id}/stops

{
  "place_id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
  "seq": 1,
  "kind": "start",
  "fixed": true,
  "stop_type": "accommodation",
  "arrival_time": "15:00:00",
  "departure_time": "09:00:00",
  "duration_minutes": 720,
  "priority": 1,
  "notes": "Hotel check-in at 3 PM"
}
```

### Example 2: Add END Location (Day Ending)

```json
POST /stops/{trip_id}/days/{day_id}/stops

{
  "place_id": "01K4AHPK4S1KVTYDB5ASTGTM8L",
  "seq": 5,
  "kind": "end",
  "fixed": true,
  "stop_type": "accommodation",
  "arrival_time": "18:00:00",
  "priority": 1,
  "notes": "Hotel check-in"
}
```

### Example 3: Add VIA Stop (Intermediate Stop)

```json
POST /stops/{trip_id}/days/{day_id}/stops

{
  "place_id": "01K4AHPK4S1KVTYDB5ASTGTM8M",
  "seq": 2,
  "kind": "via",
  "fixed": false,
  "stop_type": "food",
  "arrival_time": "12:30:00",
  "departure_time": "14:00:00",
  "duration_minutes": 90,
  "priority": 2,
  "notes": "Lunch at local restaurant"
}
```

---

## Important Constraints

### START Stops
- ✅ Must have `seq = 1`
- ✅ Must have `fixed = true`
- ✅ Only one START per day

### END Stops
- ✅ Must have `fixed = true`
- ✅ Can be any seq > 1

### VIA Stops
- ✅ Can have any seq > 1
- ✅ Typically `fixed = false` (allows route optimization)

### Sequence Numbers
- ✅ Must be unique within a day
- ✅ Must be > 0

---

## Automatic Behaviors

After creating a stop, the system **automatically**:

1. **Computes an optimized route** for the day
2. **Commits it as the default route**
3. **If you created an END stop**, it creates a START stop for the next day (inheriting the END location)

This ensures that:
- Routes are always up-to-date
- Day transitions are seamless (Day N's end = Day N+1's start)
- No manual route computation is needed

---

## Updating an Existing Stop

### Endpoint
```
PATCH /stops/{trip_id}/days/{day_id}/stops/{stop_id}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `trip_id` | string | Trip identifier |
| `day_id` | string | Day identifier |
| `stop_id` | string | Stop identifier |

### Request Body (Partial Update)

All fields are optional. Only include fields you want to update.

```json
{
  "place_id": "01K4AHPK4S1KVTYDB5ASTGTM8N",
  "arrival_time": "13:00:00",
  "notes": "Updated arrival time"
}
```

### Example

```bash
PATCH /stops/{trip_id}/days/{day_id}/stops/{stop_id}

{
  "arrival_time": "13:00:00",
  "duration_minutes": 120,
  "notes": "Extended lunch duration"
}
```

---

## Complete JavaScript Example

### Adding a Day with Start and End

```javascript
// 1. Create start place
const startPlace = await fetch('/places', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    name: "Tel Aviv Hotel",
    address: "123 Dizengoff St, Tel Aviv",
    lat: 32.0853,
    lon: 34.7818
  })
});
const startPlaceData = await startPlace.json();

// 2. Create end place
const endPlace = await fetch('/places', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    name: "Jerusalem Hotel",
    address: "456 King David St, Jerusalem",
    lat: 31.7683,
    lon: 35.2137
  })
});
const endPlaceData = await endPlace.json();

// 3. Create START stop
const startStop = await fetch(`/stops/${tripId}/days/${dayId}/stops`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    place_id: startPlaceData.id,
    seq: 1,
    kind: "start",
    fixed: true,
    stop_type: "accommodation",
    departure_time: "09:00:00"
  })
});

// 4. Create END stop
const endStop = await fetch(`/stops/${tripId}/days/${dayId}/stops`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    place_id: endPlaceData.id,
    seq: 2,
    kind: "end",
    fixed: true,
    stop_type: "accommodation",
    arrival_time: "18:00:00"
  })
});

// 5. Add intermediate stops (optional)
const viaStop = await fetch(`/stops/${tripId}/days/${dayId}/stops`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    place_id: "01K4AHPK4S1KVTYDB5ASTGTM8M",
    seq: 2,  // Will shift END to seq=3 automatically
    kind: "via",
    fixed: false,
    stop_type: "attraction",
    arrival_time: "11:00:00",
    departure_time: "13:00:00",
    duration_minutes: 120,
    priority: 2,
    notes: "Visit museum"
  })
});
```

---

## Retrieving Day Locations

### Get Days with Locations Summary

#### Endpoint
```
GET /days/summary?trip_id={trip_id}
```

#### Response

```json
{
  "days": [
    {
      "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
      "trip_id": "01K367ED2RPNS2H19J8PQDNXFB",
      "seq": 1,
      "status": "ACTIVE",
      "rest_day": false,
      "calculated_date": "2024-07-15"
    }
  ],
  "locations": [
    {
      "day_id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
      "start": {
        "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
        "name": "Tel Aviv Hotel",
        "address": "123 Dizengoff St, Tel Aviv",
        "lat": 32.0853,
        "lon": 34.7818
      },
      "end": {
        "id": "01K4AHPK4S1KVTYDB5ASTGTM8L",
        "name": "Jerusalem Hotel",
        "address": "456 King David St, Jerusalem",
        "lat": 31.7683,
        "lon": 35.2137
      },
      "route_total_km": 65.4,
      "route_total_min": 78.5
    }
  ]
}
```

---

## Error Handling

### Common Errors

#### 400 Bad Request - Invalid Sequence

```json
{
  "detail": "START stops must have seq=1"
}
```

#### 400 Bad Request - Duplicate Sequence

```json
{
  "detail": "A stop with sequence number 2 already exists for this day"
}
```

#### 404 Not Found - Invalid Place

```json
{
  "detail": "Place not found"
}
```

#### 403 Forbidden - Not Trip Owner

```json
{
  "detail": "You must be the trip owner to modify stops"
}
```

---

## Best Practices

### 1. Always Create Places First
Before creating stops, ensure the place exists in the database. This allows:
- Reuse of places across multiple trips
- Consistent location data
- Better search and autocomplete

### 2. Use Proper Sequence Numbers
- START: Always seq=1
- VIA: seq=2, 3, 4, ...
- END: Last sequence number

### 3. Set Fixed Appropriately
- START and END: Always `fixed=true`
- VIA: Use `fixed=false` for flexible stops that can be reordered during optimization

### 4. Leverage Automatic Route Computation
The system automatically computes and commits routes after stop creation/update. No manual intervention needed.

### 5. Use Stop Types for Better Organization
Categorize stops with appropriate `stop_type` values for:
- Better UI filtering and display
- Route optimization hints
- Trip planning insights

### 6. Include Timing Information
Provide `arrival_time`, `departure_time`, and `duration_minutes` for:
- Realistic route planning
- Time-based optimization
- Schedule conflict detection

---

## Summary

**To add a location to a day:**

1. **Create/get the Place** → `POST /places` → Get `place_id`
2. **Create the Stop** → `POST /stops/{trip_id}/days/{day_id}/stops` with:
   - `place_id` from step 1
   - `kind`: `"start"`, `"end"`, or `"via"`
   - `seq`: Position in the day (START must be 1)
   - `fixed`: `true` for START/END, `false` for VIA
   - Optional: times, duration, type, notes, etc.

The system automatically computes and commits the route after each stop creation/update.

**Key Constraints:**
- START stops: seq=1, fixed=true
- END stops: fixed=true
- VIA stops: seq>1, typically fixed=false
- Sequence numbers must be unique within a day

**Automatic Behaviors:**
- Route computation and commit after stop changes
- Next day's START creation when END is added
