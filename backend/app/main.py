"""
RoadTrip Planner FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
# from app.api.pins import router as pins_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MyTrip - Road Trip Planner API",
    description="""
    A comprehensive road trip planning API with route optimization and user authentication.

    ## Features

    - ✅ **Trip Management**: Create, view, and manage road trips
    - ✅ **Days Organization**: Day-by-day trip planning with automatic date calculation
    - ✅ **Stops Management**: Comprehensive stops system with 12 categories and detailed planning
    - ✅ **Flexible Dates**: Optional start dates for trip planning
    - ✅ **Auto-Generated Slugs**: URL-friendly trip identifiers
    - ✅ **Trip Statuses**: Draft, Active, Completed, Archived
    - ✅ **User Authentication**: Secure Bearer token authentication
    - ✅ **Route Planning**: Integration with GraphHopper routing
    - ✅ **Collaborative Planning**: Multi-user trip management

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

    ## Trip Creation

    When creating trips:
    - **title** is required (1-255 characters)
    - **destination** is optional (max 255 characters)
    - **start_date** is optional (format: YYYY-MM-DD)
    - **slug** is auto-generated from the title
    - **status** defaults to "draft"

    ## Stops Management

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
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "roadtrip-planner-backend",
            "version": "1.0.0"
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
# app.include_router(pins_router, prefix="/pins", tags=["pins"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )