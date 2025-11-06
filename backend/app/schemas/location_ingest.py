"""
Schemas for legacy PHP-compatible location ingestion endpoints

- POST /location/api/getloc
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class LocationSubmitRequest(BaseModel):
    """Request body for /location/api/getloc

    Mirrors the PHP getloc.php expectations.
    """

    id: str = Field(..., min_length=1, max_length=100, description="Device identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Username")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    # Optional telemetry
    accuracy: Optional[float] = Field(None, ge=0)
    altitude: Optional[float] = None
    speed: Optional[float] = Field(None, ge=0)
    bearing: Optional[float] = Field(None, ge=0, le=360)
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    network_type: Optional[str] = Field(None, max_length=20)
    provider: Optional[str] = Field(None, max_length=20)

    # Client timestamp in milliseconds since epoch
    timestamp: Optional[int] = Field(None, ge=0)

    @field_validator("network_type", "provider")
    @classmethod
    def strip_empty(cls, v: Optional[str]):
        if v is None:
            return v
        v = v.strip()
        return v or None


class LocationSubmitResponse(BaseModel):
    id: str
    name: str
    storage_mode: str = Field("database")
    request_id: str
    record_id: int

