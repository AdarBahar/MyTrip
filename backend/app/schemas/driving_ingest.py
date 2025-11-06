"""
Schemas for legacy-compatible driving events ingestion
"""
from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


EventShort = Literal["start", "data", "stop"]
EventLong = Literal["driving_start", "driving_data", "driving_stop"]


class DrivingLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    altitude: Optional[float] = None


class TripSummary(BaseModel):
    duration_seconds: Optional[float] = Field(None, ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    avg_speed: Optional[float] = Field(None, ge=0)
    max_speed: Optional[float] = Field(None, ge=0)


class DrivingSubmitRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=100, description="Device identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Username")

    # Support both PHP (event) and guide (event_type) inputs
    event: Optional[str] = Field(None, description="Event: start|data|stop")
    event_type: Optional[str] = Field(None, description="Alternative: driving_start|driving_data|driving_stop")

    timestamp: int = Field(..., description="Client timestamp in ms since epoch")
    location: DrivingLocation

    # Optional telemetry
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[float] = Field(None, ge=0, le=360)
    altitude: Optional[float] = None

    # Trip association
    trip_id: Optional[str] = Field(None, max_length=100)
    trip_summary: Optional[TripSummary] = None

    @model_validator(mode="before")
    @classmethod
    def _normalize_event(cls, data: dict):
        # Normalize event/event_type into 'event' field with short form
        if not isinstance(data, dict):
            return data
        event = data.get("event")
        event_type = data.get("event_type")
        if not event and event_type:
            mapping = {
                "driving_start": "start",
                "driving_data": "data",
                "driving_stop": "stop",
            }
            if event_type in mapping:
                data["event"] = mapping[event_type]
        return data

    @model_validator(mode="after")
    def _validate_event(self):
        if self.event not in ("start", "data", "stop"):
            raise ValueError("event must be one of: start, data, stop")
        return self


class DrivingSubmitResponse(BaseModel):
    id: str
    name: str
    event_type: EventShort
    status: Literal["success", "warning", "error"]
    message: str
    request_id: str
    trip_id: Optional[str] = None
    storage_mode: Optional[str] = None
    record_id: Optional[int] = None

