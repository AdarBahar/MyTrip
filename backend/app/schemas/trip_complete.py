"""
Trip complete schemas for comprehensive trip data responses
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.day import DayWithAllStops
from app.schemas.trip import TripSchema


class TripSummary(BaseModel):
    """Summary statistics for a trip"""

    total_days: int = Field(description="Total number of days in the trip")
    total_stops: int = Field(description="Total number of stops across all days")
    trip_duration_days: Optional[int] = Field(
        None, description="Duration of the trip in days"
    )
    status_breakdown: dict[str, int] = Field(
        default_factory=dict, description="Count of days by status"
    )
    stop_type_breakdown: dict[str, int] = Field(
        default_factory=dict, description="Count of stops by type"
    )


class TripCompleteResponse(BaseModel):
    """Complete trip response with all days and stops included"""

    trip: TripSchema = Field(description="Complete trip information")
    days: list[DayWithAllStops] = Field(
        description="All days ordered by sequence with their stops"
    )
    summary: TripSummary = Field(description="Trip summary statistics")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trip": {
                        "id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",
                        "slug": "summer-road-trip-2024",
                        "title": "Summer Road Trip 2024",
                        "destination": "Israel",
                        "start_date": "2024-07-15",
                        "timezone": "Asia/Jerusalem",
                        "status": "active",
                        "is_published": False,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z",
                        "created_by_user": {
                            "id": "01K4J0CYB3YSGWDZB9N92V3ZQ3",
                            "email": "user@example.com",
                            "name": "John Doe",
                        },
                    },
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
                                        "latitude": 32.0853,
                                        "longitude": 34.7818,
                                    },
                                }
                            ],
                            "stops_count": 3,
                            "has_route": True,
                        }
                    ],
                    "summary": {
                        "total_days": 2,
                        "total_stops": 4,
                        "trip_duration_days": 7,
                        "status_breakdown": {"active": 2, "completed": 0},
                        "stop_type_breakdown": {
                            "ACCOMMODATION": 2,
                            "ATTRACTION": 1,
                            "RESTAURANT": 1,
                        },
                    },
                }
            ]
        }
    )
