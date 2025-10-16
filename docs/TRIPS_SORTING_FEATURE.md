# Trips Sorting Feature

## Overview

Added sorting functionality to the `/trips` endpoint to allow ordering results by various fields and directions.

## New Parameter

### `sort_by` (optional)

- **Format**: `field:direction`
- **Default**: `created_at:desc` (newest trips first)
- **Description**: Sort trips by the specified field and direction

## Supported Sort Fields

| Field | Description | Example Values |
|-------|-------------|----------------|
| `created_at` | Trip creation timestamp | `2024-01-15T10:30:00Z` |
| `updated_at` | Last update timestamp | `2024-01-16T14:20:00Z` |
| `title` | Trip title | `"Summer Road Trip 2024"` |
| `start_date` | Trip start date | `2024-07-15` |
| `status` | Trip status | `draft`, `active`, `completed`, `archived` |

## Supported Directions

- `asc` - Ascending order (oldest/smallest first)
- `desc` - Descending order (newest/largest first)

## Usage Examples

### Get 10 Most Recent Trips
```http
GET /trips?size=10&sort_by=created_at:desc
```

### Get Trips by Title (Alphabetical)
```http
GET /trips?sort_by=title:asc
```

### Get Oldest Trips First
```http
GET /trips?sort_by=created_at:asc
```

### Get Trips by Start Date (Upcoming First)
```http
GET /trips?sort_by=start_date:desc
```

### Get Trips by Status
```http
GET /trips?sort_by=status:asc
```

## Default Behavior

- **Without `sort_by`**: Defaults to `created_at:desc` (newest first)
- **Invalid `sort_by`**: Falls back to `created_at:desc`
- **Invalid field**: Falls back to `created_at:desc`
- **Invalid direction**: Falls back to `desc`

## Response Format

The response format remains unchanged. The sorting only affects the order of items in the `data` array (modern format) or `trips` array (legacy format).

### Modern Response Example
```json
{
  "data": [
    {
      "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
      "title": "Latest Trip",
      "created_at": "2024-01-16T10:30:00Z",
      ...
    },
    {
      "id": "01K4AHPK4S1KVTYDB5ASTGTM8L",
      "title": "Earlier Trip", 
      "created_at": "2024-01-15T10:30:00Z",
      ...
    }
  ],
  "meta": { ... },
  "links": { ... }
}
```

## Pagination Links

The `sort_by` parameter is automatically included in pagination links when it differs from the default (`created_at:desc`).

## Error Handling

- Invalid sort fields are ignored (fallback to default)
- Invalid sort directions are ignored (fallback to `desc`)
- Malformed `sort_by` parameters are ignored (fallback to default)
- No errors are thrown for invalid sorting parameters

## Implementation Details

- Uses SQLAlchemy's `order_by()` with `desc()` and `asc()` functions
- Sorting is applied before pagination
- Total count is calculated before sorting for performance
- Sorting parameter is preserved in pagination links

## Testing

Use the provided test script to verify functionality:

```bash
python3 test_trips_sorting.py --api-base http://localhost:8000
```

## Backward Compatibility

- Existing API calls without `sort_by` will now return trips in newest-first order
- This may change the order compared to previous versions (which had no guaranteed order)
- All other functionality remains unchanged
