# Address Search Autocomplete API

This document describes the endpoints available for address and place search autocomplete functionality.

## Overview

Your system provides **two main endpoints** for address/place search:

1. **Type-ahead Suggestions** (`/places/v1/places/suggest`) - Fast autocomplete for UI
2. **Full Place Search** (`/places/v1/places/search`) - Comprehensive search with details

---

## 1. Type-ahead Suggestions (Recommended for Autocomplete)

### Endpoint
```
GET /places/v1/places/suggest
```

### Purpose
Fast, lightweight autocomplete suggestions while the user is typing. Optimized for real-time performance (target <120ms).

### Key Features
- ⚡ **Fast Response**: Optimized for real-time typing
- 🎯 **Proximity Bias**: Results prioritized by distance from lat/lng
- 🏷️ **Category Filtering**: Filter by hotel, restaurant, museum, address, etc.
- 🌍 **Geographic Filtering**: Limit results to specific countries or bounding box
- ✨ **Text Highlighting**: Matching text highlighted with `<b>` tags for UI
- 🔗 **Session Management**: Group related requests with session tokens

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (minimum 1 character) | `"montef"` |
| `session_token` | string | Session token for grouping requests | `"st_abc123"` |

### Optional Parameters

| Parameter | Type | Range/Format | Description | Example |
|-----------|------|--------------|-------------|---------|
| `lat` | float | -90 to 90 | User latitude for proximity bias | `32.07` |
| `lng` | float | -180 to 180 | User longitude for proximity bias | `34.78` |
| `radius` | integer | 1-50000 | Bias radius in meters | `5000` |
| `bbox` | string | `minLon,minLat,maxLon,maxLat` | Bounding box filter | `"34.7,32.0,34.8,32.1"` |
| `countries` | string | ISO-3166-1 alpha-2 codes | Comma-separated country codes | `"IL,US"` |
| `categories` | string | Category names | Comma-separated filters | `"hotel,restaurant,museum"` |
| `lang` | string | BCP-47 code | Language code (default: `"en"`) | `"en"` |
| `limit` | integer | 1-20 | Maximum results (default: 8) | `8` |

### Example Request

```bash
GET /places/v1/places/suggest?q=montef&lat=32.07&lng=34.78&radius=5000&countries=IL&categories=hotel&session_token=st_123
```

### Response Format

```json
{
  "session_token": "st_123",
  "suggestions": [
    {
      "id": "place_001",
      "name": "Hotel Montefiore",
      "highlighted": "Hotel <b>Montef</b>iore",
      "formatted_address": "36 Montefiore St, Tel Aviv, Israel",
      "types": ["lodging"],
      "center": {
        "lat": 32.0753,
        "lng": 34.7818
      },
      "distance_m": 450,
      "confidence": 0.95,
      "source": "internal"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_token` | string | Echo of the request session token |
| `suggestions` | array | List of place suggestions |
| `suggestions[].id` | string | Unique place identifier |
| `suggestions[].name` | string | Place name |
| `suggestions[].highlighted` | string | Name with `<b>` tags for matching text |
| `suggestions[].formatted_address` | string | Human-readable address |
| `suggestions[].types` | array | Place type categories |
| `suggestions[].center` | object | Geographic coordinates `{lat, lng}` |
| `suggestions[].distance_m` | integer | Distance from query point in meters (if lat/lng provided) |
| `suggestions[].confidence` | float | Confidence score 0-1 |
| `suggestions[].source` | string | Data source identifier |

### Usage Pattern

1. **Create a new session_token** when user focuses on search input
2. **Send requests** with same session_token for each keystroke
3. **Debounce requests** by 150-250ms for optimal performance
4. **Use returned suggestions** to populate dropdown/autocomplete UI
5. **Reset session_token** when input loses focus or user selects a result

### JavaScript Example

