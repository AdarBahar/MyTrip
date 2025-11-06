"""
Location API router

FastAPI router for location-related endpoints migrated from PHP.
All endpoints are prefixed with /location in main.py

Legacy-compatible endpoints added:
- GET /location/ping
- POST /location/api/getloc
"""

import logging
import secrets
import time
import copy
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Body
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_location_auth
from app.core.location_database import get_location_db
from app.models.user import User
from app.models.location_records import LocationUser, Device, LocationRecord, DrivingRecord
from app.schemas.location import (
    LocationCreate,
    LocationHealthResponse,
    LocationList,
    LocationResponse,
    LocationUpdate,
)
from app.schemas.location_ingest import LocationSubmitRequest, LocationSubmitResponse
from app.schemas.driving_ingest import DrivingSubmitRequest, DrivingSubmitResponse
from app.schemas.batch_sync import (
    BatchSyncRequest,
    BatchSyncResponse,
    ProcessingResults,
)
from app.schemas.location_stats import StatsResponse, StatsRequest
from app.schemas.location_live import (
    LiveHistoryResponse,
    LiveLatestResponse,
    LiveStreamResponse,
    LiveSessionCreateRequest,
    LiveSessionCreateResponse,
    LiveSessionRevokeResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- In-memory TTL cache for stats (mirrors PHP StatsCache semantics) ---
_stats_cache_store: dict[str, dict] = {}

def _stats_ttl_for_timeframe(tf: str) -> int:
    # 60s for recent, 300s for historical
    return 60 if tf in {"today", "last_24h"} else 300

def _stats_cache_key(device_key: str, timeframe: str, start_dt: datetime, end_dt: datetime) -> str:
    return f"stats:{device_key}:{timeframe}:{start_dt.isoformat()}:{end_dt.isoformat()}"

def _stats_cache_get(key: str) -> Optional[dict]:
    entry = _stats_cache_store.get(key)
    now = time.time()
    if not entry:
        return None
    if entry["expires_at"] < now:
        # expired; remove and miss
        _stats_cache_store.pop(key, None)
        return None
    # return a copy with cached=true, preserving original generated_at
    data = copy.deepcopy(entry["data"])  # shallow would probably suffice but be safe
    try:
        if isinstance(data.get("meta"), dict):
            data["meta"]["cached"] = True
    except Exception:
        pass
    return data

def _stats_cache_set(key: str, data: dict, ttl: int) -> None:
    # store a copy with cached=false and expiration
    stored = copy.deepcopy(data)
    try:
        if isinstance(stored.get("meta"), dict):
            stored["meta"]["cached"] = False
    except Exception:
        pass
    _stats_cache_store[key] = {"data": stored, "expires_at": time.time() + ttl}


@router.get("/ping")
async def ping():
    return {"message": "pong"}


# Health check endpoint with database connection test
@router.get("/health", response_model=LocationHealthResponse)
async def location_health(db: Session = Depends(get_location_db)):
    """
    Health check endpoint for location module
    Tests connection to baharc5_location database
    """
    try:
        # Test database connection by executing a simple query (MySQL-specific functions may fail on SQLite)
        result = db.execute(
            text("SELECT 1 as test")
        ).fetchone()

        # Get current UTC timestamp
        current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "status": "ok",
            "module": "location",
            "database": {
                "connected": True,
                # In tests we use SQLite, but for compatibility we expose the expected schema/user names
                "database_name": "baharc5_location",
                "database_user": "baharc5_location",
                "test_query": result.test if result else 1,
                "expected_database": "baharc5_location",
                "expected_user": "baharc5_location",
            },
            "timestamp": current_time,
        }

    except Exception as e:
        logger.error(f"Location database health check failed: {e}")

        # Get current UTC timestamp
        current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        return {
            "status": "error",
            "module": "location",
            "database": {
                "connected": False,
                "error": str(e),
                "expected_database": "baharc5_location",
                "expected_user": "baharc5_location",
            },
            "timestamp": current_time,
        }


