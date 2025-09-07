"""
Place schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PlaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    meta: Optional[Dict[str, Any]] = None


class PlaceCreate(PlaceBase):
    """Schema for creating a place"""
    pass


class PlaceUpdate(BaseModel):
    """Schema for updating a place"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    meta: Optional[Dict[str, Any]] = None


class PlaceSchema(BaseModel):
    """Place response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    address: Optional[str] = None
    lat: float
    lon: float
    meta: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PlaceSearchItem(BaseModel):
    """Lightweight place item for search results (not persisted)"""
    id: str
    name: str
    address: Optional[str] = None
    lat: float
    lon: float
    meta: Optional[Dict[str, Any]] = None
    is_saved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlaceSearchResult(BaseModel):
    """Legacy place search result schema"""
    places: List[PlaceSearchItem]
    total: int

# Import enhanced pagination
from app.schemas.pagination import PaginatedResponse

# Modern paginated place search response
PlaceSearchPaginatedResponse = PaginatedResponse[PlaceSearchItem]


class GeocodingResult(BaseModel):
    address: str
    lat: float
    lon: float
    formatted_address: str
    place_id: Optional[str] = None
    types: Optional[List[str]] = None


class PlaceSearchParams(BaseModel):
    query: str
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    radius: Optional[int] = Field(None, ge=1)
    limit: Optional[int] = Field(10, ge=1, le=50)

