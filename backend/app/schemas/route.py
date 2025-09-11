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


class DayRouteBreakdownRequest(BaseModel):
    """Request for detailed day route breakdown with optimization support"""

    trip_id: str
    day_id: str
    start: RoutePoint = Field(..., description="Starting point of the day")
    stops: List[RoutePoint] = Field(..., description="Ordered list of stops to visit")
    end: RoutePoint = Field(..., description="Ending point of the day")
    profile: str = Field(default="car", pattern="^(car|motorcycle|bike)$")
    optimize: bool = Field(
        default=False,
        description="Optimize stop order between start and end points"
    )
    fixed_stop_indices: Optional[List[int]] = Field(
        default=None,
        description="Indices of stops that cannot be reordered (0-based)"
    )
    options: Optional[RouteOptions] = None


class RouteSegment(BaseModel):
    """Individual route segment between two points"""

    from_point: RoutePoint = Field(..., description="Starting point of this segment")
    to_point: RoutePoint = Field(..., description="Ending point of this segment")
    distance_km: float = Field(..., description="Distance in kilometers")
    duration_min: float = Field(..., description="Duration in minutes")
    geometry: Dict[str, Any] = Field(..., description="GeoJSON LineString geometry")
    instructions: List[Dict[str, Any]] = Field(..., description="Turn-by-turn instructions")
    segment_type: str = Field(..., description="Type: start_to_stop, stop_to_stop, or stop_to_end")
    segment_index: int = Field(..., description="Order index of this segment")


class DayRouteBreakdownResponse(BaseModel):
    """Detailed breakdown of a day's route with optimization results"""

    trip_id: str
    day_id: str
    total_distance_km: float = Field(..., description="Total distance for the entire day")
    total_duration_min: float = Field(..., description="Total duration for the entire day")
    segments: List[RouteSegment] = Field(..., description="Individual route segments")
    optimized_order: Optional[List[RoutePoint]] = Field(
        default=None,
        description="Optimized order of all points (start + stops + end) if optimization was requested"
    )
    optimization_savings: Optional[Dict[str, float]] = Field(
        default=None,
        description="Savings from optimization: distance_km_saved, duration_min_saved"
    )
    summary: Dict[str, Any] = Field(..., description="Additional summary information")
    computed_at: datetime = Field(..., description="When this breakdown was computed")
