"""
Trip schemas with ISO-8601 date/datetime standardization
"""
from datetime import date, datetime, timedelta
from typing import Optional, List
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer, ValidationError

from app.models.trip import TripStatus, TripMemberRole, TripMemberStatus
from app.schemas.base import BaseResponseSchema, BaseResponseWithSoftDelete, ISO8601Date, ISO8601DateTime
from app.core.datetime_utils import date_serializer, datetime_serializer, date_validator, datetime_validator


class TripCreator(BaseModel):
    """Trip creator user info"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str


class TripBase(BaseModel):
    """Base trip schema with ISO-8601 date standardization"""
    slug: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    start_date: ISO8601Date = Field(
        None,
        description="Trip start date in ISO-8601 format (YYYY-MM-DD)",
        examples=["2024-07-15", "2024-12-25"]
    )
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="Trip timezone (IANA timezone database format)",
        examples=["UTC", "America/New_York", "Europe/London"]
    )
    status: TripStatus = TripStatus.ACTIVE
    is_published: bool = False

    @field_serializer('start_date')
    def serialize_start_date(self, d: Optional[date]) -> Optional[str]:
        """Serialize start_date to ISO-8601 format"""
        return date_serializer(d)

    @field_validator('start_date', mode='before')
    @classmethod
    def validate_start_date(cls, v) -> Optional[date]:
        """Validate and parse start_date field"""
        return date_validator(v)


class TripCreate(BaseModel):
    """Schema for creating a trip with ISO-8601 date standardization"""
    title: str = Field(..., min_length=1, max_length=255, description="Trip title (required)")
    destination: Optional[str] = Field(None, max_length=255, description="Trip destination (optional)")
    start_date: ISO8601Date = Field(
        None,
        description="Trip start date in ISO-8601 format (YYYY-MM-DD) - optional",
        examples=["2024-07-15", "2024-12-25"]
    )
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="Trip timezone (IANA timezone database format) - optional, defaults to UTC",
        examples=["UTC", "America/New_York", "Europe/London"]
    )
    status: TripStatus = Field(TripStatus.DRAFT, description="Trip status (defaults to 'draft')")
    is_published: bool = Field(False, description="Whether the trip is published (defaults to false)")

    @field_serializer('start_date')
    def serialize_start_date(self, d: Optional[date]) -> Optional[str]:
        """Serialize start_date to ISO-8601 format"""
        return date_serializer(d)

    @field_validator('start_date', mode='before')
    @classmethod
    def validate_start_date(cls, v) -> Optional[date]:
        """Validate and parse start_date field"""
        return date_validator(v)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate and sanitize trip title"""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')

        # Sanitize input - remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', v.strip())
        if len(sanitized) < 1:
            raise ValueError('Title must contain valid characters')

        return sanitized

    @field_validator('destination')
    @classmethod
    def validate_destination(cls, v):
        """Validate and sanitize destination"""
        if v is not None:
            # Sanitize input
            sanitized = re.sub(r'[<>"\']', '', v.strip())
            return sanitized if sanitized else None
        return v

    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        """Validate start date with warnings for past/future dates"""
        if v is not None:
            today = date.today()

            # Warn if date is in the past (but allow it)
            if v < today:
                # Note: In a real app, you'd want to return warnings to the frontend
                # For now, we'll just log it
                pass

            # Warn if date is too far in the future (more than 2 years)
            max_future_date = today + timedelta(days=730)  # 2 years
            if v > max_future_date:
                raise ValueError('Start date cannot be more than 2 years in the future')

        return v


class TripUpdate(BaseModel):
    """Schema for updating a trip with ISO-8601 date standardization"""
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    destination: Optional[str] = Field(None, max_length=255)
    start_date: ISO8601Date = Field(
        None,
        description="Trip start date in ISO-8601 format (YYYY-MM-DD)",
        examples=["2024-07-15", "2024-12-25"]
    )
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="Trip timezone (IANA timezone database format)",
        examples=["UTC", "America/New_York", "Europe/London"]
    )
    status: Optional[TripStatus] = None
    is_published: Optional[bool] = None

    @field_serializer('start_date')
    def serialize_start_date(self, d: Optional[date]) -> Optional[str]:
        """Serialize start_date to ISO-8601 format"""
        return date_serializer(d)

    @field_validator('start_date', mode='before')
    @classmethod
    def validate_start_date(cls, v) -> Optional[date]:
        """Validate and parse start_date field"""
        return date_validator(v)


class TripMemberBase(BaseModel):
    """Base trip member schema"""
    role: TripMemberRole
    invited_email: Optional[str] = Field(None, max_length=255)


class TripMemberCreate(TripMemberBase):
    """Schema for creating a trip member"""
    pass


class TripMember(TripMemberBase):
    """Trip member schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    user_id: Optional[str] = None
    status: TripMemberStatus
    created_at: datetime
    updated_at: datetime


class Trip(TripBase, BaseResponseWithSoftDelete):
    """Trip schema with standardized ISO-8601 datetime fields"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                    "slug": "summer-road-trip-2024",
                    "title": "Summer Road Trip 2024",
                    "destination": "California, USA",
                    "start_date": "2024-07-15",
                    "timezone": "America/Los_Angeles",
                    "status": "active",
                    "is_published": False,
                    "created_by": "01K367ED2RPNS2H19J8PQDNXFB",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                    "deleted_at": None
                }
            ],
            "timezone_info": {
                "description": "All datetime fields (created_at, updated_at, deleted_at) are in UTC timezone",
                "format": "ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)",
                "timezone": "UTC"
            }
        }
    )

    created_by: str = Field(
        description="ID of the user who created this trip",
        examples=["01K367ED2RPNS2H19J8PQDNXFB"]
    )

    # Optional relationships
    members: Optional[List[TripMember]] = None
    created_by_user: Optional[TripCreator] = None


class TripCreateResponse(BaseModel):
    """Enhanced trip creation response with next steps"""
    trip: Trip
    next_steps: List[str]
    suggestions: dict

class TripList(BaseModel):
    """Legacy trip list response schema (deprecated)"""
    trips: List[Trip]
    total: int
    page: int
    size: int

# Import enhanced pagination
from app.schemas.pagination import PaginatedResponse

# Modern paginated trip response
TripPaginatedResponse = PaginatedResponse[Trip]