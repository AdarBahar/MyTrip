"""
Day schemas
"""
from datetime import date as Date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.day import DayStatus


class DayBase(BaseModel):
    """Base day schema"""
    seq: int = Field(..., gt=0, description="Day sequence number (1, 2, 3, etc.)")
    date: Optional[Date] = Field(None, description="Specific date for this day (optional)")
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional notes and metadata")


class DayCreate(BaseModel):
    """Schema for creating a day"""
    seq: Optional[int] = Field(None, gt=0, description="Day sequence number (auto-generated if not provided)")
    date: Optional[Date] = Field(None, description="Specific date for this day (optional)")
    status: DayStatus = Field(DayStatus.ACTIVE, description="Day status")
    rest_day: bool = Field(False, description="Whether this is a rest day (no driving)")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional notes and metadata")


class DayUpdate(BaseModel):
    """Schema for updating a day"""
    seq: Optional[int] = Field(None, gt=0, description="Day sequence number")
    date: Optional[Date] = Field(None, description="Specific date for this day")
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