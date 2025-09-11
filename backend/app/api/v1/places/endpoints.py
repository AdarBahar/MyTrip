"""
Places API Endpoints

FastAPI endpoints for address and POI search with type-ahead suggestions.
"""

import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Header, Request, Depends
from fastapi.responses import JSONResponse
import logging

from .models import (
    SuggestResponse, SearchResponse, PlaceDetails, HealthResponse, ErrorResponse,
    SuggestRequest, SearchRequest, PlaceType, SortOrder
)
from .service import places_service
from ....core.auth import get_current_user
from ....core.rate_limiting import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/places", tags=["places-typeahead"])

# Rate limiter instances
suggest_limiter = RateLimiter(max_requests=50, window_seconds=60)  # 50 requests per minute
search_limiter = RateLimiter(max_requests=30, window_seconds=60)   # 30 requests per minute


def generate_request_id() -> str:
    """Generate unique request ID for tracking"""
    return f"req_{uuid.uuid4().hex[:12]}"


def create_error_response(code: str, message: str, status_code: int = 400, retry_after_ms: Optional[int] = None) -> JSONResponse:
    """Create standardized error response"""
    request_id = generate_request_id()
    error_response = ErrorResponse(
        error={
            "code": code,
            "message": message,
            "retry_after_ms": retry_after_ms,
            "request_id": request_id
        }
    )
    
    headers = {}
    if retry_after_ms:
        headers["Retry-After"] = str(retry_after_ms // 1000)
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
        headers=headers
    )


@router.get("/suggest",
    response_model=SuggestResponse,
    summary="Type-ahead Suggestions",
    description="Get fast, lightweight place suggestions while typing",
    response_description="List of place suggestions with highlighted matching text"
)
async def get_suggestions(
    request: Request,
    q: str = Query(..., min_length=1, max_length=256, description="Search query (minimum 1 character)", example="montef"),
    session_token: str = Query(..., description="Session token for grouping requests", example="st_abc123"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="User latitude for proximity bias", example=32.07),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="User longitude for proximity bias", example=34.78),
    radius: Optional[int] = Query(None, ge=1, le=50000, description="Bias radius in meters", example=5000),
    bbox: Optional[str] = Query(None, description="Bounding box: minLon,minLat,maxLon,maxLat", example="34.7,32.0,34.8,32.1"),
    countries: Optional[str] = Query(None, description="Comma-separated ISO-3166-1 alpha-2 codes", example="IL,US"),
    categories: Optional[str] = Query(None, description="Comma-separated category filters", example="hotel,restaurant,museum"),
    lang: Optional[str] = Query("en", description="BCP-47 language code", example="en"),
    limit: Optional[int] = Query(8, ge=1, le=20, description="Maximum results (1-20)", example=8),
    current_user = Depends(get_current_user)
):
    """
    **Type-ahead Suggestions for Places**

    Provides fast, lightweight predictions while typing for addresses and points of interest.

    **Key Features:**
    - ⚡ **Fast Response**: Optimized for real-time typing (target <120ms)
    - 🎯 **Proximity Bias**: Results prioritized by distance from lat/lng
    - 🏷️ **Category Filtering**: Filter by hotel, restaurant, museum, address, etc.
    - 🌍 **Geographic Filtering**: Limit results to specific countries or bounding box
    - ✨ **Text Highlighting**: Matching text highlighted with `<b>` tags for UI
    - 🔗 **Session Management**: Group related requests with session tokens

    **Usage Pattern:**
    1. Create a new session_token when user focuses on search input
    2. Send requests with same session_token for each keystroke
    3. Debounce requests by 150-250ms for optimal performance
    4. Use returned suggestions to populate dropdown/autocomplete UI

    **Example Request:**
    ```
    GET /places/v1/places/suggest?q=montef&lat=32.07&lng=34.78&radius=5000&countries=IL&categories=hotel&session_token=st_123
    ```

    **Response includes:**
    - Highlighted matching text for UI rendering
    - Geographic coordinates for mapping
    - Distance from query point (if lat/lng provided)
    - Confidence scores for ranking
    - Place types and categories for filtering
    """
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        # Rate limiting
        client_ip = request.client.host
        if not suggest_limiter.allow_request(f"suggest:{client_ip}"):
            return create_error_response(
                "RATE_LIMIT",
                "Too many suggestion requests",
                429,
                retry_after_ms=60000
            )
        
        # Validate coordinate pair
        if (lat is None) != (lng is None):
            return create_error_response(
                "BAD_REQUEST",
                "Both lat and lng must be provided together"
            )
        
        # Create request object
        suggest_request = SuggestRequest(
            q=q,
            session_token=session_token,
            lat=lat,
            lng=lng,
            radius=radius,
            bbox=bbox,
            countries=countries,
            categories=categories,
            lang=lang,
            limit=limit
        )
        
        # Get suggestions
        suggestions = await places_service.get_suggestions(suggest_request)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Suggestions request {request_id} completed in {duration_ms:.1f}ms")
        
        return SuggestResponse(
            session_token=session_token,
            suggestions=suggestions
        )
        
    except ValueError as e:
        logger.warning(f"Validation error in suggestions: {e}")
        return create_error_response("BAD_REQUEST", str(e))
    except Exception as e:
        logger.error(f"Error in suggestions endpoint: {e}")
        return create_error_response(
            "BACKEND_UNAVAILABLE",
            "Internal server error",
            500
        )


