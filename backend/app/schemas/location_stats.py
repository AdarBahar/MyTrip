from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class StatsCounts(BaseModel):
    """Counts summary for a time range or segment."""
    location_updates: int = Field(0, description="Total number of location_records in the range")
    driving_sessions: int = Field(0, description="Distinct trip_id values observed in driving_records in the range")
    updates_realtime: int = Field(0, description="Location updates with source_type=realtime")
    updates_batched: int = Field(0, description="Location updates with source_type=batch")


class StatsRange(BaseModel):
    """Time range bounds of the stats."""
    from_: str = Field(..., alias="from", description="Range start (ISO 8601)")
    to: str = Field(..., description="Range end (ISO 8601)")

    model_config = ConfigDict(populate_by_name=True)


class StatsMeta(BaseModel):
    """Meta information about the stats payload."""
    first_seen_at: Optional[str] = Field(None, description="First server_time for this device across all time")
    last_update_at: Optional[str] = Field(None, description="Last server_time for this device across all time")
    generated_at: str = Field(..., description="Timestamp when the stats were generated (ISO 8601)")
    version: str = Field("1.0", description="Stats response version")
    cached: bool = Field(False, description="Whether this response was served from cache")


class StatsSegmentBucket(BaseModel):
    """One segment bucket with time bounds and counts."""
    start: str = Field(..., description="Bucket start (ISO 8601)")
    end: str = Field(..., description="Bucket end (ISO 8601)")
    counts: StatsCounts


class StatsSegments(BaseModel):
    """Segmented breakdown of counts across the requested range."""
    granularity: Optional[Literal["hour", "day"]] = Field(None, description="Segmentation granularity if applied")
    buckets: List[StatsSegmentBucket] = Field(default_factory=list, description="Ordered buckets covering the range")


class StatsResponse(BaseModel):
    """Response model for /location/api/stats"""
    device_name: str = Field(..., description="Resolved device name or provided identifier")
    device_id: str = Field(..., description="Resolved device identifier")
    timeframe: Literal["today", "last_24h", "last_7d", "last_week", "total", "custom"] = Field(
        ..., description="Timeframe used to compute statistics"
    )
    range: StatsRange
    counts: StatsCounts
    meta: StatsMeta
    segments: Optional[StatsSegments] = Field(None, description="Optional segmented breakdown when requested")


class StatsRequest(BaseModel):
    """POST body for /location/api/stats"""
    device_name: Optional[str] = Field(None, description="Device friendly name (legacy PHP parameter)")
    device_id: Optional[str] = Field(None, description="Device identifier (convenience parameter)")
    timeframe: Literal["today", "last_24h", "last_7d", "last_week", "total", "custom"] = Field(
        "today", description="Requested timeframe"
    )
    from_param: Optional[str] = Field(None, alias="from", description="Custom range start (ISO 8601)")
    to_param: Optional[str] = Field(None, alias="to", description="Custom range end (ISO 8601)")
    segments: Optional[bool] = Field(False, description="Include segmented counts: hourly for last_24h, daily for last_7d")

    model_config = ConfigDict(populate_by_name=True)
