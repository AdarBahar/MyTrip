# 📚 MyTrip API Documentation

Welcome to the comprehensive documentation for the MyTrip Road Trip Planner API! This directory contains up-to-date API specifications and documentation reflecting all recent improvements and enhancements.

## 📋 Documentation Files

### 🔧 **API Specifications**
- **[openapi.json](./openapi.json)** - Machine-readable OpenAPI 3.1 specification
- **[openapi.yaml](./openapi.yaml)** - Human-readable YAML format specification
- **[API_SUMMARY.md](./API_SUMMARY.md)** - Quick overview with endpoint counts and features

### 📖 **Interactive Documentation**
- **[Swagger UI](http://localhost:8000/docs)** - Interactive API explorer with live testing
- **[ReDoc](http://localhost:8000/redoc)** - Clean, responsive API documentation

## 🚀 **Recent API Improvements**

### ✅ **Enhanced Trip Creation**
- **Input Sanitization**: Removes dangerous characters to prevent injection attacks
- **Smart Validation**: Length limits, date range checks, meaningful content validation
- **Enhanced Response**: Provides contextual next steps and planning suggestions
- **Better Onboarding**: Guides users through the trip creation process

### ✅ **Intelligent Routing System**
- **Hybrid GraphHopper**: Self-hosted + cloud fallback for global coverage
- **Rate Limit Management**: Exponential backoff prevents API quota exhaustion
- **Circuit Breaker**: Automatic protection against cascading failures
- **Enhanced Error Messages**: Actionable steps for different error scenarios

### ✅ **Performance Optimizations**
- **Place Search Caching**: 5-minute TTL cache for faster repeated searches
- **Resource Management**: Shared HTTP clients prevent memory leaks
- **Smart Bounds Checking**: Reduces unnecessary external API calls
- **Matrix Optimization**: Efficient distance matrix computation

### ✅ **Enhanced Error Handling**
- **Structured Errors**: Consistent error format with actionable steps
- **Context-Aware Messages**: Different guidance for different error types
- **Recovery Guidance**: Specific steps users can take to resolve issues

## 🎯 **API Categories**

### 🔐 **Authentication** (3 endpoints)
- User login and token management
- Development-friendly authentication system
- Bearer token security

### 🗺️ **Trips** (6 endpoints)
- Enhanced trip creation with validation
- Trip management and organization
- Collaborative planning features

### 📅 **Days** (6 endpoints)
- Day-by-day trip planning
- Automatic date calculation
- Flexible scheduling

### 🛑 **Stops** (8 endpoints)
- Comprehensive stops management
- 12 stop categories (accommodation, food, attractions, etc.)
- Priority levels and time management

### 📍 **Places** (8 endpoints)
- Intelligent place search with caching
- MapTiler geocoding integration
- Proximity-based results

### 🗺️ **Routing** (8 endpoints)
- Hybrid routing system
- Route optimization
- Matrix computation for multi-stop routes

### ⚙️ **Settings** (2 endpoints)
- User preferences
- Configuration management

## 🔄 **Keeping Documentation Updated**

The API documentation is automatically generated from the codebase to ensure accuracy. To update:

### **Automatic Generation**
```bash
# Run the export script inside the backend container
docker exec roadtrip-backend python scripts/export_openapi.py

# Copy updated files to local docs directory
docker cp roadtrip-backend:/app/docs/openapi.json backend/docs/
docker cp roadtrip-backend:/app/docs/openapi.yaml backend/docs/
docker cp roadtrip-backend:/app/docs/API_SUMMARY.md backend/docs/
```

### **Manual Updates**
1. **Update API descriptions** in route decorators and docstrings
2. **Enhance schema documentation** in Pydantic models
3. **Add examples** in the export script
4. **Update main.py** description for major feature additions

## 🧪 **Testing the API**

### **Using Swagger UI**
1. Visit [http://localhost:8000/docs](http://localhost:8000/docs)
2. Click "Authorize" and enter your Bearer token
3. Explore and test endpoints interactively

### **Using curl**
```bash
# 1. Get authentication token
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email": "your.email@example.com"}'

# 2. Use the token for API calls
curl -X GET "http://localhost:8000/trips/" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Using the Frontend**
The frontend application automatically handles authentication and provides a user-friendly interface for all API functionality.

## 🚨 **Error Handling Examples**

### **Rate Limiting (429)**
```json
{
  "detail": "Routing temporarily unavailable due to rate limits",
  "error_type": "RATE_LIMIT",
  "retry_after": 60,
  "suggestions": [
    "Wait 1-2 minutes before trying again",
    "Consider using fewer stops",
    "Try again during off-peak hours"
  ]
}
```

### **Geographic Coverage (400)**
```json
{
  "detail": "Coordinates are outside supported region",
  "error_type": "OUT_OF_BOUNDS",
  "supported_regions": ["Israel", "Palestine"],
  "suggestions": [
    "Try using nearby major cities",
    "Check if all locations are in the same region"
  ]
}
```

## 📊 **API Statistics**

- **Total Endpoints**: 43
- **Authentication Required**: 40 endpoints
- **Public Endpoints**: 3 (login, health, root)
- **OpenAPI Version**: 3.1.0
- **API Version**: 1.0.0

## 🔗 **Related Documentation**

- **[Testing Configuration](./TESTING_CONFIGURATION.md)** - Test setup and configuration
- **[Improvements Implemented](../../docs/IMPROVEMENTS_IMPLEMENTED.md)** - Recent feature additions
- **[Frontend Documentation](../../frontend/README.md)** - Client-side documentation

---

*Documentation automatically generated and maintained to reflect the current state of the API*
