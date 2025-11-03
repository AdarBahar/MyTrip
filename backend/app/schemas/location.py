"""
Location Pydantic schemas

Request and response models for location endpoints.
These schemas provide automatic validation, serialization, and API documentation.
"""

from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseResponseWithSoftDelete


# Health Check Schemas
class LocationDatabaseInfo(BaseModel):
    """Database connection information for health check"""

    connected: bool = Field(
        ..., description="Whether database connection is successful"
    )
    database_name: Optional[str] = Field(None, description="Connected database name")
    database_user: Optional[str] = Field(None, description="Connected database user")
    test_query: Optional[int] = Field(None, description="Test query result")
    expected_database: str = Field(..., description="Expected database name")
    expected_user: str = Field(..., description="Expected database user")
    error: Optional[str] = Field(None, description="Error message if connection failed")


class LocationHealthResponse(BaseModel):
    """Health check response schema"""

    status: str = Field(..., description="Health status: 'ok' or 'error'")
    module: str = Field(..., description="Module name")
    database: LocationDatabaseInfo = Field(
        ..., description="Database connection information"
    )
    timestamp: str = Field(..., description="Health check timestamp in UTC")


class LocationBase(BaseModel):
    """Base location schema with common fields"""

    name: str = Field(..., min_length=1, max_length=255, description="Location name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Location description"
    )
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    country: Optional[str] = Field(None, max_length=100, description="Country name")
    latitude: Optional[Decimal] = Field(
        None, ge=-90, le=90, description="Latitude coordinate"
    )
    longitude: Optional[Decimal] = Field(
        None, ge=-180, le=180, description="Longitude coordinate"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Location category"
    )
    tags: Optional[list[str]] = Field(default_factory=list, description="Location tags")
    extra_data: Optional[dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )
    is_active: bool = Field(True, description="Whether the location is active")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags list"""
        if v is None:
            return []
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        for tag in v:
            if not isinstance(tag, str) or len(tag.strip()) == 0:
                raise ValueError("Tags must be non-empty strings")
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return [tag.strip() for tag in v]

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_coordinates(cls, v):
        """Validate coordinate precision"""
        if v is not None and v.as_tuple().exponent < -8:
            raise ValueError("Coordinate precision cannot exceed 8 decimal places")
        return v


class LocationCreate(LocationBase):
    """Schema for creating a new location"""

    # All fields inherited from LocationBase
    # Add any creation-specific validation here
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location (all fields optional)"""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Location name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Location description"
    )
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    city: Optional[str] = Field(None, max_length=100, description="City name")
    country: Optional[str] = Field(None, max_length=100, description="Country name")
    latitude: Optional[Decimal] = Field(
        None, ge=-90, le=90, description="Latitude coordinate"
    )
    longitude: Optional[Decimal] = Field(
        None, ge=-180, le=180, description="Longitude coordinate"
    )
    category: Optional[str] = Field(
        None, max_length=100, description="Location category"
    )
    tags: Optional[list[str]] = Field(None, description="Location tags")
    extra_data: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the location is active"
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags list"""
        if v is None:
            return None
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        for tag in v:
            if not isinstance(tag, str) or len(tag.strip()) == 0:
                raise ValueError("Tags must be non-empty strings")
            if len(tag) > 50:
                raise ValueError("Each tag must be 50 characters or less")
        return [tag.strip() for tag in v]


class LocationResponse(BaseResponseWithSoftDelete):
    """Schema for location responses"""

    name: str = Field(..., description="Location name")
    description: Optional[str] = Field(None, description="Location description")
    address: Optional[str] = Field(None, description="Full address")
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    latitude: Optional[Decimal] = Field(None, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, description="Longitude coordinate")
    category: Optional[str] = Field(None, description="Location category")
    tags: list[str] = Field(default_factory=list, description="Location tags")
    extra_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    is_active: bool = Field(..., description="Whether the location is active")
    created_by: str = Field(..., description="ID of user who created the location")

    # Inherits from BaseResponseWithSoftDelete:
    # - id: str (ULID)
    # - created_at: ISO8601DateTime (UTC)
    # - updated_at: ISO8601DateTime (UTC)
    # - deleted_at: Optional[ISO8601DateTime] (UTC)


class LocationList(BaseModel):
    """Schema for paginated location list responses"""

    locations: list[LocationResponse] = Field(..., description="List of locations")
    total: int = Field(..., ge=0, description="Total number of locations")
    skip: int = Field(0, ge=0, description="Number of records skipped")
    limit: int = Field(100, ge=1, description="Maximum number of records returned")


class LocationSearchParams(BaseModel):
    """Schema for location search parameters"""

    query: Optional[str] = Field(None, max_length=255, description="Search query")
    category: Optional[str] = Field(
        None, max_length=100, description="Filter by category"
    )
    city: Optional[str] = Field(None, max_length=100, description="Filter by city")
    country: Optional[str] = Field(
        None, max_length=100, description="Filter by country"
    )
    tags: Optional[list[str]] = Field(None, description="Filter by tags")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    near_lat: Optional[Decimal] = Field(
        None, ge=-90, le=90, description="Latitude for proximity search"
    )
    near_lng: Optional[Decimal] = Field(
        None, ge=-180, le=180, description="Longitude for proximity search"
    )
    radius_km: Optional[float] = Field(
        None, gt=0, le=1000, description="Search radius in kilometers"
    )


class LocationBulkCreate(BaseModel):
    """Schema for bulk location creation"""

    locations: list[LocationCreate] = Field(
        ..., min_items=1, max_items=100, description="List of locations to create"
    )


class LocationBulkResponse(BaseModel):
    """Schema for bulk operation responses"""

    created: list[LocationResponse] = Field(
        ..., description="Successfully created locations"
    )
    errors: list[dict[str, Any]] = Field(
        default_factory=list, description="Errors encountered during creation"
    )
    total_requested: int = Field(
        ..., ge=0, description="Total number of locations requested"
    )
    total_created: int = Field(
        ..., ge=0, description="Total number of locations successfully created"
    )


# Add more schemas based on your PHP implementation
# Examples:
# class LocationFavorite(BaseModel):
# class LocationStats(BaseModel):
# class LocationExport(BaseModel):
# etc.
