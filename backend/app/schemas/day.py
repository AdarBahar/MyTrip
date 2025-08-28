"""
Day schemas
"""
from datetime import datetime, date as Date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, computed_field

from app.models.day import DayStatus
from app.schemas.place import PlaceSchema


class DayBase(BaseModel):
    """Base day schema"""
    seq: int = Field(..., gt=0, description="Day sequence number (1, 2, 3, etc.)")
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional notes and metadata")


class DayCreate(BaseModel):
    """Schema for creating a day"""
    seq: Optional[int] = Field(None, gt=0, description="Day sequence number (auto-generated if not provided)")
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional notes and metadata")


class DayUpdate(BaseModel):
    """Schema for updating a day"""
    seq: Optional[int] = Field(None, gt=0, description="Day sequence number")
    status: Optional[DayStatus] = Field(None, description="Day status")
    rest_day: Optional[bool] = Field(None, description="Whether this is a rest day")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional notes and metadata")


class Day(DayBase):
    """Day schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    # Optional trip information for date calculation
    trip_start_date: Optional[Date] = Field(None, description="Trip start date (for calculated_date)")

    @computed_field
    @property
    def calculated_date(self) -> Optional[Date]:
        """Calculate the date for this day based on trip start date and sequence"""
        if not self.trip_start_date:
            return None

        from datetime import timedelta
        return self.trip_start_date + timedelta(days=self.seq - 1)


class DayList(BaseModel):
    """Day list response schema"""
    days: List[Day]
    total: int
    trip_id: str


class DayWithStops(Day):
    """Day schema with stops included"""
    stops_count: Optional[int] = Field(None, description="Number of stops in this day")
    has_route: Optional[bool] = Field(None, description="Whether this day has a computed route")


class DayListWithStops(BaseModel):
    """Day list response schema with stops information"""
    days: List[DayWithStops]
    total: int
    trip_id: str


class DayLocations(BaseModel):
    day_id: str
    start: Optional[PlaceSchema] = None
    end: Optional[PlaceSchema] = None
    # Optional route summary (start -> via -> end)
    route_total_km: Optional[float] = None
    route_total_min: Optional[float] = None
    route_coordinates: Optional[List[List[float]]] = None  # [ [lon,lat], ... ]


class DayListSummary(BaseModel):
    """Days list along with start/end places for each day"""
    days: List[Day]
    locations: List[DayLocations]
    total: int
    trip_id: str