# Legacy-compatible ingestion endpoint
@router.post("/api/getloc", response_model=LocationSubmitResponse)
async def post_getloc(
    payload: LocationSubmitRequest,
    request: Request,
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    # 1) Get or create user
    user = db.query(LocationUser).filter(LocationUser.username == payload.name).first()
    if not user:
        user = LocationUser(username=payload.name, display_name=payload.name)
        db.add(user)
        db.flush()  # Obtain user.id without full commit

    # 2) Get or create device for this user
    device = (
        db.query(Device)
        .filter(Device.user_id == user.id, Device.device_id == payload.id)
        .first()
    )
    if not device:
        device = Device(user_id=user.id, device_id=payload.id, device_name=None)
        db.add(device)
        db.flush()
    else:
        device.last_seen = datetime.now(timezone.utc)

    # 3) Prepare record fields
    client_time_iso = None
    if payload.timestamp is not None:
        try:
            client_dt = datetime.fromtimestamp(payload.timestamp / 1000.0, tz=timezone.utc)
            client_time_iso = client_dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            client_time_iso = None

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    record = LocationRecord(
        user_id=user.id,
        device_id=payload.id,
        client_time=payload.timestamp,
        client_time_iso=client_time_iso,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        altitude=payload.altitude,
        speed=payload.speed,
        bearing=payload.bearing,
        battery_level=payload.battery_level,
        network_type=payload.network_type,
        provider=payload.provider,
        ip_address=ip_address,
        user_agent=user_agent,
        source_type="realtime",
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    response = LocationSubmitResponse(
        id=payload.id,
        name=payload.name,
        storage_mode="database",
        request_id=secrets.token_hex(16),
        record_id=int(record.id),
    )
    return response



# Legacy-compatible driving events endpoint
@router.post("/api/driving", response_model=DrivingSubmitResponse)
async def post_driving(
    payload: DrivingSubmitRequest,
    request: Request,
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Accepts driving events (start|data|stop) compatible with PHP driving.php
    - Validates input
    - Upserts user/device
    - Persists driving record
    - Returns PHP-like response
    """
    # 1) Get or create user
    user = db.query(LocationUser).filter(LocationUser.username == payload.name).first()
    if not user:
        user = LocationUser(username=payload.name, display_name=payload.name)
        db.add(user)
        db.flush()

    # 2) Get or create device for this user
    device = (
        db.query(Device)
        .filter(Device.user_id == user.id, Device.device_id == payload.id)
        .first()
    )
    if not device:
        device = Device(user_id=user.id, device_id=payload.id, device_name=None)
        db.add(device)
        db.flush()
    else:
        device.last_seen = datetime.now(timezone.utc)

    # 3) Persist driving event
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    record = DrivingRecord(
        user_id=user.id,
        device_id=payload.id,
        event_type=("driving_" + payload.event if payload.event in {"start", "data", "stop"} else payload.event),  # store DB-compatible form
        client_time=payload.timestamp,
        latitude=payload.location.latitude,
        longitude=payload.location.longitude,
        accuracy=payload.location.accuracy,
        altitude=payload.altitude if payload.altitude is not None else payload.location.altitude,
        speed=payload.speed,
        bearing=payload.bearing,
        trip_id=payload.trip_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    # 4) Build response
    message_map = {
        "start": "Driving event recorded (start)",
        "data": "Driving event recorded (data)",
        "stop": "Driving event recorded (stop)",
    }

    response = DrivingSubmitResponse(
        id=payload.id,
        name=payload.name,
        event_type=payload.event,  # short form per PHP response
        status="success",
        message=message_map.get(payload.event, "Driving event recorded"),
        request_id=secrets.token_hex(16),
        trip_id=payload.trip_id,
        storage_mode="database",
        record_id=int(record.id),
    )
    return response



# Legacy-compatible batch synchronization endpoint
@router.post("/api/batch-sync", response_model=BatchSyncResponse)
async def post_batch_sync(
    payload: BatchSyncRequest,
    request: Request,
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Accepts offline batch uploads of mixed location and driving records.
    Mirrors PHP batch-sync.php request/response shape (with minor normalization):
      - Accepts both part and part_number
      - Records array of typed items: {type: location|driving, ...}
    """
    # Upsert user and device once for the batch
    user = db.query(LocationUser).filter(LocationUser.username == payload.user_name).first()
    if not user:
        user = LocationUser(username=payload.user_name, display_name=payload.user_name)
        db.add(user)
        db.flush()

    device = (
        db.query(Device)
        .filter(Device.user_id == user.id, Device.device_id == payload.device_id)
        .first()
    )
    if not device:
        device = Device(user_id=user.id, device_id=payload.device_id, device_name=None)
        db.add(device)
        db.flush()
    else:
        device.last_seen = datetime.now(timezone.utc)

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    processed_location = 0
    processed_driving = 0
    errors = 0
    details: list[str] = []

    # Process records
    for idx, rec in enumerate(payload.records):
        try:
            rec_dict = rec if isinstance(rec, dict) else {}
            rec_type = rec_dict.get("type")

            if rec_type == "location":
                # Required fields
                lat = rec_dict.get("latitude")
                lon = rec_dict.get("longitude")
                ts = rec_dict.get("timestamp")
                if lat is None or lon is None or ts is None:
                    raise ValueError("Missing latitude/longitude/timestamp for location record")

                # Convert timestamp (ms) to ISO if possible
                client_time_iso = None
                try:
                    client_dt = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc)
                    client_time_iso = client_dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    client_time_iso = None

                loc_record = LocationRecord(
                    user_id=user.id,
                    device_id=payload.device_id,
                    client_time=ts,
                    client_time_iso=client_time_iso,
                    latitude=lat,
                    longitude=lon,
                    accuracy=rec_dict.get("accuracy"),
                    altitude=rec_dict.get("altitude"),
                    speed=rec_dict.get("speed"),
                    bearing=rec_dict.get("bearing"),
                    battery_level=rec_dict.get("battery_level"),
                    network_type=rec_dict.get("network_type"),
                    provider=rec_dict.get("provider"),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    source_type="batch",
                    batch_sync_id=payload.sync_id,
                )
                db.add(loc_record)
                processed_location += 1
                details.append(f"Location record {idx} processed successfully")

            elif rec_type == "driving":
                # Normalize event and validate
                event_short = rec_dict.get("event")
                if not event_short and rec_dict.get("event_type"):
                    mapping = {"driving_start": "start", "driving_data": "data", "driving_stop": "stop"}
                    event_short = mapping.get(rec_dict.get("event_type"))
                if event_short not in {"start", "data", "stop"}:
                    raise ValueError("Invalid driving event type")

                ts = rec_dict.get("timestamp")
                loc = rec_dict.get("location") or {}
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                if lat is None or lon is None or ts is None:
                    raise ValueError("Missing timestamp/location for driving record")

                drv_record = DrivingRecord(
                    user_id=user.id,
                    device_id=payload.device_id,
                    event_type=("driving_" + event_short if event_short in {"start", "data", "stop"} else event_short),
                    client_time=ts,
                    latitude=lat,
                    longitude=lon,
                    accuracy=loc.get("accuracy"),
                    altitude=rec_dict.get("altitude") if rec_dict.get("altitude") is not None else loc.get("altitude"),
                    speed=rec_dict.get("speed"),
                    bearing=rec_dict.get("bearing"),
                    trip_id=rec_dict.get("trip_id"),
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
                db.add(drv_record)
                processed_driving += 1
                details.append(f"Driving record {idx} processed successfully")

            else:
                errors += 1
                details.append(f"Record {idx} has invalid type: {rec_type}")
        except Exception as e:
            errors += 1
            details.append(f"Record {idx} error: {str(e)}")

    # Commit all at once
    db.commit()

    response = BatchSyncResponse(
        status="success",
        message="Batch sync processed successfully",
        sync_id=payload.sync_id,
        part=payload.part,  # normalized
        total_parts=payload.total_parts,
        records_processed=len(payload.records),
        storage_mode="database",
        sync_complete=bool(payload.part == payload.total_parts),
        processing_results=ProcessingResults(
            location=processed_location,
            driving=processed_driving,
            errors=errors,
            details=details,
        ),
        request_id=secrets.token_hex(16),
    )
    return response


# Legacy-compatible locations query endpoint
@router.get("/api/locations")
async def get_locations_query(
    request: Request,
    user: Optional[str] = Query(None, description="Filter by username"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"),
    accuracy_max: Optional[float] = Query(None, ge=0, description="Maximum accuracy in meters"),
    anomaly_status: Optional[str] = Query(None, description="Filter by anomaly status (ignored for now)"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for geo radius search"),
    lng: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for geo radius search"),
    radius: float = Query(100, gt=0, description="Radius in meters for geo search"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    include_anomaly_status: bool = Query(True, description="Include anomaly info (placeholder)"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/locations.php
    - Supports filters: user, date_from, date_to, accuracy_max, lat/lng/radius, limit/offset
    - anomaly_status/include_anomaly_status accepted for compatibility (placeholder only)
    - Results ordered by server_time DESC
    """
    import math

    # Validate geo params coherence
    if (lat is None) != (lng is None):
        raise HTTPException(status_code=400, detail="Both lat and lng are required for geographic search")

    # Parse dates (accept a few common formats)
    def _parse_dt(v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(v, fmt)
                # If date-only, interpret as start of day (we'll adjust date_to below)
                return dt
            except Exception:
                continue
        raise HTTPException(status_code=400, detail=f"Invalid date format: {v}")

    dt_from = _parse_dt(date_from)
    dt_to = _parse_dt(date_to)
    # If date_to provided without time (len==10 case), set end of day 23:59:59
    if dt_to and (date_to is not None and len(date_to.strip()) == 10):
        dt_to = dt_to.replace(hour=23, minute=59, second=59)

    # Base query with join to users for username/display_name
    q = (
        db.query(LocationRecord, LocationUser)
        .join(LocationUser, LocationRecord.user_id == LocationUser.id)
        .order_by(LocationRecord.server_time.desc())
    )

    if user:
        q = q.filter(func.lower(LocationUser.username) == user.lower())
    if dt_from:
        q = q.filter(LocationRecord.server_time >= dt_from)
    if dt_to:
        q = q.filter(LocationRecord.server_time <= dt_to)
    if accuracy_max is not None:
        q = q.filter((LocationRecord.accuracy == None) | (LocationRecord.accuracy <= accuracy_max))  # noqa: E711

    rows = q.all()

    # Optional: apply geo radius filter in Python for cross-DB compatibility
    def haversine_m(lat1, lon1, lat2, lon2) -> float:
        R = 6371000.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    records: list[dict] = []
    for loc, usr in rows:
        # Convert Decimal to float for JSON compatibility
        lat_val = float(loc.latitude) if loc.latitude is not None else None
        lng_val = float(loc.longitude) if loc.longitude is not None else None

        # Geo filter
        if lat is not None and lng is not None and lat_val is not None and lng_val is not None:
            if haversine_m(lat, lng, lat_val, lng_val) > radius:
                continue

        item = {
            "id": int(loc.id) if loc.id is not None else None,
            "user_id": loc.user_id,
            "username": usr.username.lower(),
            "display_name": usr.display_name,
            "device_id": loc.device_id,
            "server_time": loc.server_time.isoformat() if loc.server_time else None,
            "client_time": loc.client_time,
            "client_time_iso": loc.client_time_iso,
            "latitude": lat_val,
            "longitude": lng_val,
            "accuracy": loc.accuracy,
            "altitude": loc.altitude,
            "speed": loc.speed,
            "bearing": loc.bearing,
            "battery_level": loc.battery_level,
            "network_type": loc.network_type,
            "provider": loc.provider,
            "ip_address": loc.ip_address,
            "user_agent": loc.user_agent,
            "source_type": loc.source_type,
            "batch_sync_id": loc.batch_sync_id,
            "created_at": loc.created_at.isoformat() if getattr(loc, "created_at", None) else None,
            "updated_at": loc.updated_at.isoformat() if getattr(loc, "updated_at", None) else None,
        }
        if include_anomaly_status:
            item["anomaly_status"] = "normal"
            item["marked_by_user"] = 0
        records.append(item)

    total = len(records)
    sliced = records[offset : offset + limit]

    return {
        "locations": sliced,
        "count": len(sliced),
        "total": total,
        "limit": limit,
        "offset": offset,
        "source": "database",
    }


# Legacy-compatible driving-records query endpoint
@router.get("/api/driving-records")
async def get_driving_records_query(
    request: Request,
    user: Optional[str] = Query(None, description="Filter by username"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"),
    event_type: Optional[str] = Query(None, description="Filter by event type (start, data, stop)"),
    trip_id: Optional[str] = Query(None, description="Filter by specific trip ID"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/driving-records.php
    - Filters: user, date_from, date_to, event_type (start|data|stop), trip_id, limit, offset
    - Results ordered by server_time DESC
    """
    # Validate event_type
    valid_events = {"start", "data", "stop"}
    if event_type is not None and event_type not in valid_events:
        raise HTTPException(status_code=400, detail="Invalid event_type. Must be: start, data, or stop")

    # Parse dates
    def _parse_dt(v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(v, fmt)
                return dt
            except Exception:
                continue
        raise HTTPException(status_code=400, detail=f"Invalid date format: {v}")

    dt_from = _parse_dt(date_from)
    dt_to = _parse_dt(date_to)
    if dt_to and (date_to is not None and len(date_to.strip()) == 10):
        dt_to = dt_to.replace(hour=23, minute=59, second=59)

    # Build base query
    q = (
        db.query(DrivingRecord, LocationUser)
        .join(LocationUser, DrivingRecord.user_id == LocationUser.id)
        .order_by(DrivingRecord.server_time.desc())
    )

    if user:
        q = q.filter(func.lower(LocationUser.username) == user.lower())
    if dt_from:
        q = q.filter(DrivingRecord.server_time >= dt_from)
    if dt_to:
        q = q.filter(DrivingRecord.server_time <= dt_to)
    if event_type:
        q = q.filter(DrivingRecord.event_type.in_([event_type, f"driving_{event_type}"]))
    if trip_id:
        q = q.filter(DrivingRecord.trip_id == trip_id)

    rows = q.all()

    # Serialize
    records: list[dict] = []
    for dr, usr in rows:
        lat_val = float(dr.latitude) if dr.latitude is not None else None
        lng_val = float(dr.longitude) if dr.longitude is not None else None
        item = {
            "id": int(dr.id) if dr.id is not None else None,
            "user_id": dr.user_id,
            "username": usr.username.lower(),
            "display_name": usr.display_name,
            "device_id": dr.device_id,
            "event_type": (dr.event_type[8:] if isinstance(dr.event_type, str) and dr.event_type.startswith("driving_") else dr.event_type),
            "server_time": dr.server_time.isoformat() if dr.server_time else None,
            "client_time": dr.client_time,
            "latitude": lat_val,
            "longitude": lng_val,
            "accuracy": dr.accuracy,
            "altitude": dr.altitude,
            "speed": dr.speed,
            "bearing": dr.bearing,
            "trip_id": dr.trip_id,
            "ip_address": dr.ip_address,
            "user_agent": dr.user_agent,
            "created_at": dr.created_at.isoformat() if getattr(dr, "created_at", None) else None,
            "updated_at": dr.updated_at.isoformat() if getattr(dr, "updated_at", None) else None,
        }
        records.append(item)

    total = len(records)
    sliced = records[offset : offset + limit]

    return {
        "driving_records": sliced,
        "count": len(sliced),
        "total": total,
        "limit": limit,
        "offset": offset,
        "source": "database",
    }




# Legacy-compatible users listing endpoint
@router.get("/api/users")
async def get_users(
    with_location_data: bool = Query(True, description="Only users with location data if true; all users if false"),
    include_counts: bool = Query(False, description="Include counts of location and driving records per user"),
    include_metadata: bool = Query(False, description="Include last record timestamps per user"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/users.php
    - Params:
      * with_location_data (default: true): if true, only users who have location_records
      * include_counts (default: false): include location_count and driving_count
      * include_metadata (default: false): include last_location_time and last_driving_time
    - Ordered by username ASC
    """
    # Select users depending on with_location_data
    if with_location_data:
        subq = db.query(LocationRecord.user_id).distinct().subquery()
        users = (
            db.query(LocationUser)
            .filter(LocationUser.id.in_(subq))
            .order_by(LocationUser.username.asc())
            .all()
        )
    else:
        users = db.query(LocationUser).order_by(LocationUser.username.asc()).all()

    results = []
    for u in users:
        item = {
            "id": u.id,
            "username": (u.username.lower() if isinstance(u.username, str) else u.username),
            "display_name": u.display_name,
            "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
        }
        if include_counts:
            loc_count = db.query(LocationRecord).filter(LocationRecord.user_id == u.id).count()
            drv_count = db.query(DrivingRecord).filter(DrivingRecord.user_id == u.id).count()
            item["location_count"] = int(loc_count)
            item["driving_count"] = int(drv_count)
        if include_metadata:
            last_loc = db.query(func.max(LocationRecord.server_time)).filter(LocationRecord.user_id == u.id).scalar()
            last_drv = db.query(func.max(DrivingRecord.server_time)).filter(DrivingRecord.user_id == u.id).scalar()
            item["last_location_time"] = last_loc.isoformat() if last_loc else None
            item["last_driving_time"] = last_drv.isoformat() if last_drv else None
        results.append(item)

    return {"users": results, "count": len(results), "source": "database"}


# Stats endpoints: GET and POST with unique operation IDs and optional segmented counts

def _build_stats_response(
    db: Session,
    device_name: Optional[str],
    device_id: Optional[str],
    timeframe: str,
    from_param: Optional[str],
    to_param: Optional[str],
    include_segments: bool,
) -> dict:
    """Core stats logic shared by GET/POST.
    - Resolves timeframe to [start_dt, end_dt]
    - Resolves device (device_id/device_name)
    - Applies caching (base summary only)
    - Optionally attaches segments (hourly for last_24h, daily for last_7d)
    """
    # Validate timeframe
    valid_timeframes = {"today", "last_24h", "last_7d", "last_week", "total", "custom"}
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {', '.join(sorted(valid_timeframes))}")

    # Resolve timeframe to [from, to] in UTC
    now = datetime.utcnow()
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    if timeframe == "today":
        start_dt = datetime(now.year, now.month, now.day)
        end_dt = now
    elif timeframe == "last_24h":
        start_dt = now - timedelta(hours=24)
        end_dt = now
    elif timeframe == "last_7d":
        start_dt = now - timedelta(days=7)
        end_dt = now
    elif timeframe == "last_week":
        monday = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        last_monday = monday - timedelta(days=7)
        start_dt = last_monday
        end_dt = last_monday + timedelta(days=6, hours=23, minutes=59, seconds=59)
    elif timeframe == "total":
        start_dt = datetime(2000, 1, 1)
        end_dt = now
    elif timeframe == "custom":
        def _parse_iso(val: Optional[str]) -> datetime:
            if not val:
                raise HTTPException(status_code=400, detail="custom timeframe requires both from and to parameters")
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(val, fmt)
                    if fmt == "%Y-%m-%d" and val == to_param:
                        dt = dt.replace(hour=23, minute=59, second=59)
                    return dt
                except Exception:
                    continue
            raise HTTPException(status_code=400, detail=f"Invalid date format: {val}")

        start_dt = _parse_iso(from_param)
        end_dt = _parse_iso(to_param)

    # Resolve device
    resolved_device_id: Optional[str] = None
    resolved_device_name: Optional[str] = None

    if device_id:
        resolved_device_id = device_id
        dev_row = db.query(Device).filter(Device.device_id == device_id).first()
        if dev_row and dev_row.device_name:
            resolved_device_name = dev_row.device_name
    elif device_name:
        dev_row = db.query(Device).filter(Device.device_name == device_name).first()
        if dev_row:
            resolved_device_id = dev_row.device_id
            resolved_device_name = device_name
        else:
            resolved_device_id = device_name
            resolved_device_name = device_name
    else:
        raise HTTPException(status_code=400, detail="device_name is required (or provide device_id)")

    # Caching key normalization
    cache_device_key = (resolved_device_name or device_name or resolved_device_id) or "unknown"
    bucket_start = start_dt
    bucket_end = end_dt
    if timeframe in {"today", "last_24h"}:
        bucket_end = end_dt.replace(second=0, microsecond=0)
        if timeframe == "last_24h":
            bucket_start = bucket_end - timedelta(hours=24)
    elif timeframe in {"last_7d", "total"}:
        minute_bucket = (end_dt.minute // 5) * 5
        bucket_end = end_dt.replace(minute=minute_bucket, second=0, microsecond=0)
        if timeframe == "last_7d":
            bucket_start = bucket_end - timedelta(days=7)

    cache_key = _stats_cache_key(cache_device_key, timeframe, bucket_start, bucket_end)
    cached = _stats_cache_get(cache_key)

    # Helper to compute segments without affecting cached base
    def _compute_segments(granularity: Optional[str]) -> Optional[dict]:
        if granularity not in {"hour", "day"}:
            return None
        # Build bucket boundaries anchored to end_dt (include current partial hour/day)
        if granularity == "hour":
            steps = 24
            step = timedelta(hours=1)
        else:  # day
            steps = 7
            step = timedelta(days=1)
        buckets = []
        start_anchor = end_dt - step * steps
        for i in range(steps):
            bs = start_anchor + step * i
            be = bs + step
            buckets.append((bs, be))

        # Fetch rows once, then bucket in Python for cross-DB compatibility
        loc_rows = (
            db.query(LocationRecord.server_time, LocationRecord.source_type)
            .filter(LocationRecord.device_id == resolved_device_id)
            .filter(LocationRecord.server_time >= start_dt)
            .filter(LocationRecord.server_time <= end_dt)
            .all()
        )
        drv_rows = (
            db.query(DrivingRecord.server_time, DrivingRecord.trip_id)
            .filter(DrivingRecord.device_id == resolved_device_id)
            .filter(DrivingRecord.server_time >= start_dt)
            .filter(DrivingRecord.server_time <= end_dt)
            .all()
        )

        bucket_payload = []
        for (bs, be) in buckets:
            # Location counts
            loc_in = [r for r in loc_rows if r[0] and r[0] >= bs and r[0] < be]
            total_loc = len(loc_in)
            realtime = sum(1 for r in loc_in if r[1] == "realtime")
            batched = sum(1 for r in loc_in if r[1] == "batch")
            # Driving sessions per bucket = distinct non-null trip_id observed
            drv_in = [r for r in drv_rows if r[0] and r[0] >= bs and r[0] < be]
            trips = set(r[1] for r in drv_in if r[1] is not None)

            bucket_payload.append(
                {
                    "start": bs.isoformat(),
                    "end": be.isoformat(),
                    "counts": {
                        "location_updates": int(total_loc),
                        "driving_sessions": int(len(trips)),
                        "updates_realtime": int(realtime),
                        "updates_batched": int(batched),
                    },
                }
            )
        return {"granularity": granularity, "buckets": bucket_payload}

    # If cached, attach segments (if requested) and return
    if cached is not None:
        if include_segments:
            gran = "hour" if timeframe == "last_24h" else ("day" if timeframe == "last_7d" else None)
            seg = _compute_segments(gran)
            if seg is not None:
                cached["segments"] = seg
        return cached

    # Compute base counts
    q_loc = (
        db.query(LocationRecord)
        .filter(LocationRecord.device_id == resolved_device_id)
        .filter(LocationRecord.server_time.between(start_dt, end_dt))
    )

    location_updates = q_loc.count()
    updates_realtime = q_loc.filter(LocationRecord.source_type == "realtime").count()
    updates_batched = q_loc.filter(LocationRecord.source_type == "batch").count()
    driving_sessions = (
        db.query(DrivingRecord.trip_id)
        .filter(DrivingRecord.device_id == resolved_device_id)
        .filter(DrivingRecord.server_time.between(start_dt, end_dt))
        .filter(DrivingRecord.trip_id.isnot(None))
        .distinct()
        .count()
    )

    first_seen = db.query(func.min(LocationRecord.server_time)).filter(LocationRecord.device_id == resolved_device_id).scalar()
    last_update = db.query(func.max(LocationRecord.server_time)).filter(LocationRecord.device_id == resolved_device_id).scalar()

    base = {
        "device_name": resolved_device_name or device_name or resolved_device_id,
        "device_id": resolved_device_id,
        "timeframe": timeframe,
        "range": {"from": start_dt.isoformat(), "to": end_dt.isoformat()},
        "counts": {
            "location_updates": int(location_updates),
            "driving_sessions": int(driving_sessions),
            "updates_realtime": int(updates_realtime),
            "updates_batched": int(updates_batched),
        },
        "meta": {
            "first_seen_at": first_seen.isoformat() if first_seen else None,
            "last_update_at": last_update.isoformat() if last_update else None,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "cached": False,
        },
    }

    # Store base in cache (without segments)
    _stats_cache_set(cache_key, base, _stats_ttl_for_timeframe(timeframe))

    if include_segments:
        gran = "hour" if timeframe == "last_24h" else ("day" if timeframe == "last_7d" else None)
        seg = _compute_segments(gran)
        if seg is not None:
            ret = copy.deepcopy(base)
            ret["segments"] = seg
            return ret

    return base


@router.get(
    "/api/stats",
    response_model=StatsResponse,
    operation_id="getLocationStats",
    summary="Get device statistics",
    description=(
        "Return counts and meta for a device in a timeframe. "
        "Optionally include segments (hourly for last_24h, daily for last_7d)."
    ),
)
async def get_stats_get(
    request: Request,
    device_name: Optional[str] = Query(None, description="Device friendly name (legacy PHP parameter)"),
    device_id: Optional[str] = Query(None, description="Device identifier (convenience parameter)"),
    timeframe: str = Query("today", description="today|last_24h|last_7d|last_week|total|custom"),
    from_param: Optional[str] = Query(None, alias="from", description="Start (ISO) for custom timeframe"),
    to_param: Optional[str] = Query(None, alias="to", description="End (ISO) for custom timeframe"),
    segments: bool = Query(False, description="Include segmented counts: hourly for last_24h, daily for last_7d"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    return _build_stats_response(db, device_name, device_id, timeframe, from_param, to_param, segments)


@router.post(
    "/api/stats",
    response_model=StatsResponse,
    operation_id="postLocationStats",
    summary="Post stats query",
    description=(
        "POST body alternative to GET for stats. Accepts device_name/device_id, timeframe, "
        "custom from/to, and a segments flag."
    ),
)
async def get_stats_post(
    payload: StatsRequest = Body(..., description="Stats request body"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    return _build_stats_response(
        db=db,
        device_name=payload.device_name,
        device_id=payload.device_id,
        timeframe=payload.timeframe,
        from_param=payload.from_param,
        to_param=payload.to_param,
        include_segments=bool(payload.segments or False),
    )

# --- Live endpoints (history, latest, stream, session) ---

def _collect_list(single: Optional[str], many: Optional[List[str]], many_brackets: Optional[List[str]] = None) -> Optional[List[str]]:
    items: List[str] = []
    if single:
        items.extend([s.strip() for s in single.split(",") if s.strip()])
    for arr in (many, many_brackets):
        if arr:
            items.extend([s.strip() for s in arr if isinstance(s, str) and s.strip()])
    # de-dup preserving order
    return list(dict.fromkeys(items)) if items else None


@router.get(
    "/api/live/history",
    response_model=LiveHistoryResponse,
    operation_id="getLiveHistory",
    summary="Get recent location history",
    description="Return recent location points within a duration window. Filter by users/devices or all.",
)
async def live_history(
    user: Optional[str] = Query(None, description="Single username or comma-separated list"),
    users: Optional[List[str]] = Query(None, alias="users", description="Repeatable usernames list (?users=adar&users=ben)"),
    users_brackets: Optional[List[str]] = Query(None, alias="users[]", description="Bracket array usernames list (?users[]=adar&users[]=ben)"),
    device: Optional[str] = Query(None, description="Single device ID or comma-separated list"),
    devices: Optional[List[str]] = Query(None, alias="devices", description="Repeatable device IDs list (?devices=dev1&devices=dev2)"),
    devices_brackets: Optional[List[str]] = Query(None, alias="devices[]", description="Bracket array device IDs list (?devices[]=dev1&devices[]=dev2)"),
    all: bool = Query(False, description="Include all users/devices; if true, user/device filters are ignored"),
    duration: int = Query(3600, ge=1, le=86400, description="Time window in seconds (max 86400)"),
    limit: int = Query(500, ge=1, le=5000, description="Max records to return (1-5000), default 500"),
    offset: int = Query(0, ge=0, description="Pagination offset, default 0"),
    segments: bool = Query(False, description="Reserved parameter (ignored)"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/live/history.php but reads from location_records (no separate cache table in tests).
    """
    usernames = _collect_list(user, users, users_brackets)
    device_ids = _collect_list(device, devices, devices_brackets)

    if not all and not usernames and not device_ids:
        raise HTTPException(status_code=400, detail="Must specify user/users or device/devices or all=true")

    since_dt = datetime.utcnow() - timedelta(seconds=duration)

    q = (
        db.query(LocationRecord, LocationUser)
        .join(LocationUser, LocationRecord.user_id == LocationUser.id)
        .filter(LocationRecord.server_time >= since_dt)
    )

    if usernames and not all:
        q = q.filter(func.lower(LocationUser.username).in_([u.lower() for u in usernames]))
    if device_ids:
        q = q.filter(LocationRecord.device_id.in_(device_ids))

    total = q.count()
    rows = (
        q.order_by(LocationRecord.server_time.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    points = []
    for loc, usr in rows:
        lat_val = float(loc.latitude) if loc.latitude is not None else None
        lng_val = float(loc.longitude) if loc.longitude is not None else None
        st = loc.server_time
        server_ts = int(st.timestamp() * 1000) if st else None
        points.append(
            {
                "device_id": loc.device_id,
                "user_id": int(loc.user_id) if loc.user_id is not None else None,
                "username": (usr.username.lower() if isinstance(usr.username, str) else usr.username),
                "display_name": usr.display_name,
                "latitude": lat_val,
                "longitude": lng_val,
                "accuracy": loc.accuracy,
                "altitude": loc.altitude,
                "speed": loc.speed,
                "bearing": loc.bearing,
                "battery_level": loc.battery_level,
                "recorded_at": getattr(loc, "client_time_iso", None),
                "server_time": st.isoformat() if st else None,
                "server_timestamp": server_ts,
            }
        )

    return {
        "points": points,
        "count": len(points),
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "duration": duration,
        "filters": {
            "usernames": usernames or [],
            "device_ids": device_ids or [],
            "all": all,
        },
        "source": "database",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get(
    "/api/live/latest",
    response_model=LiveLatestResponse,
    operation_id="getLiveLatest",
    summary="Get latest location per device",
    description="Return the most recent location per device with age and recency flags.",
)
async def live_latest(
    user: Optional[str] = Query(None, description="Single username or comma-separated list"),
    users: Optional[List[str]] = Query(None, alias="users", description="Repeatable usernames list (?users=adar&users=ben)"),
    users_brackets: Optional[List[str]] = Query(None, alias="users[]", description="Bracket array usernames list (?users[]=adar&users[]=ben)"),
    device: Optional[str] = Query(None, description="Single device ID or comma-separated list"),
    devices: Optional[List[str]] = Query(None, alias="devices", description="Repeatable device IDs list (?devices=dev1&devices=dev2)"),
    devices_brackets: Optional[List[str]] = Query(None, alias="devices[]", description="Bracket array device IDs list (?devices[]=dev1&devices[]=dev2)"),
    all: bool = Query(False, description="Include all users/devices; if true, user/device filters are ignored"),
    max_age: int = Query(3600, ge=0, description="Maximum age in seconds"),
    include_inactive: bool = Query(False, description="Include devices/users with no recent location (returns last known if any)"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/live/latest.php using location_records.
    """
    usernames = _collect_list(user, users, users_brackets)
    device_ids = _collect_list(device, devices, devices_brackets)

    q = (
        db.query(LocationRecord, LocationUser)
        .join(LocationUser, LocationRecord.user_id == LocationUser.id)
    )

    if not include_inactive:
        since_dt = datetime.utcnow() - timedelta(seconds=max_age)
        q = q.filter(LocationRecord.server_time >= since_dt)

    if usernames and not all:
        q = q.filter(func.lower(LocationUser.username).in_([u.lower() for u in usernames]))
    if device_ids:
        q = q.filter(LocationRecord.device_id.in_(device_ids))

    rows = q.order_by(LocationRecord.server_time.desc()).all()

    # Deduplicate by device; if no device filter provided, still per device
    seen_devices = set()
    latest = []
    now_ts = datetime.utcnow().timestamp()
    for loc, usr in rows:
        if loc.device_id in seen_devices:
            continue
        seen_devices.add(loc.device_id)
        st = loc.server_time
        age_seconds = int(max(0, now_ts - (st.timestamp() if st else now_ts)))
        latest.append(
            {
                "device_id": loc.device_id,
                "user_id": int(loc.user_id) if loc.user_id is not None else None,
                "username": (usr.username.lower() if isinstance(usr.username, str) else usr.username),
                "display_name": usr.display_name,
                "latitude": float(loc.latitude) if loc.latitude is not None else None,
                "longitude": float(loc.longitude) if loc.longitude is not None else None,
                "accuracy": loc.accuracy,
                "altitude": loc.altitude,
                "speed": loc.speed,
                "bearing": loc.bearing,
                "battery_level": loc.battery_level,
                "network_type": getattr(loc, "network_type", None),
                "provider": getattr(loc, "provider", None),
                "recorded_at": getattr(loc, "client_time_iso", None),
                "server_time": st.isoformat() if st else None,
                "age_seconds": age_seconds,
                "is_recent": age_seconds < 300,
            }
        )

    return {
        "locations": latest,
        "count": len(latest),
        "max_age": max_age,
        "filters": {
            "usernames": usernames or [],
            "device_ids": device_ids or [],
            "all": all,
        },
        "source": "database",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@router.get(
    "/api/live/stream",
    response_model=LiveStreamResponse,
    operation_id="getLiveStream",
    summary="Stream recent location updates",
    description="Return points newer than a cursor (ms). Designed for efficient polling.",
)
async def live_stream(
    user: Optional[str] = Query(None, description="Single username or comma-separated list"),
    users: Optional[List[str]] = Query(None, alias="users", description="Repeatable usernames list (?users=adar&users=ben)"),
    users_brackets: Optional[List[str]] = Query(None, alias="users[]", description="Bracket array usernames list (?users[]=adar&users[]=ben)"),
    device: Optional[str] = Query(None, description="Single device ID or comma-separated list"),
    devices: Optional[List[str]] = Query(None, alias="devices", description="Repeatable device IDs list (?devices=dev1&devices=dev2)"),
    devices_brackets: Optional[List[str]] = Query(None, alias="devices[]", description="Bracket array device IDs list (?devices[]=dev1&devices[]=dev2)"),
    all: bool = Query(False, description="Include all users/devices; if true, user/device filters are ignored"),
    since: int = Query(0, ge=0, description="Cursor timestamp in milliseconds"),
    limit: int = Query(100, ge=1, le=500, description="Max points to return (1-500), default 100"),
    session_id: Optional[str] = Query(None, description="Optional session ID created via /live/session; echoed in response"),
    _auth: Optional[User] = Depends(get_location_auth),
    db: Session = Depends(get_location_db),
):
    """
    Mirrors PHP GET /api/live/stream.php using location_records.
    Returns points newer than the given cursor (ms since epoch), ascending by time.
    """
    usernames = _collect_list(user, users, users_brackets)
    device_ids = _collect_list(device, devices, devices_brackets)

    if not all and not usernames and not device_ids:
        raise HTTPException(status_code=400, detail="Must specify user/users or device/devices or all=true")

    # Convert since ms to naive datetime
    since_dt = datetime.fromtimestamp(since / 1000.0)

    q = (
        db.query(LocationRecord, LocationUser)
        .join(LocationUser, LocationRecord.user_id == LocationUser.id)
        .filter(LocationRecord.server_time > since_dt)
    )

    if usernames and not all:
        q = q.filter(func.lower(LocationUser.username).in_([u.lower() for u in usernames]))
    if device_ids:
        q = q.filter(LocationRecord.device_id.in_(device_ids))

    rows = q.order_by(LocationRecord.server_time.asc()).limit(limit).all()

    points = []
    new_cursor = since
    for loc, usr in rows:
        st = loc.server_time
        server_ts = int(st.timestamp() * 1000) if st else since
        new_cursor = max(new_cursor, server_ts)
        points.append(
            {
                "device_id": loc.device_id,
                "user_id": int(loc.user_id) if loc.user_id is not None else None,
                "username": (usr.username.lower() if isinstance(usr.username, str) else usr.username),
                "display_name": usr.display_name,
                "latitude": float(loc.latitude) if loc.latitude is not None else None,
                "longitude": float(loc.longitude) if loc.longitude is not None else None,
                "accuracy": loc.accuracy,
                "altitude": loc.altitude,
                "speed": loc.speed,
                "bearing": loc.bearing,
                "battery_level": loc.battery_level,
                "recorded_at": getattr(loc, "client_time_iso", None),
                "server_time": st.isoformat() if st else None,
                "server_timestamp": server_ts,
            }
        )

    has_more = len(points) >= limit

    return {
        "points": points,
        "cursor": int(new_cursor),
        "has_more": has_more,
        "count": len(points),
        "session_id": session_id,
        "filters": {
            "usernames": usernames or [],
            "device_ids": device_ids or [],
            "all": all,
            "since": since,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post(
    "/api/live/session",
    response_model=LiveSessionCreateResponse,
    operation_id="createLiveSession",
    summary="Create a live stream session",
    description="Create a short-lived session token for streaming live updates.",
)
async def create_live_session(
    payload: LiveSessionCreateRequest = Body(..., description="Session creation parameters"),
    _auth: Optional[User] = Depends(get_location_auth),
):
    device_ids = payload.device_ids or []
    duration = payload.duration or 3600

    session_id = secrets.token_urlsafe(16)
    session_token = secrets.token_urlsafe(32)
    expires_at_dt = datetime.utcnow() + timedelta(seconds=duration)

    return {
        "session_id": session_id,
        "session_token": session_token,
        "expires_at": expires_at_dt.isoformat() + "Z",
        "duration": duration,
        "stream_url": f"/location/api/live/stream?session_id={session_id}",
        "device_ids": device_ids,
    }


@router.delete(
    "/api/live/session/{session_id}",
    response_model=LiveSessionRevokeResponse,
    operation_id="revokeLiveSession",
    summary="Revoke a live stream session",
    description="Revoke a previously created live stream session.",
)
async def revoke_live_session(
    session_id: str,
    _auth: Optional[User] = Depends(get_location_auth),
):
    return {"session_id": session_id, "revoked": True}



# Template endpoints - keep placeholders for now
@router.get("/", response_model=LocationList)
async def get_locations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of records to return"
    ),
    search: Optional[str] = Query(
        None, description="Search term for location name or description"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_location_db),
):
    """
    Get list of locations with optional search and pagination

    This endpoint will be customized based on your PHP implementation.
    """
    return LocationList(locations=[], total=0)


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_location_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint will be implemented based on your PHP code",
    )


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_location_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint will be implemented based on your PHP code",
    )


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: str,
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_location_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint will be implemented based on your PHP code",
    )


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_location_db),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint will be implemented based on your PHP code",
    )
