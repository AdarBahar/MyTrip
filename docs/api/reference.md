# MyTrip API Reference

This document provides a comprehensive reference for the MyTrip Road Trip Planner API.

## Base URL

```
http://localhost:8100  (Development)
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8100/docs
- **ReDoc**: http://localhost:8100/redoc
- **OpenAPI JSON**: http://localhost:8100/openapi.json

## Authentication

All API endpoints (except `/auth/login` and `/health`) require authentication using Bearer tokens.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "access_token": "fake_token_...",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "user@example.com",
    "display_name": "User Name"
  }
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer fake_token_...
```

## Trips

### List Trips

```http
GET /trips/
Authorization: Bearer <token>
```

### Create Trip

```http
POST /trips/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Road Trip",
  "destination": "California, USA",
  "start_date": "2025-09-15"
}
```

**Field Details:**
- `title` (required): Trip title (1-255 characters)
- `destination` (optional): Trip destination (max 255 characters)
- `start_date` (optional): Trip start date (format: YYYY-MM-DD)
- `timezone` (optional): Trip timezone (defaults to UTC)
- `status` (optional): Trip status (defaults to "draft")
- `is_published` (optional): Whether trip is published (defaults to false)

**Note:** The `slug` is auto-generated from the title and must be unique among your trips.

**Trip Statuses:**
- `draft`: Trip is being planned
- `active`: Trip is currently happening or confirmed
- `completed`: Trip has been completed
- `archived`: Trip has been archived

### Get Trip

```http
GET /trips/{slug}
Authorization: Bearer <token>
```

### Update Trip

```http
PUT /trips/{slug}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Trip Title",
  "destination": "Updated Destination",
  "start_date": "2025-10-01"
}
```

### Delete Trip

```http
DELETE /trips/{slug}
Authorization: Bearer <token>
```

## Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "roadtrip-planner-backend",
  "version": "1.0.0"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

**Error Response Format:**
```json
{
  "detail": "Error message"
}
```