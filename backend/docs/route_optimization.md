# Route Optimization API

## Overview

The Route Optimization API provides advanced route optimization capabilities with fixed start/end points and optional fixed intermediate stops. It uses TSP (Traveling Salesman Problem) algorithms to find optimal route orders based on real road routing data.

## Endpoint

**POST** `/routing/optimize`

## Features

- ✅ **Fixed Bookends**: START and END locations remain fixed
- ✅ **Flexible Stops**: Reorder intermediate stops for optimization
- ✅ **Fixed Sequences**: Optional fixed positions for specific stops
- ✅ **Multiple Objectives**: Optimize for time or distance
- ✅ **Vehicle Profiles**: Support for car, bike, and foot routing
- ✅ **Avoidance Options**: Avoid tolls, ferries, and highways
- ✅ **Real Road Routing**: Uses GraphHopper for accurate routing
- ✅ **Route Geometry**: Returns GeoJSON LineString with coordinates
- ✅ **Comprehensive Validation**: Strong input validation and error handling
- ✅ **Deterministic Results**: Same input produces same output

## Request Schema

```json
{
  "prompt": "string (optional)",
  "meta": {
    "version": "1.0",
    "objective": "time|distance",
    "vehicle_profile": "car|bike|foot",
    "units": "metric|imperial",
    "avoid": ["tolls", "ferries", "highways"]
  },
  "data": {
    "locations": [
      {
        "id": "string (unique)",
        "type": "START|STOP|END",
        "name": "string",
        "lat": number,
        "lng": number,
        "fixed_seq": boolean,
        "seq": integer
      }
    ]
  }
}
```

### Validation Rules

- **Exactly one START and one END** location required
- **All IDs must be unique**
- **Coordinates**: lat ∈ [-90, 90], lng ∈ [-180, 180]
- **Fixed sequences**: If `fixed_seq=true` for STOP, `seq` is required
- **No sequence conflicts**: Fixed sequence numbers must be unique
- **START sequence**: If present, must be 1
- **END sequence**: Should not have seq unless enforced as last

## Response Schema

```json
{
  "version": "1.0",
  "objective": "time|distance",
  "units": "metric|imperial",
  "ordered": [
    {
      "seq": integer,
      "id": "string",
      "type": "START|STOP|END",
      "name": "string",
      "lat": number,
      "lng": number,
      "fixed_seq": boolean,
      "eta_min": number,
      "leg_distance_km": number,
      "leg_duration_min": number
    }
  ],
  "summary": {
    "stop_count": integer,
    "total_distance_km": number,
    "total_duration_min": number
  },
  "geometry": {
    "format": "geojson",
    "route": {
      "type": "LineString",
      "coordinates": [[lng, lat], ...]
    },
    "bounds": {
      "min_lat": number,
      "min_lng": number,
      "max_lat": number,
      "max_lng": number
    }
  },
  "diagnostics": {
    "warnings": ["string"],
    "assumptions": ["string"],
    "computation_notes": ["string"]
  },
  "errors": []
}
```

## Example Request

```bash
curl -X POST "https://mytrips-api.bahar.co.il/routing/optimize" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "prompt": "Optimize for minimum travel time",
    "meta": {
      "version": "1.0",
      "objective": "time",
      "vehicle_profile": "car",
      "units": "metric",
      "avoid": ["tolls"]
    },
    "data": {
      "locations": [
        {
          "id": "start-1",
          "type": "START",
          "name": "Tel Aviv Central",
          "lat": 32.0853,
          "lng": 34.7818,
          "fixed_seq": true,
          "seq": 1
        },
        {
          "id": "stop-1",
          "type": "STOP",
          "name": "Ramat Gan",
          "lat": 32.0944,
          "lng": 34.7806,
          "fixed_seq": false
        },
        {
          "id": "stop-2",
          "type": "STOP",
          "name": "Petah Tikva",
          "lat": 32.0878,
          "lng": 34.8878,
          "fixed_seq": false
        },
        {
          "id": "end-1",
          "type": "END",
          "name": "Jerusalem",
          "lat": 31.7683,
          "lng": 35.2137,
          "fixed_seq": true
        }
      ]
    }
  }'
```

## Error Responses

### 400 Bad Request
```json
{
  "version": "1.0",
  "errors": [
    {"code": "MULTIPLE_START", "message": "More than one START provided"},
    {"code": "MISSING_END", "message": "No END provided"},
    {"code": "FIXED_CONFLICT", "message": "Fixed stop sequences conflict"},
    {"code": "INVALID_COORDS", "message": "Invalid coordinates"},
    {"code": "SCHEMA_VALIDATION", "message": "Payload validation failed"}
  ]
}
```

### 422 Unprocessable Entity
```json
{
  "version": "1.0",
  "errors": [
    {"code": "DISCONNECTED_GRAPH", "message": "Locations not routable"}
  ]
}
```

## Algorithm Details

### TSP Optimization
1. **Nearest Neighbor Construction**: Build initial tour using nearest neighbor heuristic
2. **2-opt Improvement**: Apply 2-opt swaps to improve tour quality
3. **Fixed Constraint Handling**: Preserve fixed stops at specified positions
4. **Deterministic Tie-breaking**: Use lexicographic ordering for consistent results

### Routing Integration
- **Primary**: GraphHopper self-hosted for accurate routing
- **Fallback**: Haversine distance estimation if routing unavailable
- **Matrix Support**: Uses distance/time matrices when available
- **Geometry**: Returns actual route geometry with turn-by-turn data

## Security & Performance

### Authentication
- **Required**: Bearer JWT token
- **Rate Limiting**: Applied per user
- **Input Sanitization**: All string inputs sanitized

### Performance
- **Timeout Protection**: 30-second routing timeout
- **Memory Efficient**: Streaming geometry processing
- **Concurrent Safe**: Thread-safe optimization algorithms
- **Caching**: Route previews cached for repeated requests

### Robustness
- **Graceful Degradation**: Falls back to haversine if routing fails
- **Error Recovery**: Comprehensive error handling and logging
- **Idempotent**: Same input always produces same output
- **Validation**: Multi-layer input validation

## Testing

Run the test suite:
```bash
# Unit tests
pytest backend/tests/test_route_optimization.py -v

# Integration test
python backend/tools/test_route_optimization.py
```

## Use Cases

1. **Delivery Route Optimization**: Optimize delivery stops with fixed depot
2. **Tourist Itinerary Planning**: Plan sightseeing routes with fixed hotel
3. **Service Technician Routes**: Optimize service calls with priority stops
4. **Multi-stop Trip Planning**: Plan efficient multi-destination trips

## Limitations

- **Maximum Locations**: Recommended limit of 20 locations for performance
- **Geographic Scope**: Optimized for Israel/Palestine region
- **Vehicle Profiles**: Limited to car, bike, foot (motorcycle requires premium)
- **Real-time Traffic**: Not included in current optimization

## Future Enhancements

- **Time Windows**: Support for time-constrained stops
- **Vehicle Capacity**: Multi-vehicle routing with capacity constraints
- **Real-time Traffic**: Integration with live traffic data
- **Advanced Algorithms**: Genetic algorithms for larger problem sizes
