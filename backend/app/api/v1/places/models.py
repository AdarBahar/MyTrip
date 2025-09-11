"""
Places API Models

Data models for address and POI search with type-ahead suggestions.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class GeometryType(str, Enum):
    """Precision level of coordinates"""
    ROOFTOP = "rooftop"
    ROUTE = "route"
    CENTROID = "centroid"
    INTERPOLATED = "interpolated"


class PlaceType(str, Enum):
    """Place type categories"""
    ADDRESS = "address"
    POI = "poi"
    LODGING = "lodging"
    RESTAURANT = "restaurant"
    MUSEUM = "museum"
    ATTRACTION = "attraction"
    BUSINESS = "business"


class SortOrder(str, Enum):
    """Search result sorting options"""
    RELEVANCE = "relevance"
    DISTANCE = "distance"
    RATING = "rating"
    POPULARITY = "popularity"


class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in WGS-84 decimal degrees")
    lng: float = Field(..., ge=-180, le=180, description="Longitude in WGS-84 decimal degrees")


class BoundingBox(BaseModel):
    """Geographic bounding box"""
    minLat: float = Field(..., ge=-90, le=90)
    minLng: float = Field(..., ge=-180, le=180)
    maxLat: float = Field(..., ge=-90, le=90)
    maxLng: float = Field(..., ge=-180, le=180)

    @validator('maxLat')
    def validate_lat_order(cls, v, values):
        if 'minLat' in values and v <= values['minLat']:
            raise ValueError('maxLat must be greater than minLat')
        return v

    @validator('maxLng')
    def validate_lng_order(cls, v, values):
        if 'minLng' in values and v <= values['minLng']:
            raise ValueError('maxLng must be greater than minLng')
        return v


class PlaceMetadata(BaseModel):
    """Additional place metadata"""
    country: Optional[str] = Field(None, description="ISO-3166-1 alpha-2 country code")
    postcode: Optional[str] = None
    region: Optional[str] = None
    locality: Optional[str] = None
    street_number: Optional[str] = None
    route: Optional[str] = None


class PlaceSuggestion(BaseModel):
    """Type-ahead suggestion result"""
    id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Place name")
    highlighted: str = Field(..., description="Name with highlighted matching text")
    formatted_address: str = Field(..., description="Human-readable address")
    types: List[PlaceType] = Field(default_factory=list, description="Place type categories")
    center: Coordinates = Field(..., description="Geographic center point")
    distance_m: Optional[int] = Field(None, description="Distance from query point in meters")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    source: str = Field(default="internal", description="Data source identifier")


class PlaceSearchResult(BaseModel):
    """Full search result with complete details"""
    id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Place name")
    formatted_address: str = Field(..., description="Human-readable address")
    types: List[PlaceType] = Field(default_factory=list, description="Place type categories")
    center: Coordinates = Field(..., description="Geographic center point")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box if available")
    categories: List[str] = Field(default_factory=list, description="Detailed categories")
    score: float = Field(..., ge=0, le=1, description="Relevance score 0-1")
    timezone: Optional[str] = Field(None, description="IANA timezone identifier")
    metadata: Optional[PlaceMetadata] = Field(None, description="Additional metadata")
    geometry_type: Optional[GeometryType] = Field(None, description="Coordinate precision")


class PlaceDetails(PlaceSearchResult):
    """Detailed place information"""
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Website URL")
    hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating 0-5")
    popularity: Optional[float] = Field(None, ge=0, le=1, description="Popularity score 0-1")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    source_refs: Dict[str, str] = Field(default_factory=dict, description="External source references")
    name_local: Optional[str] = Field(None, description="Name in local language")
    name_ascii: Optional[str] = Field(None, description="ASCII-only name")


# Request Models

class SuggestRequest(BaseModel):
    """Type-ahead suggestions request"""
    q: str = Field(..., min_length=1, max_length=256, description="Search query")
    session_token: str = Field(..., description="Session token for grouping requests")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="User latitude for proximity bias")
    lng: Optional[float] = Field(None, ge=-180, le=180, description="User longitude for proximity bias")
    radius: Optional[int] = Field(None, ge=1, le=50000, description="Bias radius in meters")
    bbox: Optional[str] = Field(None, description="Bounding box: minLon,minLat,maxLon,maxLat")
    countries: Optional[str] = Field(None, description="Comma-separated ISO-3166-1 alpha-2 codes")
    categories: Optional[str] = Field(None, description="Comma-separated category filters")
    lang: Optional[str] = Field("en", description="BCP-47 language code")
    limit: Optional[int] = Field(8, ge=1, le=20, description="Maximum results")

    @validator('bbox')
    def validate_bbox(cls, v):
        if v is None:
            return v
        try:
            coords = [float(x.strip()) for x in v.split(',')]
            if len(coords) != 4:
                raise ValueError('bbox must have exactly 4 coordinates')
            minLng, minLat, maxLng, maxLat = coords
            if not (-180 <= minLng <= 180 and -180 <= maxLng <= 180):
                raise ValueError('longitude must be between -180 and 180')
            if not (-90 <= minLat <= 90 and -90 <= maxLat <= 90):
                raise ValueError('latitude must be between -90 and 90')
            if minLng >= maxLng or minLat >= maxLat:
                raise ValueError('bbox coordinates must be in correct order')
            return v
        except (ValueError, TypeError) as e:
            raise ValueError(f'Invalid bbox format: {e}')


class SearchRequest(SuggestRequest):
    """Full search request"""
    page_token: Optional[str] = Field(None, description="Pagination token")
    offset: Optional[int] = Field(None, ge=0, description="Result offset")
    open_now: Optional[bool] = Field(None, description="Filter for currently open POIs")
    sort: Optional[SortOrder] = Field(SortOrder.RELEVANCE, description="Sort order")


# Response Models

class SuggestResponse(BaseModel):
    """Type-ahead suggestions response"""
    session_token: str = Field(..., description="Session token for this response")
    suggestions: List[PlaceSuggestion] = Field(..., description="Suggestion results")


class SearchResponse(BaseModel):
    """Search results response"""
    results: List[PlaceSearchResult] = Field(..., description="Search results")
    page_token: Optional[str] = Field(None, description="Token for next page")
    total_count: Optional[int] = Field(None, description="Total available results")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    uptime_s: int = Field(..., description="Uptime in seconds")
    version: Optional[str] = Field(None, description="Service version")


class ErrorDetail(BaseModel):
    """Error detail information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    retry_after_ms: Optional[int] = Field(None, description="Retry delay in milliseconds")
    request_id: Optional[str] = Field(None, description="Request identifier for debugging")


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail = Field(..., description="Error details")
