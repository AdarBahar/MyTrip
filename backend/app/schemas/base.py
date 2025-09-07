"""
Base schema classes with standardized ISO-8601 date/datetime handling

Provides consistent date/datetime serialization and validation across all API schemas
with comprehensive timezone awareness and documentation.
"""
from datetime import datetime, date, time
from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator

from app.core.datetime_utils import (
    DateTimeStandards,
    datetime_serializer,
    date_serializer,
    time_serializer,
    datetime_validator,
    date_validator,
    time_validator
)


# Annotated types for consistent date/datetime handling
ISO8601DateTime = Annotated[
    Optional[datetime],
    Field(
        description="ISO-8601 datetime in UTC timezone (YYYY-MM-DDTHH:MM:SSZ)",
        examples=[
            "2024-01-15T10:30:00Z",
            "2024-07-04T14:45:30Z",
            "2024-12-25T00:00:00Z"
        ],
        json_schema_extra={
            "format": "date-time",
            "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$"
        }
    )
]

ISO8601Date = Annotated[
    Optional[date],
    Field(
        description="ISO-8601 date format (YYYY-MM-DD)",
        examples=[
            "2024-01-15",
            "2024-07-04", 
            "2024-12-25"
        ],
        json_schema_extra={
            "format": "date",
            "pattern": r"^\d{4}-\d{2}-\d{2}$"
        }
    )
]

ISO8601Time = Annotated[
    Optional[time],
    Field(
        description="ISO-8601 time format (HH:MM:SS)",
        examples=[
            "10:30:00",
            "14:45:30",
            "00:00:00"
        ],
        json_schema_extra={
            "format": "time",
            "pattern": r"^\d{2}:\d{2}:\d{2}$"
        }
    )
]


class TimestampMixin(BaseModel):
    """
    Mixin for schemas with standardized timestamp fields
    
    Provides created_at and updated_at fields with consistent ISO-8601 serialization
    and timezone awareness for all API responses.
    """
    
    created_at: ISO8601DateTime = Field(
        description="Creation timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: ISO8601DateTime = Field(
        description="Last update timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)",
        examples=["2024-01-15T10:30:00Z"]
    )
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO-8601 format"""
        return datetime_serializer(dt)
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def validate_datetime(cls, v) -> Optional[datetime]:
        """Validate and parse datetime fields"""
        return datetime_validator(v)


class SoftDeleteMixin(BaseModel):
    """
    Mixin for schemas with soft delete functionality
    
    Provides deleted_at field with consistent ISO-8601 serialization
    for soft delete timestamp tracking.
    """
    
    deleted_at: ISO8601DateTime = Field(
        None,
        description="Soft delete timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)",
        examples=["2024-01-15T10:30:00Z", None]
    )
    
    @field_serializer('deleted_at')
    def serialize_deleted_at(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize deleted_at field to ISO-8601 format"""
        return datetime_serializer(dt)
    
    @field_validator('deleted_at', mode='before')
    @classmethod
    def validate_deleted_at(cls, v) -> Optional[datetime]:
        """Validate and parse deleted_at field"""
        return datetime_validator(v)


