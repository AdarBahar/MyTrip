"""
Stop schemas with ISO-8601 date/datetime/time standardization
"""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer

from app.models.stop import StopKind, StopType
from app.schemas.base import BaseResponseSchema, ISO8601Time, ISO8601DateTime
from app.core.datetime_utils import time_serializer, datetime_serializer, time_validator, datetime_validator


class StopBase(BaseModel):
    """Base stop schema with ISO-8601 time standardization"""
    place_id: str
    seq: int = Field(..., gt=0)
    kind: StopKind
    fixed: bool = False
    notes: Optional[str] = None

    # Enhanced stop management fields with ISO-8601 time standardization
    stop_type: StopType = StopType.OTHER
    arrival_time: ISO8601Time = Field(
        None,
        description="Planned arrival time in ISO-8601 format (HH:MM:SS)",
        examples=["09:00:00", "14:30:00"]
    )
    departure_time: ISO8601Time = Field(
        None,
        description="Planned departure time in ISO-8601 format (HH:MM:SS)",
        examples=["10:00:00", "16:30:00"]
    )
    duration_minutes: Optional[int] = Field(None, gt=0)
    booking_info: Optional[Dict[str, Any]] = None
    contact_info: Optional[Dict[str, Any]] = None
    cost_info: Optional[Dict[str, Any]] = None
    priority: int = Field(3, ge=1, le=5)

    @field_serializer('arrival_time', 'departure_time')
    def serialize_time_fields(self, t: Optional[time]) -> Optional[str]:
        """Serialize time fields to ISO-8601 format"""
        return time_serializer(t)

    @field_validator('arrival_time', 'departure_time', mode='before')
    @classmethod
    def validate_time_fields(cls, v) -> Optional[time]:
        """Validate and parse time fields"""
        return time_validator(v)

    # Coerce string inputs (case-insensitive) into proper enums
    @field_validator('kind', mode='before')
    @classmethod
    def _coerce_kind(cls, v):
        if isinstance(v, str):
            try:
                return StopKind[v.upper()]
            except KeyError:
                # Accept direct value matching too
                for m in StopKind:
                    if m.value.lower() == v.lower():
                        return m
        return v

    @field_validator('stop_type', mode='before')
    @classmethod
    def _coerce_stop_type(cls, v):
        if isinstance(v, str):
            try:
                return StopType[v.upper()]
            except KeyError:
                for m in StopType:
                    if m.value.lower() == v.lower():
                        return m
        return v


class StopCreate(StopBase):
    """Schema for creating a stop"""
    pass


class StopUpdate(BaseModel):
    """Schema for updating a stop"""
    place_id: Optional[str] = None
    seq: Optional[int] = Field(None, gt=0)
    kind: Optional[StopKind] = None
    fixed: Optional[bool] = None
    notes: Optional[str] = None

    # Enhanced stop management fields
    stop_type: Optional[StopType] = None
    arrival_time: Optional[time] = None
    departure_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    booking_info: Optional[Dict[str, Any]] = None
    contact_info: Optional[Dict[str, Any]] = None
    cost_info: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

    @field_validator('stop_type', mode='before')
    @classmethod
    def _coerce_stop_type_update(cls, v):
        if isinstance(v, str):
            try:
                return StopType[v.upper()]
            except KeyError:
                for m in StopType:
                    if m.value.lower() == v.lower():
                        return m
        return v


class Stop(StopBase, BaseResponseSchema):
    """Stop schema with standardized ISO-8601 datetime and time fields"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                    "day_id": "01K367ED2RPNS2H19J8PQDNXFB",
                    "trip_id": "01K367ED2RPNS2H19J8PQDNXFC",
                    "place_id": "01K367ED2RPNS2H19J8PQDNXFD",
                    "seq": 1,
                    "kind": "start",
                    "fixed": True,
                    "notes": "Hotel check-in",
                    "stop_type": "ACCOMMODATION",
                    "arrival_time": "15:00:00",
                    "departure_time": "09:00:00",
                    "duration_minutes": 720,
                    "priority": 1,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            ],
            "timezone_info": {
                "description": "All datetime fields (created_at, updated_at) are in UTC timezone",
                "format": "ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)",
                "timezone": "UTC"
            }
        }
    )

    day_id: str = Field(
        description="ID of the day this stop belongs to",
        examples=["01K367ED2RPNS2H19J8PQDNXFB"]
    )
    trip_id: str = Field(
        description="ID of the trip this stop belongs to",
        examples=["01K367ED2RPNS2H19J8PQDNXFC"]
    )

    # Time serialization is handled by the base class

    @field_validator('stop_type', mode='before')
    @classmethod
    def _coerce_stop_type_update(cls, v):
        if isinstance(v, str):
            try:
                return StopType[v.upper()]
            except KeyError:
                for m in StopType:
                    if m.value.lower() == v.lower():
                        return m
        return v

    # Serialize enums to lowercase strings for client compatibility
    @field_serializer('kind')
    def serialize_kind(self, v):
        try:
            return v.value.lower()
        except Exception:
            return str(v).lower() if isinstance(v, str) else v

    @field_serializer('stop_type')
    def serialize_stop_type(self, v):
        try:
            return v.value.lower()
        except Exception:
            return str(v).lower() if isinstance(v, str) else v


class StopWithPlace(Stop):
    """Stop schema with place information included"""
    place: Optional[Dict[str, Any]] = None


class StopList(BaseModel):
    """Legacy stop list schema (optionally includes place info)"""
    stops: List[StopWithPlace]

# Import enhanced pagination
from app.schemas.pagination import PaginatedResponse

# Modern paginated stop response
StopPaginatedResponse = PaginatedResponse[StopWithPlace]


class StopsUpdate(BaseModel):
    """Schema for updating multiple stops"""
    stops: List[StopCreate] = Field(..., min_items=2)

    @classmethod
    def validate_stops(cls, v):
        """Validate that there's exactly one start and one end"""
        starts = [s for s in v if s.kind == StopKind.START]
        ends = [s for s in v if s.kind == StopKind.END]

        if len(starts) != 1:
            raise ValueError("Exactly one start stop is required")
        if len(ends) != 1:
            raise ValueError("Exactly one end stop is required")
        if starts[0].seq != 1:
            raise ValueError("Start stop must have seq=1")
        if not starts[0].fixed:
            raise ValueError("Start stop must be fixed")
        if not ends[0].fixed:
            raise ValueError("End stop must be fixed")

        return v


class StopTypeInfo(BaseModel):
    """Stop type information for UI"""
    type: StopType
    label: str
    description: str
    icon: str
    color: str

    @field_serializer('type')
    def _serialize_type(self, v: StopType, _info):
        # Emit lowercase string for API consumers/tests
        return v.value.lower()


class StopReorder(BaseModel):
    """Schema for reordering stops within a day"""
    stop_id: str
    new_seq: int = Field(..., gt=0)


class StopBulkReorder(BaseModel):
    """Schema for bulk reordering stops"""
    reorders: List[StopReorder] = Field(..., min_items=1)


class StopsSummary(BaseModel):
    """Schema for trip stops summary"""
    trip_id: str
    total_stops: int
    by_type: Dict[str, int] = Field(
        ...,
        description="Count of stops by type (accommodation, food, attraction, etc.)"
    )