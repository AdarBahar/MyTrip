"""
RoadTrip Planner FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.security import HTTPBearer

from app.core.config import settings
from app.core.database import engine
from app.models import Base

# Import test detection utility to check for configuration leaks
try:
    from app.core.test_detection import warn_if_test_config_leaked
    warn_if_test_config_leaked()
except ImportError:
    pass  # Test detection utility not available

# Import routers
from app.api.auth.router import router as auth_router
from app.api.trips.router import router as trips_router
from app.api.routing.router import router as routing_router
from app.api.days.router import router as days_router
from app.api.stops.router import router as stops_router
from app.api.places.router import router as places_router
from app.api.settings.router import router as settings_router
from app.api.monitoring.router import router as monitoring_router
from app.api.enums.router import router as enums_router
# from app.api.pins import router as pins_router

# Import exception handlers
from app.core.exception_handlers import (
    validation_exception_handler,
    http_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    general_exception_handler,
    business_rule_violation_handler,
    resource_not_found_handler,
    permission_denied_handler,
    BusinessRuleViolation,
    ResourceNotFoundError,
    PermissionDeniedError
)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MyTrip - Road Trip Planner API",
    description="""
    A comprehensive road trip planning API with intelligent route optimization, enhanced error handling, and user authentication.

    ## 🚀 Features

    - ✅ **Trip Management**: Create, view, and manage road trips with enhanced validation
    - ✅ **Days Organization**: Day-by-day trip planning with automatic date calculation
    - ✅ **Stops Management**: Comprehensive stops system with 12 categories and detailed planning
    - ✅ **Intelligent Routing**: Hybrid GraphHopper routing with automatic fallback
    - ✅ **Enhanced Error Handling**: Actionable error messages with recovery guidance
    - ✅ **Place Search Caching**: Aggressive caching for improved performance
    - ✅ **Rate Limit Management**: Exponential backoff and circuit breaker patterns
    - ✅ **Modern Pagination**: Navigation links and comprehensive metadata
    - ✅ **Bulk Operations**: Efficient batch processing for multiple resources
    - ✅ **Smart Sequence Management**: Conflict-free ordering for collaborative editing
    - ✅ **Advanced Filtering**: Multi-attribute filtering and flexible sorting
    - ✅ **Input Validation**: Sanitization and security protection
    - ✅ **User Authentication**: Secure Bearer token authentication
    - ✅ **Collaborative Planning**: Multi-user trip management

    ## 🛡️ Recent Improvements

    ### Enhanced Trip Creation
    - **Input Sanitization**: Removes dangerous characters to prevent injection attacks
    - **Smart Validation**: Length limits, date range checks, meaningful content validation
    - **Enhanced Response**: Provides contextual next steps and planning suggestions
    - **Better Onboarding**: Guides users through the trip creation process

    ### Intelligent Routing System
    - **Hybrid Approach**: Self-hosted GraphHopper with cloud fallback
    - **Geographic Coverage**: Primary coverage for Israel/Palestine, global fallback
    - **Rate Limit Protection**: Exponential backoff prevents API quota exhaustion
    - **Circuit Breaker**: Skips unnecessary computations for out-of-bounds coordinates
    - **Enhanced Error Messages**: Specific guidance for different error scenarios

    ### Performance Optimizations
    - **Place Search Caching**: 5-minute TTL cache for faster repeated searches
    - **Resource Management**: Shared HTTP clients prevent memory leaks
    - **Smart Bounds Checking**: Reduces unnecessary external API calls
    - **Matrix Optimization**: Efficient distance matrix computation with fallbacks
    - **Modern Pagination**: Navigation links reduce client-side URL construction
    - **Bulk Operations**: Process up to 100 items in single API calls

    ## Authentication

    This API uses Bearer token authentication. To get started:

    1. **Login** using the `/auth/login` endpoint with your email address
    2. **Copy the access_token** from the response
    3. **Click the "Authorize" button** below and enter: `Bearer <your_token>`
    4. **Use protected endpoints** - they will automatically include your authentication

    ### Quick Start Example:

    ```bash
    # 1. Login to get your token
    curl -X POST "http://localhost:8100/auth/login" \\
         -H "Content-Type: application/json" \\
         -d '{"email": "adar.bahar@gmail.com"}'

    # 2. Create a new trip (start_date is optional)
    curl -X POST "http://localhost:8100/trips/" \\
         -H "Authorization: Bearer fake_token_YOUR_TOKEN_HERE" \\
         -H "Content-Type: application/json" \\
         -d '{"title": "My Road Trip", "destination": "California, USA"}'

    # 3. List your trips
    curl -X GET "http://localhost:8100/trips/" \\
         -H "Authorization: Bearer fake_token_YOUR_TOKEN_HERE"
    ```

    ## 🗺️ Routing & Navigation

    ### Intelligent Routing System
    The API provides sophisticated route computation with multiple fallback strategies:

    #### Primary Routing (Self-hosted GraphHopper)
    - **Coverage**: Israel and Palestine region
    - **Performance**: Fast, no rate limits
    - **Features**: Turn-by-turn directions, route optimization

    #### Fallback Routing (GraphHopper Cloud)
    - **Coverage**: Global
    - **Usage**: Automatic fallback for out-of-bounds coordinates
    - **Rate Limiting**: 3 calls per minute with exponential backoff

    #### Route Computation Features
    - **Route Optimization**: Traveling salesman optimization for multiple stops
    - **Multiple Profiles**: Car, motorcycle, bicycle support
    - **Avoid Options**: Tolls, highways, ferries
    - **Matrix Computation**: Distance/time matrices for optimization
    - **Error Recovery**: Graceful degradation with helpful error messages

    #### Error Handling
    - **Rate Limit (429)**: Exponential backoff with clear retry guidance
    - **Out of Bounds (400)**: Specific advice for geographic limitations
    - **Service Errors (500)**: Actionable steps for recovery
    - **Circuit Breaker**: Prevents cascading failures

    ## 🚗 Trip Creation

    ### Enhanced Trip Creation
    When creating trips, the API now provides enhanced validation and guidance:

    #### Required Fields
    - **title**: 1-255 characters (sanitized for security)
    - **destination**: Optional, max 255 characters
    - **start_date**: Optional, format YYYY-MM-DD (validated against future limits)

    #### Auto-Generated Fields
    - **slug**: URL-friendly identifier from title
    - **status**: Defaults to "draft"
    - **next_steps**: Contextual guidance for trip planning
    - **suggestions**: Time-based planning advice

    #### Enhanced Response
    ```json
    {
      "trip": { ... },
      "next_steps": [
        "Set your trip start date to help with planning",
        "Create your first day in Jerusalem"
      ],
      "suggestions": {
        "planning_timeline": "You have plenty of time to plan...",
        "popular_destinations": [...]
      }
    }
    ```

    ## 📄 Modern Pagination

    ### Enhanced Pagination System
    All list endpoints now support modern pagination with navigation links:

    #### Standard Pagination Parameters
    - **page**: Page number (1-based, default: 1)
    - **size**: Items per page (1-100, default: 20)
    - **format**: Response format - 'modern' (default) or 'legacy'

    #### Modern Response Format
    ```json
    {
      "data": [...],
      "meta": {
        "current_page": 1,
        "per_page": 20,
        "total_items": 45,
        "total_pages": 3,
        "has_next": true,
        "has_prev": false,
        "from_item": 1,
        "to_item": 20
      },
      "links": {
        "self": "http://localhost:8000/trips?page=1&size=20",
        "first": "http://localhost:8000/trips?page=1&size=20",
        "last": "http://localhost:8000/trips?page=3&size=20",
        "next": "http://localhost:8000/trips?page=2&size=20",
        "prev": null
      }
    }
    ```

    #### Navigation Benefits
    - **Self-contained URLs**: No client-side URL construction needed
    - **Filter Preservation**: Query parameters maintained across pages
    - **RESTful Navigation**: Standard first/last/next/prev links
    - **Metadata Rich**: Comprehensive pagination information

    #### Backward Compatibility
    Legacy format available via `format=legacy` parameter for existing clients.

    ## 🔄 Bulk Operations

    ### Efficient Batch Processing
    All major resources support bulk operations for improved efficiency:

    #### Supported Operations
    - **Bulk Delete**: Remove multiple resources in a single transaction
    - **Bulk Update**: Update multiple resources with field-level validation
    - **Bulk Reorder**: Reposition multiple items with sequence validation

    #### Bulk Delete Features
    ```json
    {
      "ids": ["id1", "id2", "id3"],
      "force": false
    }
    ```
    - **Transactional Safety**: All-or-nothing deletion
    - **Permission Validation**: Per-resource access control
    - **Cascade Handling**: Automatic cleanup of dependent resources
    - **Audit Logging**: Comprehensive operation tracking

    #### Bulk Update Features
    ```json
    {
      "updates": [
        {"id": "id1", "data": {"field": "value"}},
        {"id": "id2", "data": {"field": "value"}}
      ]
    }
    ```
    - **Field Filtering**: Only allowed fields can be updated
    - **Validation Hooks**: Pre/post-update processing
    - **Partial Success**: Individual item results
    - **Error Isolation**: Failed items don't affect successful ones

    #### Bulk Reorder Features
    ```json
    {
      "items": [
        {"id": "id1", "seq": 1},
        {"id": "id2", "seq": 2}
      ]
    }
    ```
    - **Sequence Validation**: No duplicate positions
    - **Scope Awareness**: Reordering within specific contexts
    - **Automatic Route Updates**: Triggers recomputation when needed

    #### Performance Benefits
    - **Reduced API Calls**: Process up to 100 items per request
    - **Database Efficiency**: Single transaction for multiple operations
    - **Network Optimization**: Fewer round trips
    - **UI Responsiveness**: Batch operations for drag-and-drop interfaces

    #### Available Endpoints
    - **Trips**: `DELETE /trips/bulk`, `PATCH /trips/bulk`
    - **Days**: `DELETE /days/bulk`, `PATCH /days/bulk`
    - **Stops**: `DELETE /stops/bulk`, `PATCH /stops/bulk`, `POST /stops/bulk/reorder`

    ## 🔢 Smart Sequence Management

    ### Conflict-Free Ordering System
    Eliminates manual sequence number conflicts in collaborative environments:

    #### Intelligent Operations
    ```json
    {
      "operation": "move_up",           // Move item up one position
      "operation": "move_down",         // Move item down one position
      "operation": "move_to_top",       // Move to first position
      "operation": "move_to_bottom",    // Move to last position
      "operation": "insert_after",      // Insert after target item
      "operation": "insert_before",     // Insert before target item
      "operation": "move_to_position"   // Move to specific position
    }
    ```

    #### Collaborative Benefits
    - **Conflict Resolution**: Automatic sequence number management
    - **Atomic Operations**: All changes in single database transaction
    - **Multi-User Safe**: Works correctly with concurrent edits
    - **Auto-Route Updates**: Triggers route recomputation when needed

    #### Available Endpoints
    - **Stops**: `POST /stops/{stop_id}/sequence` - Smart stop reordering
    - **Days**: `POST /days/{day_id}/sequence` - Smart day reordering (planned)

    ## 🔍 Advanced Filtering & Sorting

    ### Multi-Attribute Query System
    Flexible filtering and sorting across all list endpoints:

    #### Filter Operators
    - **Comparison**: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`
    - **Text**: `contains`, `starts_with`, `ends_with`
    - **Lists**: `in`, `not_in`
    - **Null checks**: `is_null`, `is_not_null`
    - **Ranges**: `between`
    - **Pattern**: `regex`

    #### Filter Syntax
    ```
    field:operator:value,field2:operator2:value2

    Examples:
    - status:eq:active,created_at:gte:2024-01-01
    - stop_type:in:food|attraction,duration_min:gte:30
    - title:contains:jerusalem,date:between:2024-01-01|2024-12-31
    ```

    #### Sort Syntax
    ```
    field:direction,field2:direction2

    Examples:
    - created_at:desc,title:asc
    - seq:asc,duration_min:desc
    ```

    #### Enhanced List Endpoints
    - **Trips**: Filter by status, destination, date range, publication status
    - **Days**: Filter by date range, status, title search
    - **Stops**: Filter by type, duration range, notes search
    - **Places**: Filter by type, location, name search

    #### Search Functionality
    - **Global search**: Search across multiple fields simultaneously
    - **Range filters**: Date ranges, duration ranges, numeric ranges
    - **Multi-value filters**: Select multiple statuses, types, etc.

    ## 🔍 Place Search & Geocoding

    ### Enhanced Place Search
    The API provides intelligent place search with aggressive caching:

    #### Search Features
    - **External Integration**: MapTiler geocoding API
    - **Aggressive Caching**: 5-minute TTL for improved performance
    - **Smart Ranking**: Relevance-based result ordering
    - **Proximity Search**: Location-based result prioritization
    - **Auto-complete**: Real-time search suggestions

    #### Search Parameters
    - **query**: Search term (min 2 characters)
    - **lat/lon**: Optional proximity coordinates
    - **radius**: Search radius in meters (default: 50km)
    - **limit**: Max results (1-50, default: 10)

    #### Performance Benefits
    - **Cache Hits**: Instant results for repeated searches
    - **Reduced API Costs**: Fewer external geocoding calls
    - **Better UX**: Immediate response for common searches

    ## 🛑 Stops Management

    The stops system allows detailed itinerary planning with:

    ### Stop Types (12 categories):
    - 🏨 **Accommodation**: Hotels, B&Bs, camping
    - 🍽️ **Food**: Restaurants, cafes, bars
    - 🎯 **Attraction**: Museums, landmarks, tours
    - ⛽ **Gas**: Fuel stations, charging points
    - 🛍️ **Shopping**: Stores, markets, outlets
    - 🚗 **Transport**: Airports, train stations
    - 🏥 **Services**: Banks, hospitals, repairs
    - 🌲 **Nature**: Parks, trails, beaches
    - 🎭 **Culture**: Theaters, galleries, events
    - 🌙 **Nightlife**: Bars, clubs, entertainment
    - 📍 **Other**: Custom locations

    ### Stop Features:
    - **Time Management**: Arrival/departure times, duration estimates
    - **Priority Levels**: Must see (1) to Optional (5)
    - **Booking Info**: Confirmation numbers, status tracking
    - **Cost Tracking**: Estimated and actual expenses
    - **Contact Details**: Phone, website, notes
    - **Flexible Ordering**: Drag-and-drop reordering within days

    ### Stop Operations:
    - Create, read, update, delete stops
    - Reorder stops within days
    - Filter by type and priority
    - Include place information
    - Trip-wide stops summary

    ## 🚨 Error Handling & Recovery

    ### Enhanced Error Responses
    The API provides detailed error information with actionable recovery steps:

    #### Rate Limiting (429)
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

    #### Geographic Coverage (400)
    ```json
    {
      "detail": "Coordinates are outside supported region",
      "error_type": "OUT_OF_BOUNDS",
      "supported_regions": ["Israel", "Palestine"],
      "suggestions": [
        "Try using nearby major cities",
        "Check if all locations are in the same region",
        "Consider splitting international trips"
      ]
    }
    ```

    #### Service Errors (500)
    ```json
    {
      "detail": "Routing service temporarily unavailable",
      "error_type": "SERVICE_ERROR",
      "suggestions": [
        "Try again in a few moments",
        "Check that all locations are valid",
        "Contact support if problem persists"
      ]
    }
    ```

    ### Circuit Breaker Pattern
    - **Automatic Protection**: Prevents cascading failures
    - **Smart Backoff**: Exponential delays for failed services
    - **Resource Conservation**: Skips unnecessary API calls
    - **Graceful Degradation**: Maintains functionality during outages

    **Development Note**: This is a development authentication system. Any valid email address can be used to login and will automatically create a user account.
    """,
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Custom OpenAPI schema to add security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Bearer token in the format: Bearer <token>"
        }
    }

    # Add security to protected endpoints
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                # Skip auth endpoints from requiring auth
                if not path.startswith("/auth/login") and not path.startswith("/health") and not path == "/":
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Configure CORS
# In dev, loosen CORS to any origin; in other envs, use configured origins
if settings.APP_ENV.lower() == "dev":
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint with system status information.

    Returns:
    - **status**: Service health status
    - **service**: Service name and version
    - **routing_mode**: Current routing configuration (selfhost/cloud)
    - **use_cloud_matrix**: Whether cloud matrix computation is enabled

    This endpoint is useful for:
    - Monitoring service availability
    - Checking routing configuration
    - Debugging connectivity issues
    - Load balancer health checks
    """
    from app.core.config import settings as cfg
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "roadtrip-planner-backend",
            "version": "1.0.0",
            "routing_mode": cfg.GRAPHHOPPER_MODE,
            "use_cloud_matrix": cfg.USE_CLOUD_MATRIX,
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RoadTrip Planner API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(trips_router, prefix="/trips", tags=["trips"])
app.include_router(routing_router, prefix="/routing", tags=["routing"])
app.include_router(days_router, prefix="/trips/{trip_id}/days", tags=["days"])
app.include_router(stops_router, prefix="/stops", tags=["stops"])
app.include_router(places_router, prefix="/places", tags=["places"])
app.include_router(settings_router, tags=["settings"])
app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
app.include_router(enums_router, prefix="/enums", tags=["enums"])
# app.include_router(pins_router, prefix="/pins", tags=["pins"])

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(BusinessRuleViolation, business_rule_violation_handler)
app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
app.add_exception_handler(PermissionDeniedError, permission_denied_handler)
app.add_exception_handler(Exception, general_exception_handler)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )