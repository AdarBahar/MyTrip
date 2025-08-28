"""
Route schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


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
    optimize: bool = Field(
        False, description="Optimize VIA stop order (respects fixed stops)"
    )
    fixed_stop_ids: Optional[List[str]] = Field(
        None,
        description="Explicit list of fixed stop IDs (optional; otherwise use DB flags)",
    )
    options: Optional[RouteOptions] = None


class RoutePreview(BaseModel):
    """Route preview response"""

    total_km: float
    total_min: float
    geometry: Dict[str, Any]  # GeoJSON LineString
    legs: List[Dict[str, Any]]
    debug: Dict[str, Any]
    preview_token: str  # Token to commit this route
    proposed_order: Optional[List[str]] = Field(
        None, description="Proposed stop ID order (START..VIA..END)"
    )
    warnings: Optional[List[Dict[str, Any]]] = Field(
        None, description="Potential issues like long detours"
    )


class RouteCommitRequest(BaseModel):
    """Route commit request"""

    preview_token: str
    name: Optional[str] = None


class RouteLegSchema(BaseModel):
    """Route leg schema"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    route_version_id: str
    seq: int
    distance_km: Optional[float]
    duration_min: Optional[float]
    geojson: Optional[Dict[str, Any]]
    meta: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class RouteVersionSchema(BaseModel):
    """Route version schema"""

    model_config = ConfigDict(from_attributes=True)

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
    stop_snapshot: Optional[List[Dict[str, Any]]]
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Optional relationships
    legs: Optional[List[RouteLegSchema]] = None


class RouteVersionList(BaseModel):
    """Route version list schema"""

    routes: List[RouteVersionSchema]


class RouteVersionUpdate(BaseModel):
    name: Optional[str] = None


class DayRouteActiveSummary(BaseModel):
    day_id: str
    start: Optional[Dict[str, Any]] = None
    end: Optional[Dict[str, Any]] = None
    route_total_km: Optional[float] = None
    route_total_min: Optional[float] = None
    route_coordinates: Optional[List[List[float]]] = None  # [lon, lat]
    route_version_id: Optional[str] = None

class BulkDayRouteSummaryRequest(BaseModel):
    day_ids: List[str]

class BulkDayRouteSummaryResponse(BaseModel):
    summaries: List[DayRouteActiveSummary]
