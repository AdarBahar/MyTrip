"""
Route optimization request/response schemas
"""
from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator


class LocationType(str, Enum):
    """Location type enumeration"""
    START = "START"
    STOP = "STOP"
    END = "END"


class Objective(str, Enum):
    """Optimization objective"""
    TIME = "time"
    DISTANCE = "distance"


class VehicleProfile(str, Enum):
    """Vehicle profile enumeration"""
    CAR = "car"
    BIKE = "bike"
    FOOT = "foot"


class Units(str, Enum):
    """Units enumeration"""
    METRIC = "metric"
    IMPERIAL = "imperial"


class AvoidanceOption(str, Enum):
    """Avoidance options"""
    TOLLS = "tolls"
    FERRIES = "ferries"
    HIGHWAYS = "highways"


class OptimizationMeta(BaseModel):
    """Optimization metadata"""
    version: str = Field(default="1.0", description="API version")
    objective: Objective = Field(description="Optimization objective")
    vehicle_profile: VehicleProfile = Field(description="Vehicle profile")
    units: Units = Field(default=Units.METRIC, description="Units system")
    avoid: list[AvoidanceOption] = Field(default_factory=list, description="Avoidance options")


class LocationRequest(BaseModel):
    """Location in optimization request"""
    id: str = Field(description="Unique location identifier")
    type: LocationType = Field(description="Location type")
    name: str = Field(description="Location name")
    lat: float = Field(description="Latitude", ge=-90, le=90)
    lng: float = Field(description="Longitude", ge=-180, le=180)
    fixed_seq: bool = Field(description="Whether sequence is fixed")
    seq: Optional[int] = Field(None, description="Sequence number (required if fixed_seq=true for STOP)")

    @validator('seq')
    def validate_seq(cls, v, values):
        """Validate sequence number based on type and fixed_seq"""
        location_type = values.get('type')
        fixed_seq = values.get('fixed_seq')
        
        if location_type == LocationType.START:
            if v is not None and v != 1:
                raise ValueError("START location seq must be 1 if present")
        elif location_type == LocationType.STOP and fixed_seq:
            if v is None:
                raise ValueError("seq is required for STOP with fixed_seq=true")
            if v <= 1:
                raise ValueError("STOP seq must be greater than 1")
        elif location_type == LocationType.END:
            # END should not have seq unless enforced as last
            pass
            
        return v


class OptimizationData(BaseModel):
    """Optimization data container"""
    locations: list[LocationRequest] = Field(description="List of locations to optimize")

    @validator('locations')
    def validate_locations(cls, v):
        """Validate location constraints"""
        if len(v) < 2:
            raise ValueError("At least 2 locations required")
        
        # Check for exactly one START and one END
        start_count = sum(1 for loc in v if loc.type == LocationType.START)
        end_count = sum(1 for loc in v if loc.type == LocationType.END)
        
        if start_count != 1:
            raise ValueError("Exactly one START location required")
        if end_count != 1:
            raise ValueError("Exactly one END location required")
        
        # Check unique IDs
        ids = [loc.id for loc in v]
        if len(ids) != len(set(ids)):
            raise ValueError("All location IDs must be unique")
        
        # Check fixed sequence conflicts
        fixed_seqs = [loc.seq for loc in v if loc.fixed_seq and loc.seq is not None]
        if len(fixed_seqs) != len(set(fixed_seqs)):
            raise ValueError("Fixed sequence numbers must be unique")
        
        return v


class RouteOptimizationRequest(BaseModel):
    """Route optimization request schema"""
    prompt: Optional[str] = Field(None, description="Free-form optimization instructions")
    meta: OptimizationMeta = Field(description="Optimization metadata")
    data: OptimizationData = Field(description="Location data")


class LocationResponse(BaseModel):
    """Location in optimization response"""
    seq: int = Field(description="Sequence number")
    id: str = Field(description="Location identifier")
    type: LocationType = Field(description="Location type")
    name: str = Field(description="Location name")
    lat: float = Field(description="Latitude")
    lng: float = Field(description="Longitude")
    fixed_seq: bool = Field(description="Whether sequence was fixed")
    eta_min: float = Field(description="ETA from START in minutes")
    leg_distance_km: float = Field(description="Distance from previous location in km")
    leg_duration_min: float = Field(description="Duration from previous location in minutes")


class OptimizationSummary(BaseModel):
    """Optimization summary statistics"""
    stop_count: int = Field(description="Number of STOP locations")
    total_distance_km: float = Field(description="Total route distance in km")
    total_duration_min: float = Field(description="Total route duration in minutes")


class GeometryBounds(BaseModel):
    """Geometry bounding box"""
    min_lat: float = Field(description="Minimum latitude")
    min_lng: float = Field(description="Minimum longitude")
    max_lat: float = Field(description="Maximum latitude")
    max_lng: float = Field(description="Maximum longitude")


class RouteGeometry(BaseModel):
    """Route geometry data"""
    type: str = Field(default="LineString", description="GeoJSON type")
    coordinates: list[list[float]] = Field(description="GeoJSON coordinates [lng, lat]")


class OptimizationGeometry(BaseModel):
    """Optimization geometry container"""
    format: str = Field(default="geojson", description="Geometry format")
    route: RouteGeometry = Field(description="Route geometry")
    bounds: GeometryBounds = Field(description="Geometry bounds")


class OptimizationDiagnostics(BaseModel):
    """Optimization diagnostics"""
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made")
    computation_notes: list[str] = Field(default_factory=list, description="Computation notes")


class OptimizationError(BaseModel):
    """Optimization error"""
    code: str = Field(description="Error code")
    message: str = Field(description="Error message")


class RouteOptimizationResponse(BaseModel):
    """Route optimization response schema"""
    version: str = Field(default="1.0", description="API version")
    objective: Objective = Field(description="Optimization objective used")
    units: Units = Field(description="Units used")
    ordered: list[LocationResponse] = Field(description="Optimized location order")
    summary: OptimizationSummary = Field(description="Route summary")
    geometry: OptimizationGeometry = Field(description="Route geometry")
    diagnostics: OptimizationDiagnostics = Field(description="Diagnostics information")
    errors: list[OptimizationError] = Field(default_factory=list, description="Error list")


class RouteOptimizationErrorResponse(BaseModel):
    """Route optimization error response"""
    version: str = Field(default="1.0", description="API version")
    errors: list[OptimizationError] = Field(description="List of errors")
