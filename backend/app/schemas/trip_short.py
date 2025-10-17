"""
Trip short format schemas for compact trip listing with day summaries
"""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.trip import TripStatus


class DaySummary(BaseModel):
    """Summary of a single day with start/end status and stop count"""

    day: int = Field(description="Day sequence number")
    start: bool = Field(description="Whether day has a start stop")
    stops: int = Field(description="Total number of stops in this day")
    end: bool = Field(description="Whether day has an end stop")


class TripShort(BaseModel):
    """Short trip format with basic info and day summaries"""

    id: str = Field(description="Trip ID")
    slug: str = Field(description="Trip URL slug")
    title: str = Field(description="Trip title")
    destination: Optional[str] = Field(None, description="Trip destination")
    start_date: Optional[str] = Field(
        None, description="Trip start date in ISO-8601 format"
    )
    timezone: Optional[str] = Field(None, description="Trip timezone")
    status: TripStatus = Field(description="Trip status")
    is_published: bool = Field(description="Whether trip is published")
    created_by: str = Field(description="User ID who created the trip")
    members: list[str] = Field(
        default_factory=list, description="List of member user IDs"
    )
    total_days: int = Field(description="Total number of days in the trip")
    days: list[DaySummary] = Field(
        description="Day summaries with start/end status and stop counts"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "01K5RPT2HKFSMBAEDXKJ7K8E99",
                    "slug": "summer-road-trip-2024",
                    "title": "Summer Road Trip 2024",
                    "destination": "Europe",
                    "start_date": "2024-07-15",
                    "timezone": "Europe/London",
                    "status": "active",
                    "is_published": False,
                    "created_by": "01K5P68329YFSCTV777EB4GM9P",
                    "members": [],
                    "total_days": 3,
                    "days": [
                        {"day": 1, "start": True, "stops": 4, "end": True},
                        {"day": 2, "start": True, "stops": 3, "end": True},
                        {"day": 3, "start": True, "stops": 2, "end": True},
                    ],
                }
            ]
        },
    )


class TripShortResponse(BaseModel):
    """Response for short format trip listing"""

    data: list[TripShort] = Field(description="List of trips in short format")
    meta: dict[str, Any] = Field(description="Pagination metadata")
    links: dict[str, Optional[str]] = Field(description="Pagination links")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "data": [
                        {
                            "id": "01K5RPT2HKFSMBAEDXKJ7K8E99",
                            "slug": "summer-road-trip-2024",
                            "title": "Summer Road Trip 2024",
                            "destination": "Europe",
                            "start_date": "2024-07-15",
                            "timezone": "Europe/London",
                            "status": "active",
                            "is_published": False,
                            "created_by": "01K5P68329YFSCTV777EB4GM9P",
                            "members": [],
                            "total_days": 2,
                            "days": [
                                {"day": 1, "start": True, "stops": 4, "end": True},
                                {"day": 2, "start": True, "stops": 3, "end": True},
                            ],
                        }
                    ],
                    "meta": {
                        "current_page": 1,
                        "per_page": 20,
                        "total_items": 1,
                        "total_pages": 1,
                    },
                    "links": {
                        "first": "/trips?page=1",
                        "last": "/trips?page=1",
                        "prev": None,
                        "next": None,
                    },
                }
            ]
        }
    )
