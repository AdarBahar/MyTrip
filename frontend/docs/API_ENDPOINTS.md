# Frontend API Endpoints

This document describes the frontend API proxy endpoints that provide access to backend services.

## Places Search API

### Type-ahead Suggestions

**Endpoint:** `GET /api/places/v1/places/suggest`

**Description:** Get fast, lightweight place suggestions for type-ahead search functionality.

**Parameters:**
- `q` (required): Search query string
- `session_token` (required): Session token for grouping requests
- `lat` (optional): User latitude for proximity bias
- `lng` (optional): User longitude for proximity bias
- `radius` (optional): Bias radius in meters
- `countries` (optional): Comma-separated ISO country codes
- `categories` (optional): Comma-separated category filters
- `lang` (optional): Language code (en, he, etc.)
- `limit` (optional): Maximum results (default: 8)

**Example Request:**
```bash
GET /api/places/v1/places/suggest?q=tel&session_token=abc123&limit=5
```

**Example Response:**
```json
{
  "session_token": "abc123",
  "suggestions": [
    {
      "id": "poi_tel_aviv_museum",
      "name": "Tel Aviv Museum of Art",
      "highlighted": "<b>Tel</b> Aviv Museum of Art",
      "formatted_address": "27 Shaul Hamelech Blvd, Tel Aviv-Yafo, Israel",
      "types": ["museum", "poi"],
      "center": {"lat": 32.0773, "lng": 34.7863},
      "distance_m": 1200,
      "confidence": 0.95,
      "source": "places_api"
    }
  ]
}
```

### Full Search

**Endpoint:** `GET /api/places/v1/places/search`

**Description:** Comprehensive place search with detailed results.

**Parameters:** Same as suggest endpoint plus:
- `page_token` (optional): Pagination token
- `offset` (optional): Result offset
- `open_now` (optional): Filter for currently open places
- `sort` (optional): Sort order (relevance, distance, rating, popularity)

### Place Details

**Endpoint:** `GET /api/places/v1/places/{id}`

**Description:** Get detailed information about a specific place.

**Parameters:**
- `id` (path): Place identifier

**Example Request:**
```bash
GET /api/places/v1/places/poi_tel_aviv_museum
```

**Example Response:**
```json
{
  "id": "poi_tel_aviv_museum",
  "name": "Tel Aviv Museum of Art",
  "formatted_address": "27 Shaul Hamelech Blvd, Tel Aviv-Yafo, Israel",
  "types": ["museum", "poi"],
  "center": {"lat": 32.0773, "lng": 34.7863},
  "categories": ["museum", "art", "culture"],
  "rating": 4.5,
  "popularity": 0.85,
  "phone": "+972-3-607-7020",
  "website": "https://www.tamuseum.org.il",
  "hours": {
    "monday": "10:00-18:00",
    "tuesday": "10:00-18:00"
  }
}
```

## Geocoding API

### Forward Geocoding

**Endpoint:** `GET /api/places/geocode`

**Description:** Convert addresses to geographic coordinates using MapTiler geocoding API.

**Parameters:**
- `address` (required): Address or location to geocode

**Example Request:**
```bash
GET /api/places/geocode?address=New York
```

**Example Response:**
```json
[
  {
    "address": "New York",
    "lat": 40.75263781837546,
    "lon": -73.99205356836319,
    "formatted_address": "New York, New York, United States",
    "place_id": "place.123456789",
    "types": ["locality", "political"]
  },
  {
    "address": "New York",
    "lat": 43.00035,
    "lon": -75.4999,
    "formatted_address": "New York, United States",
    "place_id": "place.987654321",
    "types": ["administrative_area_level_1", "political"]
  }
]
```

### Reverse Geocoding

**Endpoint:** `GET /api/places/reverse-geocode`

**Description:** Convert geographic coordinates to addresses using MapTiler reverse geocoding API.

**Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)

**Example Request:**
```bash
GET /api/places/reverse-geocode?lat=32.0853&lon=34.7818
```

**Example Response:**
```json
[
  {
    "address": "Tel Aviv",
    "lat": 32.0853,
    "lon": 34.7818,
    "formatted_address": "Tel Aviv-Yafo, Israel",
    "place_id": "place.tel_aviv",
    "types": ["locality", "political"]
  }
]
```

## Error Responses

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Address parameter is required"
}
```

**404 Not Found:**
```json
{
  "error": "Place not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Failed to geocode address"
}
```

## Authentication

All endpoints require authentication via Bearer token:

```bash
Authorization: Bearer your_token_here
```

For development, the frontend automatically includes the authentication token.

## Rate Limiting

- **Places API**: No specific rate limits (uses mock data)
- **Geocoding API**: Subject to MapTiler API rate limits
- **Caching**: Responses cached for 5 minutes

## CORS

All endpoints support CORS for frontend access from the same domain.

## Response Headers

- `Content-Type: application/json`
- `Cache-Control: public, max-age=300` (for geocoding endpoints)

## Usage Examples

### React Component Integration

```typescript
import { geocodeAddress } from '@/lib/api/places'

// Use geocoding in a component
const handleSearch = async (query: string) => {
  try {
    const results = await geocodeAddress(query)
    console.log('Geocoding results:', results)
  } catch (error) {
    console.error('Geocoding failed:', error)
  }
}
```

### Places Search Integration

```typescript
import PlacesSearch from '@/components/ui/PlacesSearch'

// Use places search component
<PlacesSearch
  useRealGeocoding={true}
  onPlaceSelect={(place) => {
    console.log('Selected place:', place)
  }}
  onCoordinatesSelect={(lat, lng, place) => {
    console.log('Coordinates:', lat, lng)
  }}
/>
```