```javascript
// 1. Generate session token when input is focused
let sessionToken = `st_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// 2. Debounced autocomplete function
const debounce = (fn, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

// 3. Fetch suggestions
const fetchSuggestions = async (query, userLat, userLng) => {
  if (query.length < 1) return;

  const params = new URLSearchParams({
    q: query,
    session_token: sessionToken,
    limit: 8
  });

  if (userLat && userLng) {
    params.append('lat', userLat);
    params.append('lng', userLng);
    params.append('radius', 5000);
  }

  const response = await fetch(`/places/v1/places/suggest?${params}`);
  const data = await response.json();

  // Render suggestions in dropdown
  renderSuggestions(data.suggestions);
};

// 4. Attach to input with debouncing
const debouncedFetch = debounce(fetchSuggestions, 200);

searchInput.addEventListener('input', (e) => {
  debouncedFetch(e.target.value, userLat, userLng);
});

// 5. Reset session token when input loses focus
searchInput.addEventListener('blur', () => {
  sessionToken = `st_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
});
```

---

## 2. Full Place Search

### Endpoint
```
GET /places/v1/places/search
```

### Purpose
Comprehensive search with full details, metadata, and comprehensive information suitable for mapping, display, and detailed place information.

### Key Features
- Complete place details with contact information
- Geographic coordinates and bounding boxes
- Categories, ratings, and popularity scores
- Timezone and metadata for each place
- Pagination tokens for large result sets

### Use Cases
- Final search results after user selects from type-ahead suggestions
- Comprehensive place discovery and exploration
- Detailed place information for trip planning
- Geographic search within specific areas or countries

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (minimum 1 character) | `"hotel montefiore"` |

### Optional Parameters

| Parameter | Type | Range/Format | Description | Example |
|-----------|------|--------------|-------------|---------|
| `lat` | float | -90 to 90 | User latitude for proximity bias | `32.07` |
| `lng` | float | -180 to 180 | User longitude for proximity bias | `34.78` |
| `radius` | integer | 1-50000 | Bias radius in meters | `10000` |
| `bbox` | string | `minLon,minLat,maxLon,maxLat` | Bounding box filter | `"34.7,32.0,34.8,32.1"` |
| `countries` | string | ISO-3166-1 alpha-2 codes | Comma-separated country codes | `"IL,US"` |
| `categories` | string | Category names | Comma-separated filters | `"hotel,restaurant"` |
| `lang` | string | BCP-47 code | Language code (default: `"en"`) | `"en"` |
| `limit` | integer | 1+ | Maximum results per page | `10` |
| `offset` | integer | 0+ | Result offset for pagination | `0` |
| `open_now` | boolean | true/false | Filter for currently open POIs | `true` |
| `sort` | string | `relevance`, `distance`, `rating`, `popularity` | Sort order (default: `relevance`) | `"rating"` |

### Example Request

```bash
GET /places/v1/places/search?q=museum&lat=32.07&lng=34.78&countries=IL&sort=rating&limit=10
```

### Response Format

```json
{
  "results": [
    {
      "id": "place_002",
      "name": "Tel Aviv Museum of Art",
      "formatted_address": "27 Shaul Hamelech Blvd, Tel Aviv, Israel",
      "types": ["museum", "attraction"],
      "center": {
        "lat": 32.0776,
        "lng": 34.7831
      },
      "bbox": {
        "min_lat": 32.0770,
        "min_lng": 34.7825,
        "max_lat": 32.0782,
        "max_lng": 34.7837
      },
      "score": 0.92
    }
  ],
  "page_token": "page_10_1234567890",
  "total_count": 45
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | List of search results |
| `results[].id` | string | Unique place identifier |
| `results[].name` | string | Place name |
| `results[].formatted_address` | string | Human-readable address |
| `results[].types` | array | Place type categories |
| `results[].center` | object | Geographic coordinates `{lat, lng}` |
| `results[].bbox` | object | Bounding box (if available) |
| `results[].score` | float | Relevance score |
| `page_token` | string | Token for next page (if more results available) |
| `total_count` | integer | Total available results |

---

## 3. Legacy Search Endpoint (MapTiler-based)

### Endpoint
```
GET /places/search
```

### Purpose
Older search endpoint using MapTiler geocoding API with aggressive caching (5-minute TTL).

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Search term (minimum 2 characters) | `"tel aviv"` |

### Optional Parameters

| Parameter | Type | Range/Format | Description | Example |
|-----------|------|--------------|-------------|---------|
| `lat` | float | -90 to 90 | Latitude for proximity search | `32.07` |
| `lon` | float | -180 to 180 | Longitude for proximity search | `34.78` |
| `radius` | integer | 1+ | Search radius in meters (default: 50000) | `50000` |
| `limit` | integer | 1-50 | Maximum results (default: 10) | `10` |
| `format` | string | `legacy`, `modern` | Response format (default: `modern`) | `"modern"` |

### Example Request

```bash
GET /places/search?query=tel+aviv&lat=32.07&lon=34.78&radius=50000&limit=10&format=modern
```

### Features
- Aggressive caching (5-minute TTL) for improved performance
- Proximity-based search with lat/lon parameters
- Integration with user's saved places
- Modern pagination with navigation links

---

## Comparison Table

| Feature | `/suggest` (Autocomplete) | `/search` (Full Search) | `/places/search` (Legacy) |
|---------|---------------------------|-------------------------|---------------------------|
| **Speed** | <120ms target | Slower, comprehensive | Cached (5-min TTL) |
| **Min Query Length** | 1 character | 1 character | 2 characters |
| **Highlighted Text** | ✅ Yes (`<b>` tags) | ❌ No | ❌ No |
| **Session Token** | ✅ Required | ❌ Not used | ❌ Not used |
| **Max Results** | 1-20 (default 8) | Configurable with pagination | 1-50 (default 10) |
| **Proximity Bias** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Category Filtering** | ✅ Yes | ✅ Yes | ❌ No |
| **Country Filtering** | ✅ Yes | ✅ Yes | ❌ No |
| **Sorting Options** | ❌ No (by relevance) | ✅ Yes (relevance, distance, rating, popularity) | ❌ No |
| **Use Case** | Real-time typing | Final results, detailed info | General search with caching |

---

## Recommendations

### **For Autocomplete UI (Recommended):**

✅ **Use:** `GET /places/v1/places/suggest`

**Why:**
- ⚡ Optimized for real-time typing (target <120ms)
- ✨ Highlighted matching text with `<b>` tags
- 🎯 Proximity-based ranking
- 🔗 Session management for grouping requests
- 🏷️ Category and country filtering

### **For Full Search Results:**

✅ **Use:** `GET /places/v1/places/search`

**Why:**
- Complete place details
- Pagination support
- Multiple sort options (relevance, distance, rating)
- Comprehensive metadata

### **For Cached General Search:**

✅ **Use:** `GET /places/search`

**Why:**
- 5-minute caching for repeated queries
- MapTiler geocoding API integration
- Modern pagination support
- Good for general search without advanced filtering

---

## Rate Limiting

The `/suggest` endpoint includes rate limiting to prevent abuse:
- **Limit:** Configurable per IP address
- **Response:** HTTP 429 with `retry_after_ms` field when limit exceeded
- **Recommendation:** Implement client-side debouncing (150-250ms) to stay within limits

---

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error_code": "BAD_REQUEST",
  "message": "Both lat and lng must be provided together",
  "status": 400,
  "retry_after_ms": null
}
```

Common error codes:
- `BAD_REQUEST` (400) - Invalid parameters
- `RATE_LIMIT` (429) - Too many requests
- `BACKEND_UNAVAILABLE` (500) - Internal server error
