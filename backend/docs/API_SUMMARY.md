# MyTrip API Documentation Summary

## 📊 API Overview

- **Total Endpoints**: 83
- **API Version**: 1.0.0
- **OpenAPI Version**: 3.1.0

## 🆕 Latest Updates

### New App Login Endpoint
✅ **POST /auth/app-login** - Simple authentication without token management
- Returns boolean authentication result
- No JWT token generation required
- Perfect for mobile apps and legacy systems
- Validates against hashed passwords in database

### Enhanced Day Management
- Soft delete functionality with cascade to stops
- Day status enum: ACTIVE, INACTIVE, DELETED
- Bulk operations with proper filtering

### Improved Error Handling
- Generic error messages to prevent user enumeration
- Graceful degradation for authentication failures
- Enhanced validation and security

## 📋 Endpoint Categories

- **Ai**: 2 endpoints
- **Auth**: 4 endpoints
- **Days**: 9 endpoints
- **Enums**: 5 endpoints
- **Jwt-Auth**: 5 endpoints
- **Monitoring**: 8 endpoints
- **Places**: 12 endpoints
- **Places-Typeahead**: 16 endpoints
- **Route-Optimization**: 2 endpoints
- **Routing**: 12 endpoints
- **Settings**: 2 endpoints
- **Stops**: 12 endpoints
- **Trips**: 10 endpoints


## 🔗 Quick Links

- [Swagger UI](https://mytrips-api.bahar.co.il/docs) - Interactive API documentation
- [ReDoc](https://mytrips-api.bahar.co.il/redoc) - Alternative documentation view
- [OpenAPI JSON](./openapi.json) - Machine-readable specification
- [OpenAPI YAML](./openapi.yaml) - Human-readable specification

## 🛡️ Authentication Options

### JWT Token Authentication (Existing)
```bash
Authorization: Bearer <your_token>
```
Get your token by calling the `/auth/login` endpoint.

### Simple App Authentication (New)
```bash
POST /auth/app-login
{
  "email": "user@example.com",
  "password": "user_password"
}
```
Returns simple boolean authentication result without token management.

## 🚨 Error Handling

The API provides enhanced error responses with actionable recovery steps:

- **Authentication Errors**: Generic messages to prevent user enumeration
- **Validation Errors**: Detailed field-level validation feedback
- **Rate Limiting**: Exponential backoff with retry guidance
- **Service Errors**: Specific recovery steps and fallback options

## 📈 Performance Features

- **Caching**: Aggressive place search caching for improved response times
- **Soft Delete**: Data preservation with proper filtering
- **Circuit Breaker**: Automatic protection against cascading failures
- **Resource Management**: Optimized HTTP client usage and memory management

---

*Generated automatically from OpenAPI specification*
