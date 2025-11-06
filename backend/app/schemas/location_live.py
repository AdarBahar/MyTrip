from typing import List, Optional
from pydantic import BaseModel, Field


# Shared filter shapes
class LiveCommonFilters(BaseModel):
    usernames: List[str] = Field(default_factory=list, description="Resolved usernames filter")
    device_ids: List[str] = Field(default_factory=list, description="Resolved device IDs filter")
    all: bool = Field(False, description="If true, includes all users/devices")


class LiveStreamFilters(LiveCommonFilters):
    since: Optional[int] = Field(None, description="Cursor timestamp in milliseconds used for this query")


# Data items
class LivePoint(BaseModel):
    device_id: Optional[str] = Field(None, description="Device identifier for the point")
    user_id: Optional[int] = Field(None, description="User ID owning the device")
    username: Optional[str] = Field(None, description="Username owning the device")
    display_name: Optional[str] = Field(None, description="User display name")
    latitude: Optional[float] = Field(None, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, description="Longitude in decimal degrees")
    accuracy: Optional[float] = Field(None, description="Accuracy in meters if provided")
    altitude: Optional[float] = Field(None, description="Altitude in meters if provided")
    speed: Optional[float] = Field(None, description="Speed in m/s if provided")
    bearing: Optional[float] = Field(None, description="Bearing in degrees if provided")
    battery_level: Optional[float] = Field(None, description="Battery level percentage if provided")
    recorded_at: Optional[str] = Field(None, description="Client timestamp ISO if provided")
    server_time: Optional[str] = Field(None, description="Server-side timestamp ISO when persisted")
    server_timestamp: Optional[int] = Field(None, description="Server-side timestamp in ms since epoch")


class LiveLatestItem(BaseModel):
    device_id: Optional[str] = Field(None, description="Device identifier")
    user_id: Optional[int] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    display_name: Optional[str] = Field(None, description="User display name")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")
    accuracy: Optional[float] = Field(None, description="Accuracy in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    speed: Optional[float] = Field(None, description="Speed in m/s")
    bearing: Optional[float] = Field(None, description="Bearing in degrees")
    battery_level: Optional[float] = Field(None, description="Battery level percentage")
    network_type: Optional[str] = Field(None, description="Network type if provided")
    provider: Optional[str] = Field(None, description="Location provider if provided")
    recorded_at: Optional[str] = Field(None, description="Client timestamp (ISO)")
    server_time: Optional[str] = Field(None, description="Server-side timestamp (ISO)")
    age_seconds: int = Field(..., description="Age in seconds from now to server_time")
    is_recent: bool = Field(..., description="True if age_seconds < 300")


# Responses
class LiveHistoryResponse(BaseModel):
    points: List[LivePoint] = Field(default_factory=list, description="History points ordered DESC by time")
    count: int = Field(..., description="Number of points returned in this page")
    total: int = Field(..., description="Total number of points satisfying the filter")
    limit: int = Field(..., description="Requested page size")
    offset: int = Field(..., description="Requested pagination offset")
    duration: int = Field(..., description="History duration window in seconds")
    filters: LiveCommonFilters
    source: str = Field("database", description="Source of the data")
    timestamp: str = Field(..., description="Response creation time (ISO)")


class LiveLatestResponse(BaseModel):
    locations: List[LiveLatestItem] = Field(default_factory=list, description="Latest location per device")
    count: int = Field(..., description="Number of devices returned")
    max_age: int = Field(..., description="Max age filter applied in seconds")
    filters: LiveCommonFilters
    source: str = Field("database", description="Source of the data")
    timestamp: str = Field(..., description="Response creation time (ISO)")


class LiveStreamResponse(BaseModel):
    points: List[LivePoint] = Field(default_factory=list, description="Streamed points newer than cursor")
    cursor: int = Field(..., description="New cursor (ms since epoch) up to the newest point returned")
    has_more: bool = Field(..., description="True if there may be more data beyond the limit")
    count: int = Field(..., description="Number of points returned in this response")
    session_id: Optional[str] = Field(None, description="Session ID if provided")
    filters: LiveStreamFilters
    timestamp: str = Field(..., description="Response creation time (ISO)")


# Session models
class LiveSessionCreateRequest(BaseModel):
    device_ids: Optional[List[str]] = Field(default_factory=list, description="Optional device allowlist for the session")
    duration: Optional[int] = Field(3600, ge=60, le=86400, description="Session duration in seconds (60..86400)")


class LiveSessionCreateResponse(BaseModel):
    session_id: str = Field(..., description="Newly created session identifier")
    session_token: str = Field(..., description="Opaque token for session auth")
    expires_at: str = Field(..., description="Session expiry time (ISO)")
    duration: int = Field(..., description="Session duration in seconds")
    stream_url: str = Field(..., description="Relative stream URL including the session_id as query parameter")
    device_ids: List[str] = Field(default_factory=list, description="Device allowlist")


class LiveSessionRevokeResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    revoked: bool = Field(..., description="Whether the session was revoked")

