"""
Trip schemas
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.trip import TripStatus, TripMemberRole, TripMemberStatus


class TripCreator(BaseModel):
    """Trip creator user info"""
    id: str
    email: str
    display_name: str

    class Config:
        from_attributes = True


class TripBase(BaseModel):
    """Base trip schema"""
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    timezone: Optional[str] = Field(None, max_length=50)
    status: TripStatus = TripStatus.ACTIVE
    is_published: bool = False


class TripCreate(BaseModel):
    """Schema for creating a trip"""
    title: str = Field(..., min_length=1, max_length=255, description="Trip title (required)")
    destination: Optional[str] = Field(None, max_length=255, description="Trip destination (optional)")
    start_date: Optional[date] = Field(None, description="Trip start date (optional) - format: YYYY-MM-DD")
    timezone: Optional[str] = Field(None, max_length=50, description="Trip timezone (optional, defaults to UTC)")
    status: TripStatus = Field(TripStatus.DRAFT, description="Trip status (defaults to 'draft')")
    is_published: bool = Field(False, description="Whether the trip is published (defaults to false)")


class TripUpdate(BaseModel):
    """Schema for updating a trip"""
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    timezone: Optional[str] = Field(None, max_length=50)
    status: Optional[TripStatus] = None
    is_published: Optional[bool] = None


class TripMemberBase(BaseModel):
    """Base trip member schema"""
    role: TripMemberRole
    invited_email: Optional[str] = Field(None, max_length=255)


class TripMemberCreate(TripMemberBase):
    """Schema for creating a trip member"""
    pass


class TripMember(TripMemberBase):
    """Trip member schema"""
    id: str
    trip_id: str
    user_id: Optional[str] = None
    status: TripMemberStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Trip(TripBase):
    """Trip schema"""
    id: str
    created_by: str
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Optional relationships
    members: Optional[List[TripMember]] = None
    created_by_user: Optional[TripCreator] = None

    class Config:
        from_attributes = True


class TripList(BaseModel):
    """Trip list response schema"""
    trips: List[Trip]
    total: int
    page: int
    size: int