@router.get("/search",
    response_model=SearchResponse,
    summary="Full Place Search",
    description="Search for places with comprehensive details and metadata",
    response_description="Detailed search results with complete place information"
)
async def search_places(
    request: Request,
    q: str = Query(..., min_length=1, max_length=256, description="Search query", example="hotel montefiore"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="User latitude for proximity bias", example=32.07),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="User longitude for proximity bias", example=34.78),
    radius: Optional[int] = Query(None, ge=1, le=50000, description="Bias radius in meters", example=10000),
    bbox: Optional[str] = Query(None, description="Bounding box: minLon,minLat,maxLon,maxLat", example="34.7,32.0,34.8,32.1"),
    countries: Optional[str] = Query(None, description="Comma-separated ISO-3166-1 alpha-2 codes", example="IL,US"),
    categories: Optional[str] = Query(None, description="Comma-separated category filters", example="hotel,restaurant"),
    lang: Optional[str] = Query("en", description="BCP-47 language code", example="en"),
    limit: Optional[int] = Query(10, ge=1, le=50, description="Maximum results (1-50)", example=10),
    page_token: Optional[str] = Query(None, description="Pagination token for next page", example="page_20_1234567890"),
    offset: Optional[int] = Query(None, ge=0, description="Result offset for pagination", example=0),
    open_now: Optional[bool] = Query(None, description="Filter for currently open POIs", example=True),
    sort: Optional[SortOrder] = Query(SortOrder.RELEVANCE, description="Sort order", example="relevance"),
    current_user = Depends(get_current_user)
):
    """
    **Comprehensive Place Search**

    Search for places with full details, metadata, and comprehensive information suitable for
    mapping, display, and detailed place information.

    **Key Features:**
    - 📍 **Complete Details**: Full place information including contact details, hours, ratings
    - 🗺️ **Geographic Data**: Precise coordinates, bounding boxes, and timezone information
    - 🔍 **Advanced Filtering**: Filter by categories, countries, operating hours
    - 📊 **Multiple Sort Options**: Sort by relevance, distance, rating, or popularity
    - 📄 **Pagination Support**: Handle large result sets with cursor-based pagination
    - 🎯 **Proximity Search**: Distance-based ranking and filtering

    **Sort Options:**
    - **relevance**: Best text match and overall relevance (default)
    - **distance**: Closest to provided lat/lng coordinates
    - **rating**: Highest rated places first
    - **popularity**: Most popular places first

    **Use Cases:**
    - Final search results after user selects from type-ahead suggestions
    - Comprehensive place discovery and exploration
    - Detailed place information for trip planning
    - Geographic search within specific areas or countries

    **Example Request:**
    ```
    GET /places/v1/places/search?q=museum&lat=32.07&lng=34.78&countries=IL&sort=rating&limit=10
    ```

    **Response includes:**
    - Complete place details with contact information
    - Geographic coordinates and bounding boxes
    - Categories, ratings, and popularity scores
    - Timezone and metadata for each place
    - Pagination tokens for large result sets
    """
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        # Rate limiting
        client_ip = request.client.host
        if not search_limiter.allow_request(f"search:{client_ip}"):
            return create_error_response(
                "RATE_LIMIT",
                "Too many search requests",
                429,
                retry_after_ms=60000
            )
        
        # Validate coordinate pair
        if (lat is None) != (lng is None):
            return create_error_response(
                "BAD_REQUEST",
                "Both lat and lng must be provided together"
            )
        
        # Create request object
        search_request = SearchRequest(
            q=q,
            session_token=f"search_{request_id}",  # Generate session token for search
            lat=lat,
            lng=lng,
            radius=radius,
            bbox=bbox,
            countries=countries,
            categories=categories,
            lang=lang,
            limit=limit,
            page_token=page_token,
            offset=offset,
            open_now=open_now,
            sort=sort
        )
        
        # Perform search
        results, next_page_token = await places_service.search_places(search_request)
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Search request {request_id} completed in {duration_ms:.1f}ms")
        
        return SearchResponse(
            results=results,
            page_token=next_page_token,
            total_count=len(results)  # Simplified for demo
        )
        
    except ValueError as e:
        logger.warning(f"Validation error in search: {e}")
        return create_error_response("BAD_REQUEST", str(e))
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return create_error_response(
            "BACKEND_UNAVAILABLE",
            "Internal server error",
            500
        )


