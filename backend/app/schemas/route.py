"""
Route schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RoutePoint(BaseModel):
    """Route point schema"""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    name: Optional[str] = None


class RouteOptions(BaseModel):
    """Route computation options"""
    avoid_highways: bool = False
    avoid_tolls: bool = False
    additional_options: Optional[Dict[str, Any]] = None


class RouteComputeRequest(BaseModel):
    """Route computation request"""
    profile: str = Field(..., pattern="^(car|motorcycle|bike)$")
    options: Optional[RouteOptions] = None


class RoutePreview(BaseModel):
    """Route preview response"""
    total_km: float
    total_min: float
    geometry: Dict[str, Any]  # GeoJSON LineString
    legs: List[Dict[str, Any]]
    debug: Dict[str, Any]
    preview_token: str  # Token to commit this route


class RouteCommitRequest(BaseModel):
    """Route commit request"""
    preview_token: str
    name: Optional[str] = None


class RouteLegSchema(BaseModel):
    """Route leg schema"""
    id: str
    route_version_id: str
    seq: int
    distance_km: Optional[float]
    duration_min: Optional[float]
    geojson: Optional[Dict[str, Any]]
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RouteVersionSchema(BaseModel):
    """Route version schema"""
    id: str
    day_id: str
    version: int
    is_active: bool
    is_primary: bool
    name: Optional[str]
    profile_used: Optional[str]
    total_km: Optional[float]
    total_min: Optional[float]
    geojson: Optional[Dict[str, Any]]
    totals: Optional[Dict[str, Any]]
    stop_snapshot: Optional[Dict[str, Any]]
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Optional relationships
    legs: Optional[List[RouteLegSchema]] = None

    class Config:
        from_attributes = True


class RouteVersionList(BaseModel):
    """Route version list schema"""
    routes: List[RouteVersionSchema]