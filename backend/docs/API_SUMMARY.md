# MyTrip API Documentation Summary

## 📊 API Overview

- **Total Endpoints**: 70
- **API Version**: 1.0.0
- **OpenAPI Version**: 3.1.0

## 🚀 Recent Improvements

### Enhanced Trip Creation
- Input sanitization and validation
- Contextual next steps and suggestions
- Smart date range validation
- Auto-generated slugs

### Intelligent Routing System
- Hybrid GraphHopper integration (self-hosted + cloud)
- Exponential backoff for rate limiting
- Circuit breaker pattern for reliability
- Enhanced error messages with actionable steps

### Performance Optimizations
- Place search caching (5-minute TTL)
- Resource management improvements
- Smart bounds checking
- Matrix computation optimization

## 📋 Endpoint Categories

- **Auth**: 3 endpoints
- **Days**: 8 endpoints
- **Enums**: 5 endpoints
- **Monitoring**: 8 endpoints
- **Places**: 12 endpoints (includes geocoding endpoints)
- **Places-Typeahead**: 16 endpoints
- **Routing**: 9 endpoints
- **Settings**: 2 endpoints
- **Stops**: 12 endpoints
- **Trips**: 9 endpoints

## 🗺️ New Geocoding Features

### Forward Geocoding
- **GET /places/geocode** - Convert addresses to coordinates using MapTiler API
- Supports worldwide address search
- Returns precise GPS coordinates
- Multi-language support (Hebrew, English, etc.)

### Reverse Geocoding
- **GET /places/reverse-geocode** - Convert coordinates to addresses
- Accurate address lookup from lat/lng
- Useful for map click events and location services

## 🔗 Quick Links

- [Swagger UI](http://localhost:8000/docs) - Interactive API documentation
- [ReDoc](http://localhost:8000/redoc) - Alternative documentation view
- [OpenAPI JSON](./openapi.json) - Machine-readable specification
- [OpenAPI YAML](./openapi.yaml) - Human-readable specification

## 🛡️ Authentication

All endpoints (except `/auth/login` and `/health`) require Bearer token authentication:

```bash
Authorization: Bearer <your_token>
```

Get your token by calling the `/auth/login` endpoint with your email address.

## 🚨 Error Handling

The API provides enhanced error responses with actionable recovery steps:

- **429 Rate Limiting**: Exponential backoff with retry guidance
- **400 Out of Bounds**: Geographic coverage limitations with alternatives
- **500 Service Errors**: Specific recovery steps and fallback options

## 📈 Performance Features

- **Caching**: Aggressive place search caching for improved response times
- **Circuit Breaker**: Automatic protection against cascading failures
- **Resource Management**: Optimized HTTP client usage and memory management
- **Smart Fallbacks**: Graceful degradation when services are unavailable

---

*Generated automatically from OpenAPI specification*
