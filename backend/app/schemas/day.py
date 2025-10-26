"""
Day schemas with ISO-8601 date/datetime standardization
"""
from datetime import date as Date

# Forward reference for StopSchema to avoid circular imports
from typing import TYPE_CHECKING, Any, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from app.core.datetime_utils import (
    date_serializer,
    date_validator,
)
from app.models.day import DayStatus
from app.schemas.base import BaseResponseWithSoftDelete, ISO8601Date
from app.schemas.place import PlaceSchema

if TYPE_CHECKING:
    pass


class DayBase(BaseModel):
    """Base day schema"""

    seq: int = Field(..., gt=0, description="Day sequence number (1, 2, 3, etc.)")
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[dict[str, Any]] = Field(
        None, description="Additional notes and metadata"
    )

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, v) -> Optional[dict[str, Any]]:
        """Validate and convert notes field to dictionary format"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            # Convert string to dictionary with a default key
            return {"note": v}
        # For other types, try to convert to string first
        try:
            return {"note": str(v)}
        except Exception:
            return None


class DayCreate(BaseModel):
    """Schema for creating a day"""

    seq: Optional[int] = Field(
        None, gt=0, description="Day sequence number (auto-generated if not provided)"
    )
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[dict[str, Any]] = Field(
        None, description="Additional notes and metadata"
    )

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, v) -> Optional[dict[str, Any]]:
        """Validate and convert notes field to dictionary format"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            # Convert string to dictionary with a default key
            return {"note": v}
        # For other types, try to convert to string first
        try:
            return {"note": str(v)}
        except Exception:
            return None


class DayUpdate(BaseModel):
    """Schema for updating a day"""

    seq: Optional[int] = Field(None, gt=0, description="Day sequence number")
    status: Optional[DayStatus] = Field(None, description="Day status")
    rest_day: Optional[bool] = Field(None, description="Whether this is a rest day")
    notes: Optional[dict[str, Any]] = Field(
        None, description="Additional notes and metadata"
    )

    @field_validator("notes", mode="before")
    @classmethod
    def validate_notes(cls, v) -> Optional[dict[str, Any]]:
        """Validate and convert notes field to dictionary format"""
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            # Convert string to dictionary with a default key
            return {"note": v}
        # For other types, try to convert to string first
        try:
            return {"note": str(v)}
        except Exception:
            return None


class Day(DayBase, BaseResponseWithSoftDelete):
    """Day schema with standardized ISO-8601 datetime fields"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                    "trip_id": "01K367ED2RPNS2H19J8PQDNXFB",
                    "seq": 1,
                    "status": "ACTIVE",
                    "rest_day": False,
                    "notes": {"weather": "sunny", "activities": ["hiking"]},
                    "trip_start_date": "2024-07-15",
                    "calculated_date": "2024-07-15",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "deleted_at": None,
                }
            ],
            "timezone_info": {
                "description": "All datetime fields (created_at, updated_at, deleted_at) are in UTC timezone",
                "format": "ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)",
                "timezone": "UTC",
            },
        },
    )

    trip_id: str = Field(
        description="ID of the trip this day belongs to",
        examples=["01K367ED2RPNS2H19J8PQDNXFB"],
    )

    # Optional trip information for date calculation
    trip_start_date: ISO8601Date = Field(
        None,
        description="Trip start date for calculated_date computation (ISO-8601: YYYY-MM-DD)",
        examples=["2024-07-15"],
    )

    @field_serializer("trip_start_date")
    def serialize_trip_start_date(self, d: Optional[Date]) -> Optional[str]:
        """Serialize trip_start_date to ISO-8601 format"""
        return date_serializer(d)

    @field_validator("trip_start_date", mode="before")
    @classmethod
    def validate_trip_start_date(cls, v) -> Optional[Date]:
        """Validate and parse trip_start_date field"""
        return date_validator(v)

    @computed_field
    @property
    def calculated_date(self) -> Optional[str]:
        """
        Calculate the date for this day based on trip start date and sequence

        Returns ISO-8601 formatted date string for consistency with API standards
        """
        if not self.trip_start_date:
            return None

        from datetime import timedelta

        calculated = self.trip_start_date + timedelta(days=self.seq - 1)
        return date_serializer(calculated)


class DayList(BaseModel):
    """Day list response schema"""

    days: list[Day]
    total: int
    trip_id: str


class DayWithStops(Day):
    """Day schema with stops included"""

    stops_count: Optional[int] = Field(None, description="Number of stops in this day")
    has_route: Optional[bool] = Field(
        None, description="Whether this day has a computed route"
    )


class DayListWithStops(BaseModel):
    """Day list response schema with stops information"""

    days: list[DayWithStops]
    total: int
    trip_id: str


class DayLocations(BaseModel):
    day_id: str
    start: Optional[PlaceSchema] = None
    end: Optional[PlaceSchema] = None
    # Optional route summary (start -> via -> end)
    route_total_km: Optional[float] = None
    route_total_min: Optional[float] = None
    route_coordinates: Optional[list[list[float]]] = None  # [ [lon,lat], ... ]


class DayListSummary(BaseModel):
    """Days list along with start/end places for each day"""

    days: list[Day]
    locations: list[DayLocations]
    total: int
    trip_id: str


class DayWithAllStops(Day):
    """Day schema with complete stops array included"""

    stops: list[Any] = Field(
        default_factory=list, description="All stops for this day ordered by sequence"
    )
    stops_count: Optional[int] = Field(None, description="Number of stops in this day")
    has_route: Optional[bool] = Field(
        None, description="Whether this day has a computed route"
    )


class DaysCompleteResponse(BaseModel):
    """Complete days response with all stops included"""

    trip_id: str
    days: list[DayWithAllStops] = Field(
        description="All days ordered by sequence with their stops"
    )
    total_days: int
    total_stops: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trip_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
                    "days": [
                        {
                            "id": "01K4J0CYB3YSGWDZB9N92V3ZQ5",
                            "trip_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
                            "seq": 1,
                            "status": "active",
                            "rest_day": False,
                            "calculated_date": "2024-07-15",
                            "stops": [
                                {
                                    "id": "01K4J0CYB3YSGWDZB9N92V3ZQ6",
                                    "seq": 1,
                                    "kind": "start",
                                    "stop_type": "ACCOMMODATION",
                                    "place": {
                                        "name": "Grand Hotel",
                                        "address": "123 Main St, Tel Aviv",
                                    },
                                }
                            ],
                            "stops_count": 3,
                            "has_route": True,
                        }
                    ],
                    "total_days": 2,
                    "total_stops": 4,
                }
            ]
        }
    )