class BaseSchema(BaseModel):
    """
    Base schema class with standardized configuration
    
    Provides consistent model configuration for all API schemas
    with proper serialization and validation settings.
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [],
            "timezone_info": {
                "description": "All datetime fields are in UTC timezone",
                "format": "ISO-8601 (YYYY-MM-DDTHH:MM:SSZ)",
                "timezone": "UTC"
            }
        }
    )


class BaseResponseSchema(BaseSchema, TimestampMixin):
    """
    Base response schema with ID and timestamps
    
    Standard base class for all API response schemas that include
    ID field and standardized timestamp fields.
    """
    
    id: str = Field(
        description="Unique identifier (ULID format)",
        examples=["01K4AHPK4S1KVTYDB5ASTGTM8K"],
        min_length=26,
        max_length=26
    )


class BaseResponseWithSoftDelete(BaseResponseSchema, SoftDeleteMixin):
    """
    Base response schema with soft delete support
    
    Standard base class for API response schemas that support
    soft delete functionality with deleted_at timestamp.
    """
    pass


class DateRangeSchema(BaseModel):
    """
    Schema for date range queries with ISO-8601 validation
    
    Provides standardized date range handling for filtering
    and querying operations across the API.
    """
    
    start_date: ISO8601Date = Field(
        None,
        description="Start date for range query (ISO-8601: YYYY-MM-DD)",
        examples=["2024-01-01"]
    )
    end_date: ISO8601Date = Field(
        None,
        description="End date for range query (ISO-8601: YYYY-MM-DD)",
        examples=["2024-12-31"]
    )
    
    @field_serializer('start_date', 'end_date')
    def serialize_date(self, d: Optional[date]) -> Optional[str]:
        """Serialize date fields to ISO-8601 format"""
        return date_serializer(d)
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def validate_date(cls, v) -> Optional[date]:
        """Validate and parse date fields"""
        return date_validator(v)
    
    def validate_range(self) -> bool:
        """Validate that start_date is before end_date"""
        if self.start_date and self.end_date:
            return self.start_date <= self.end_date
        return True


class TimeRangeSchema(BaseModel):
    """
    Schema for time range queries with ISO-8601 validation
    
    Provides standardized time range handling for scheduling
    and time-based operations across the API.
    """
    
    start_time: ISO8601Time = Field(
        None,
        description="Start time for range query (ISO-8601: HH:MM:SS)",
        examples=["09:00:00"]
    )
    end_time: ISO8601Time = Field(
        None,
        description="End time for range query (ISO-8601: HH:MM:SS)",
        examples=["17:00:00"]
    )
    
    @field_serializer('start_time', 'end_time')
    def serialize_time(self, t: Optional[time]) -> Optional[str]:
        """Serialize time fields to ISO-8601 format"""
        return time_serializer(t)
    
    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def validate_time(cls, v) -> Optional[time]:
        """Validate and parse time fields"""
        return time_validator(v)
    
    def validate_range(self) -> bool:
        """Validate that start_time is before end_time"""
        if self.start_time and self.end_time:
            return self.start_time <= self.end_time
        return True


class TimezoneInfoSchema(BaseModel):
    """
    Schema for timezone information
    
    Provides timezone metadata for API responses that include
    timezone-aware datetime fields.
    """
    
    timezone: str = Field(
        description="Timezone identifier (IANA timezone database)",
        examples=["UTC", "America/New_York", "Europe/London"]
    )
    utc_offset: str = Field(
        description="UTC offset in ISO-8601 format",
        examples=["+00:00", "-05:00", "+01:00"]
    )
    is_dst: bool = Field(
        description="Whether daylight saving time is currently active"
    )
    abbreviation: str = Field(
        description="Timezone abbreviation",
        examples=["UTC", "EST", "GMT"]
    )


def get_datetime_schema_documentation() -> dict:
    """
    Get comprehensive datetime schema documentation for API docs
    
    Returns documentation about date/datetime handling standards
    used throughout the API for developer reference.
    """
    return {
        "datetime_standards": {
            "description": "All date and datetime fields follow ISO-8601 standards",
            "timezone_handling": "All datetime fields are stored and returned in UTC",
            "formats": {
                "datetime": "YYYY-MM-DDTHH:MM:SSZ (e.g., 2024-01-15T10:30:00Z)",
                "date": "YYYY-MM-DD (e.g., 2024-01-15)",
                "time": "HH:MM:SS (e.g., 10:30:00)"
            },
            "examples": {
                "datetime": [
                    "2024-01-15T10:30:00Z",
                    "2024-07-04T14:45:30Z",
                    "2024-12-25T00:00:00Z"
                ],
                "date": [
                    "2024-01-15",
                    "2024-07-04",
                    "2024-12-25"
                ],
                "time": [
                    "10:30:00",
                    "14:45:30",
                    "00:00:00"
                ]
            }
        },
        "best_practices": [
            "Always use ISO-8601 format for date/datetime fields",
            "Store all datetimes in UTC timezone",
            "Convert to user timezone for display only",
            "Include timezone information when relevant",
            "Use null for optional date/datetime fields"
        ],
        "validation": {
            "datetime": "Must be valid ISO-8601 datetime with timezone",
            "date": "Must be valid ISO-8601 date (YYYY-MM-DD)",
            "time": "Must be valid ISO-8601 time (HH:MM:SS)"
        }
    }