@router.get("/{place_id}",
    response_model=PlaceDetails,
    summary="Place Details",
    description="Get comprehensive details for a specific place",
    response_description="Complete place information including contact details, hours, and ratings"
)
async def get_place_details(
    place_id: str = Path(..., description="Unique place identifier", example="poi_hotel_montefiore"),
    current_user = Depends(get_current_user)
):
    """
    **Detailed Place Information**

    Retrieve comprehensive information for a specific place including all available
    metadata, contact details, operating hours, ratings, and external references.

    **Key Features:**
    - 📞 **Contact Information**: Phone numbers, websites, and social media
    - 🕒 **Operating Hours**: Detailed hours of operation by day
    - ⭐ **Ratings & Reviews**: Average ratings and popularity scores
    - 🏷️ **Categories & Types**: Detailed categorization and classification
    - 🌍 **Geographic Data**: Precise coordinates, bounding boxes, timezones
    - 🔗 **External References**: Links to other data sources and providers
    - 📝 **Aliases**: Alternative names and local language variants

    **Use Cases:**
    - Display detailed place information in trip planning
    - Show comprehensive place details in mapping applications
    - Provide contact information for booking or inquiries
    - Display operating hours and availability
    - Show ratings and reviews for decision making

    **Example Request:**
    ```
    GET /places/v1/places/poi_hotel_montefiore
    ```

    **Response includes:**
    - All basic place information (name, address, coordinates)
    - Contact details (phone, website, email if available)
    - Operating hours structured by day of week
    - Ratings, popularity scores, and review counts
    - Detailed categories and place types
    - Geographic metadata (timezone, country, region)
    - External source references for data provenance
    - Alternative names and localized variants
    """
    start_time = time.time()
    request_id = generate_request_id()
    
    try:
        # Get place details
        details = await places_service.get_place_details(place_id)
        
        if not details:
            return create_error_response(
                "NOT_FOUND",
                f"Place with ID '{place_id}' not found",
                404
            )
        
        # Log performance
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Details request {request_id} for {place_id} completed in {duration_ms:.1f}ms")
        
        return details
        
    except Exception as e:
        logger.error(f"Error in place details endpoint: {e}")
        return create_error_response(
            "BACKEND_UNAVAILABLE",
            "Internal server error",
            500
        )


@router.get("/",
    response_model=HealthResponse,
    summary="Places API Health Check",
    description="Check the health and status of the Places API service",
    response_description="Service health status and uptime information"
)
async def health_check():
    """
    **Places API Health Check**

    Monitor the health and availability of the Places API service.

    **Key Information:**
    - 🟢 **Service Status**: Current operational status
    - ⏱️ **Uptime**: Service uptime in seconds
    - 📊 **Version**: Current API version
    - 🔧 **Performance**: Basic performance indicators

    **Use Cases:**
    - Load balancer health checks
    - Service monitoring and alerting
    - API availability verification
    - Performance monitoring

    **Response includes:**
    - Service status (ok, degraded, down)
    - Uptime in seconds since last restart
    - API version information
    - Basic performance metrics
    """
    try:
        uptime = places_service.get_uptime()
        
        return HealthResponse(
            status="ok",
            uptime_s=uptime,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return create_error_response(
            "BACKEND_UNAVAILABLE",
            "Service health check failed",
            503
        )


# Note: Rate limiting headers are added in individual endpoint responses
