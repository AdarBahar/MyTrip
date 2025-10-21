"""
Stops API router
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.api.routing.router import commit_route as routing_commit_route
from app.api.routing.router import compute_route as routing_compute_route
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.day import Day
from app.models.place import Place as PlaceModel
from app.models.stop import Stop, StopKind, StopType
from app.models.trip import Trip
from app.models.user import User
from app.schemas.bulk import (
    BulkDeleteRequest,
    BulkOperationResult,
    BulkReorderRequest,
    BulkUpdateRequest,
)
from app.schemas.route import RouteCommitRequest, RouteComputeRequest
from app.schemas.sequence import (
    SequenceOperationRequest,
    SequenceOperationResult,
)
from app.schemas.stop import Stop as StopSchema
from app.schemas.stop import (
    StopBulkReorder,
    StopCreate,
    StopList,
    StopsSummary,
    StopTypeInfo,
    StopUpdate,
)
from app.services.bulk_operations import BulkOperationService
from app.services.filtering import FilterCondition, FilteringService, SortCondition
from app.services.sequence_manager import SequenceManager

router = APIRouter()
logger = logging.getLogger(__name__)


def ensure_inherited_start_for_next_day(
    trip_id: str, current_day: Day, db: Session
) -> Optional[Stop]:
    """Ensure Day N+1 has a START stop equal to Day N's END place.
    Returns the created Stop if created, else None.
    """
    # Find next day by sequence
    next_day = (
        db.query(Day)
        .filter(
            Day.trip_id == trip_id,
            Day.seq == current_day.seq + 1,
            Day.deleted_at.is_(None),
        )
        .first()
    )
    if not next_day:
        return None

    # If a START already exists for the next day, do nothing
    existing_start = (
        db.query(Stop)
        .filter(
            Stop.trip_id == trip_id,
            Stop.day_id == next_day.id,
            Stop.kind == StopKind.START,
        )
        .first()
    )
    if existing_start:
        return None

    # Get previous day's END stop
    prev_end = (
        db.query(Stop)
        .filter(
            Stop.trip_id == trip_id,
            Stop.day_id == current_day.id,
            Stop.kind == StopKind.END,
        )
        .order_by(Stop.seq.desc())
        .first()
    )
    if not prev_end:
        return None

    # Create START for next day
    new_start = Stop(
        day_id=next_day.id,
        trip_id=trip_id,
        place_id=prev_end.place_id,
        seq=1,
        kind=StopKind.START,
        fixed=True,
        stop_type=StopType.OTHER,
    )
    db.add(new_start)
    db.commit()
    db.refresh(new_start)
    return new_start


def ensure_inherited_start_for_current_day(
    trip_id: str, current_day: Day, db: Session
) -> Optional[Stop]:
    """Ensure current day (N) has a START from previous day's END if none exists."""
    # If day is the first, nothing to inherit
    if current_day.seq <= 1:
        return None

    # If a START already exists for current day, nothing to do
    existing_start = (
        db.query(Stop)
        .filter(
            Stop.trip_id == trip_id,
            Stop.day_id == current_day.id,
            Stop.kind == StopKind.START,
        )
        .first()
    )
    if existing_start:
        return None

    # Find previous day
    prev_day = (
        db.query(Day)
        .filter(
            Day.trip_id == trip_id,
            Day.seq == current_day.seq - 1,
            Day.deleted_at.is_(None),
        )
        .first()
    )
    if not prev_day:
        return None

    # Get END from previous day
    prev_end = (
        db.query(Stop)
        .filter(
            Stop.trip_id == trip_id,
            Stop.day_id == prev_day.id,
            Stop.kind == StopKind.END,
        )
        .order_by(Stop.seq.desc())
        .first()
    )
    if not prev_end:
        return None

    # Create START for current day
    new_start = Stop(
        day_id=current_day.id,
        trip_id=trip_id,
        place_id=prev_end.place_id,
        seq=1,
        kind=StopKind.START,
        fixed=True,
        stop_type=StopType.OTHER,
    )
    db.add(new_start)
    db.commit()
    db.refresh(new_start)
    return new_start


def get_trip_and_verify_access(trip_id: str, current_user: User, db: Session) -> Trip:
    """Get trip and verify user has access"""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.deleted_at.is_(None)).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verify ownership (for now, only owners can manage stops)
    if trip.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this trip"
        )

    return trip


def get_day_and_verify_access(
    day_id: str, trip_id: str, current_user: User, db: Session
) -> Day:
    """Get day and verify user has access"""
    day = (
        db.query(Day)
        .filter(Day.id == day_id, Day.trip_id == trip_id, Day.deleted_at.is_(None))
        .first()
    )

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Verify trip access
    get_trip_and_verify_access(trip_id, current_user, db)

    return day


@router.get("/types", response_model=list[StopTypeInfo])
async def get_stop_types():
    """
    **Get Stop Types**

    Get all available stop types with their metadata for UI display.

    **No authentication required** - this is reference data.
    """
    stop_types = [
        StopTypeInfo(
            type=StopType.ACCOMMODATION,
            label="Accommodation",
            description="Hotels, B&Bs, camping, lodging",
            icon="bed",
            color="#8B5CF6",
        ),
        StopTypeInfo(
            type=StopType.FOOD,
            label="Food & Drink",
            description="Restaurants, cafes, bars, food trucks",
            icon="utensils",
            color="#F59E0B",
        ),
        StopTypeInfo(
            type=StopType.ATTRACTION,
            label="Attractions",
            description="Museums, landmarks, monuments",
            icon="camera",
            color="#EF4444",
        ),
        StopTypeInfo(
            type=StopType.ACTIVITY,
            label="Activities",
            description="Tours, sports, entertainment",
            icon="activity",
            color="#10B981",
        ),
        StopTypeInfo(
            type=StopType.SHOPPING,
            label="Shopping",
            description="Stores, markets, malls",
            icon="shopping-bag",
            color="#F97316",
        ),
        StopTypeInfo(
            type=StopType.GAS,
            label="Fuel & Charging",
            description="Gas stations, EV charging",
            icon="fuel",
            color="#6B7280",
        ),
        StopTypeInfo(
            type=StopType.TRANSPORT,
            label="Transportation",
            description="Airports, train stations, ports",
            icon="plane",
            color="#3B82F6",
        ),
        StopTypeInfo(
            type=StopType.SERVICES,
            label="Services",
            description="Banks, hospitals, repair shops",
            icon="tool",
            color="#8B5CF6",
        ),
        StopTypeInfo(
            type=StopType.NATURE,
            label="Nature",
            description="Parks, beaches, trails, viewpoints",
            icon="tree-pine",
            color="#059669",
        ),
        StopTypeInfo(
            type=StopType.CULTURE,
            label="Culture",
            description="Museums, theaters, galleries",
            icon="palette",
            color="#DC2626",
        ),
        StopTypeInfo(
            type=StopType.NIGHTLIFE,
            label="Nightlife",
            description="Bars, clubs, entertainment venues",
            icon="moon",
            color="#7C3AED",
        ),
        StopTypeInfo(
            type=StopType.OTHER,
            label="Other",
            description="Miscellaneous stops",
            icon="map-pin",
            color="#6B7280",
        ),
    ]

    return stop_types


@router.get("/{trip_id}/days/{day_id}/stops", response_model=StopList)
async def list_stops(
    trip_id: str,
    day_id: str,
    include_place: bool = Query(False, description="Include place information"),
    stop_type: Optional[str] = Query(
        None,
        description="Filter by stop type (case-insensitive). Valid values: accommodation, food, attraction, activity, shopping, gas, transport, services, nature, culture, nightlife, other",
        examples=["food", "accommodation", "attraction", "FOOD", "ACCOMMODATION"],
    ),
    # Enhanced filtering and sorting
    filter_string: Optional[str] = Query(
        None,
        description="Advanced filters: field:operator:value,field2:op2:val2",
        examples=[
            "stop_type:eq:food,duration_min:gte:30",
            "seq:gte:2,notes:contains:restaurant",
        ],
    ),
    sort_string: Optional[str] = Query(
        None,
        description="Sort: field:direction,field2:direction2",
        examples=["seq:asc,duration_min:desc", "created_at:desc"],
    ),
    duration_min: Optional[int] = Query(
        None,
        description="Filter by minimum duration (in minutes)",
        examples=[30, 60, 120],
    ),
    duration_max: Optional[int] = Query(
        None,
        description="Filter by maximum duration (in minutes)",
        examples=[120, 240, 480],
    ),
    search: Optional[str] = Query(
        None,
        description="Search in stop notes and place names",
        examples=["restaurant", "museum", "hotel"],
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Enhanced List Stops for Day**

    Get all stops for a specific day with advanced filtering and sorting capabilities.

    **Enhanced Features:**
    - ✅ **Multi-attribute filtering**: Filter by type, duration, notes, etc.
    - ✅ **Flexible sorting**: Sort by sequence, duration, creation date, etc.
    - ✅ **Search functionality**: Search across notes and place names
    - ✅ **Range filters**: Duration min/max filters
    - ✅ **String-based filters**: Advanced filter syntax

    **Valid Stop Types (case-insensitive):**
    - `accommodation` - Hotels, hostels, vacation rentals, camping
    - `food` - Restaurants, cafes, bars, food trucks
    - `attraction` - Museums, landmarks, monuments
    - `activity` - Tours, sports, entertainment
    - `shopping` - Stores, markets, shopping centers
    - `gas` - Gas stations, EV charging stations
    - `transport` - Airports, train stations, bus stops
    - `services` - Banks, post offices, government offices
    - `nature` - Parks, beaches, hiking trails
    - `culture` - Museums, theaters, galleries
    - `nightlife` - Bars, clubs, entertainment venues
    - `other` - Miscellaneous stops

    **Parameter Examples:**
    - `stop_type=food` - Filter for food-related stops
    - `stop_type=ACCOMMODATION` - Filter for accommodation (case-insensitive)
    - `filter_string=stop_type:eq:food,duration_min:gte:30` - Advanced filtering
    - `sort_string=seq:asc,duration_min:desc` - Sort by sequence, then duration
    - `search=restaurant` - Search in notes and place names
    - `duration_min=30&duration_max=120` - Duration range filter

    **Supported Filter Fields:**
    - `stop_type`, `seq`, `duration_min`, `notes`, `created_at`, `updated_at`

    **Supported Sort Fields:**
    - `seq`, `stop_type`, `duration_min`, `created_at`, `updated_at`

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access and load day
    day = get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Ensure inherited START exists for current day (auto-fill from previous day END)
    ensure_inherited_start_for_current_day(trip_id, day, db)

    # Build base query
    query = db.query(Stop)

    if include_place:
        # Eager-load place and avoid N+1
        query = query.options(joinedload(Stop.place))

    query = query.filter(Stop.day_id == day_id, Stop.trip_id == trip_id)

    # Initialize filtering service
    filtering_service = FilteringService()

    # Legacy stop_type filter (for backward compatibility)
    if stop_type:
        try:
            enum_val = StopType[stop_type.upper()]
        except KeyError:
            enum_val = None
            for m in StopType:
                if m.value.lower() == stop_type.lower():
                    enum_val = m
                    break
        if enum_val is None:
            raise HTTPException(status_code=422, detail="Invalid stop_type")
        query = query.filter(Stop.stop_type == enum_val)

    # Enhanced filtering
    filter_conditions = []

    # Parse filter string
    if filter_string:
        filter_conditions.extend(filtering_service.parse_filter_string(filter_string))

    # Duration range filters
    if duration_min is not None:
        filter_conditions.append(FilterCondition("duration_min", "gte", duration_min))
    if duration_max is not None:
        filter_conditions.append(FilterCondition("duration_min", "lte", duration_max))

    # Search functionality
    if search:
        # Search in notes and place names (if place is joined)
        search_filter = Stop.notes.ilike(f"%{search}%")
        if include_place:
            from app.models.place import Place

            search_filter = or_(
                Stop.notes.ilike(f"%{search}%"), Place.name.ilike(f"%{search}%")
            )
            query = query.join(Place, Stop.place_id == Place.id, isouter=True)
        query = query.filter(search_filter)

    # Apply advanced filters
    allowed_filter_fields = [
        "stop_type",
        "seq",
        "duration_min",
        "notes",
        "created_at",
        "updated_at",
    ]
    query = filtering_service.apply_filters(
        query, Stop, filter_conditions, allowed_filter_fields
    )

    # Enhanced sorting
    sort_conditions = []
    if sort_string:
        sort_conditions = filtering_service.parse_sort_string(sort_string)

    # Apply sorting with default fallback
    allowed_sort_fields = [
        "seq",
        "stop_type",
        "duration_min",
        "created_at",
        "updated_at",
    ]
    default_sort = SortCondition("seq", "asc")
    query = filtering_service.apply_sorting(
        query, Stop, sort_conditions, allowed_sort_fields, default_sort
    )

    stops = query.all()

    # If include_place is True, ensure all places are loaded
    if include_place:
        # Get all unique place_ids from stops
        place_ids = [stop.place_id for stop in stops if stop.place_id]
        if place_ids:
            # Load all places in one query
            places = db.query(PlaceModel).filter(PlaceModel.id.in_(place_ids)).all()
            places_dict = {place.id: place for place in places}

            # Attach places to stops
            for stop in stops:
                if stop.place_id and stop.place_id in places_dict:
                    stop.place = places_dict[stop.place_id]

    # Convert to response format
    stops_data = []
    for stop in stops:
        stop_dict = {
            "id": stop.id,
            "day_id": stop.day_id,
            "trip_id": stop.trip_id,
            "place_id": stop.place_id,
            "seq": stop.seq,
            "kind": stop.kind.value.lower(),
            "fixed": stop.fixed,
            "notes": stop.notes,
            "stop_type": stop.stop_type.value.lower(),
            "arrival_time": stop.arrival_time.strftime("%H:%M:%S")
            if stop.arrival_time
            else None,
            "departure_time": stop.departure_time.strftime("%H:%M:%S")
            if stop.departure_time
            else None,
            "duration_minutes": stop.duration_minutes,
            "booking_info": stop.booking_info,
            "contact_info": stop.contact_info,
            "cost_info": stop.cost_info,
            "priority": stop.priority,
            "created_at": stop.created_at.isoformat(),
            "updated_at": stop.updated_at.isoformat(),
        }

        if include_place:
            if stop.place:
                stop_dict["place"] = {
                    "id": stop.place.id,
                    "name": stop.place.name,
                    "address": stop.place.address,
                    "lat": float(stop.place.lat),
                    "lon": float(stop.place.lon),
                    "meta": stop.place.meta,
                }
            elif stop.place_id:
                # Place not loaded via joinedload, fetch it manually
                place = (
                    db.query(PlaceModel).filter(PlaceModel.id == stop.place_id).first()
                )
                if place:
                    stop_dict["place"] = {
                        "id": place.id,
                        "name": place.name,
                        "address": place.address,
                        "lat": float(place.lat),
                        "lon": float(place.lon),
                        "meta": place.meta,
                    }
                else:
                    # Place not found, set to None
                    stop_dict["place"] = None
            else:
                # No place_id, set to None
                stop_dict["place"] = None

        stops_data.append(stop_dict)

    return {"stops": stops_data}


@router.post(
    "/{trip_id}/days/{day_id}/stops", response_model=StopSchema, status_code=201
)
async def create_stop(
    trip_id: str,
    day_id: str,
    stop_data: StopCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Create New Stop**

    Add a new stop to a specific day.

    **Request Body Example:**
    ```json
    {
      "place_id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
      "seq": 2,
      "kind": "via",
      "stop_type": "food",
      "duration_minutes": 90,
      "notes": "Lunch at local restaurant",
      "priority": 2
    }
    ```

    **Valid Stop Types:**
    - `accommodation`, `food`, `attraction`, `activity`, `shopping`
    - `gas`, `transport`, `services`, `nature`, `culture`, `nightlife`, `other`

    **Valid Stop Kinds:**
    - `start` - Starting point (sequence 1, fixed)
    - `via` - Intermediate stop (can be reordered)
    - `end` - Final destination (fixed)

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Verify place exists
    place = db.query(PlaceModel).filter(PlaceModel.id == stop_data.place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    # Check if sequence number is already taken
    existing_stop = (
        db.query(Stop).filter(Stop.day_id == day_id, Stop.seq == stop_data.seq).first()
    )

    if existing_stop:
        raise HTTPException(
            status_code=400, detail=f"Sequence number {stop_data.seq} is already taken"
        )

    # Create stop
    stop = Stop(day_id=day_id, trip_id=trip_id, **stop_data.model_dump())

    db.add(stop)
    db.commit()
    db.refresh(stop)

    # If this was an END stop, ensure next day's START is created
    try:
        day = db.query(Day).filter(Day.id == day_id).first()
        if stop.kind == StopKind.END and day:
            ensure_inherited_start_for_next_day(trip_id, day, db)
    except Exception:
        pass

    # Server-side compute+commit to ensure the active route includes the new stop
    try:
        logger.info(f"[stops] compute+commit start: action=add day_id={day_id}")
        # Optimize by default, respect fixed anchors from DB
        compute_req = RouteComputeRequest(
            profile="car", optimize=True, fixed_stop_ids=None
        )
        preview = await routing_compute_route(day_id, compute_req, db)
        commit_req = RouteCommitRequest(
            preview_token=preview.preview_token, name="Default"
        )
        rv = await routing_commit_route(day_id, commit_req, db)
        logger.info(
            f"[stops] compute+commit ok: action=add day_id={day_id} rv={getattr(rv,'id',None)} v={getattr(rv,'version',None)} km={getattr(rv,'total_km',None)} min={getattr(rv,'total_min',None)}"
        )
    except Exception as e:
        logger.warning(
            f"[stops] compute+commit failed: action=add day_id={day_id} err={e}"
        )

    return StopSchema.model_validate(stop)


@router.get("/{trip_id}/days/{day_id}/stops/{stop_id}", response_model=StopSchema)
async def get_stop(
    trip_id: str,
    day_id: str,
    stop_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Get Specific Stop**

    Get details for a specific stop.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get stop
    stop = (
        db.query(Stop)
        .filter(Stop.id == stop_id, Stop.day_id == day_id, Stop.trip_id == trip_id)
        .first()
    )

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    return StopSchema.model_validate(stop)


@router.patch("/{trip_id}/days/{day_id}/stops/{stop_id}", response_model=StopSchema)
async def update_stop(
    trip_id: str,
    day_id: str,
    stop_id: str,
    stop_data: StopUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Update Stop**

    Update stop details including type, timing, notes, etc.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get stop
    stop = (
        db.query(Stop)
        .filter(Stop.id == stop_id, Stop.day_id == day_id, Stop.trip_id == trip_id)
        .first()
    )

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # If updating place_id, verify place exists
    if stop_data.place_id and stop_data.place_id != stop.place_id:
        place = db.query(PlaceModel).filter(PlaceModel.id == stop_data.place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

    # If updating sequence, check for conflicts
    if stop_data.seq and stop_data.seq != stop.seq:
        existing_stop = (
            db.query(Stop)
            .filter(
                Stop.day_id == day_id, Stop.seq == stop_data.seq, Stop.id != stop_id
            )
            .first()
        )

        if existing_stop:
            raise HTTPException(
                status_code=400,
                detail=f"Sequence number {stop_data.seq} is already taken",
            )

    # Update fields
    update_data = stop_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stop, field, value)

    db.commit()
    db.refresh(stop)

    # Server-side compute+commit after stop update
    try:
        logger.info(f"[stops] compute+commit start: action=update day_id={day_id}")
        compute_req = RouteComputeRequest(
            profile="car", optimize=True, fixed_stop_ids=None
        )
        preview = await routing_compute_route(day_id, compute_req, db)
        commit_req = RouteCommitRequest(
            preview_token=preview.preview_token, name="Default"
        )
        rv = await routing_commit_route(day_id, commit_req, db)
        logger.info(
            f"[stops] compute+commit ok: action=update day_id={day_id} rv={getattr(rv,'id',None)} v={getattr(rv,'version',None)} km={getattr(rv,'total_km',None)} min={getattr(rv,'total_min',None)}"
        )
    except Exception as e:
        logger.warning(
            f"[stops] compute+commit failed: action=update day_id={day_id} err={e}"
        )

    return StopSchema.model_validate(stop)


@router.delete("/{trip_id}/days/{day_id}/stops/{stop_id}", status_code=204)
async def delete_stop(
    trip_id: str,
    day_id: str,
    stop_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Delete Stop**

    Remove a stop from the day.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get stop
    stop = (
        db.query(Stop)
        .filter(Stop.id == stop_id, Stop.day_id == day_id, Stop.trip_id == trip_id)
        .first()
    )

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # Delete stop
    db.delete(stop)
    db.commit()

    # Server-side compute+commit after stop delete
    try:
        logger.info(f"[stops] compute+commit start: action=delete day_id={day_id}")
        compute_req = RouteComputeRequest(
            profile="car", optimize=True, fixed_stop_ids=None
        )
        preview = await routing_compute_route(day_id, compute_req, db)
        commit_req = RouteCommitRequest(
            preview_token=preview.preview_token, name="Default"
        )
        rv = await routing_commit_route(day_id, commit_req, db)
        logger.info(
            f"[stops] compute+commit ok: action=delete day_id={day_id} rv={getattr(rv,'id',None)} v={getattr(rv,'version',None)} km={getattr(rv,'total_km',None)} min={getattr(rv,'total_min',None)}"
        )
    except Exception as e:
        logger.warning(
            f"[stops] compute+commit failed: action=delete day_id={day_id} err={e}"
        )

    # Return 204 No Content (no response body)
    return


@router.post("/{trip_id}/days/{day_id}/stops/reorder")
async def reorder_stops(
    trip_id: str,
    day_id: str,
    reorder_data: StopBulkReorder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Reorder Stops**

    Bulk reorder stops within a day by updating their sequence numbers.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get all stops for the day
    stops = db.query(Stop).filter(Stop.day_id == day_id, Stop.trip_id == trip_id).all()

    stop_dict = {stop.id: stop for stop in stops}

    # Validate all stop IDs exist
    for reorder in reorder_data.reorders:
        if reorder.stop_id not in stop_dict:
            raise HTTPException(
                status_code=404, detail=f"Stop {reorder.stop_id} not found"
            )

    # Check for sequence conflicts
    new_sequences = [r.new_seq for r in reorder_data.reorders]
    if len(new_sequences) != len(set(new_sequences)):
        raise HTTPException(
            status_code=400, detail="Duplicate sequence numbers in reorder request"
        )

    # Update sequences in a way that avoids unique constraint violations
    # First, set all sequences to large values to avoid conflicts
    for i, reorder in enumerate(reorder_data.reorders):
        stop = stop_dict[reorder.stop_id]
        stop.seq = 10000 + i  # Use large values temporarily

    db.flush()  # Apply the large values first

    # Then set the actual new sequences
    for reorder in reorder_data.reorders:
        stop = stop_dict[reorder.stop_id]
        stop.seq = reorder.new_seq

    db.commit()

    # Server-side compute+commit after reorder
    try:
        logger.info(f"[stops] compute+commit start: action=reorder day_id={day_id}")
        compute_req = RouteComputeRequest(
            profile="car", optimize=True, fixed_stop_ids=None
        )
        preview = await routing_compute_route(day_id, compute_req, db)
        commit_req = RouteCommitRequest(
            preview_token=preview.preview_token, name="Default"
        )
        rv = await routing_commit_route(day_id, commit_req, db)
        logger.info(
            f"[stops] compute+commit ok: action=reorder day_id={day_id} rv={getattr(rv,'id',None)} v={getattr(rv,'version',None)} km={getattr(rv,'total_km',None)} min={getattr(rv,'total_min',None)}"
        )
    except Exception as e:
        logger.warning(
            f"[stops] compute+commit failed: action=reorder day_id={day_id} err={e}"
        )

    return {"message": f"Reordered {len(reorder_data.reorders)} stops successfully"}


@router.get("/{trip_id}/stops/summary", response_model=StopsSummary)
async def get_trip_stops_summary(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Get Trip Stops Summary**

    Get a summary of all stops across all days in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_trip_and_verify_access(trip_id, current_user, db)

    # Get stops summary by type
    summary = (
        db.query(Stop.stop_type, func.count(Stop.id).label("count"))
        .filter(Stop.trip_id == trip_id)
        .group_by(Stop.stop_type)
        .all()
    )

    # Get total stops count
    total_stops = db.query(func.count(Stop.id)).filter(Stop.trip_id == trip_id).scalar()

    # Format response
    summary_dict = {stop_type.value.lower(): 0 for stop_type in StopType}
    for stop_type, count in summary:
        summary_dict[stop_type.value.lower()] = count

    return {"trip_id": trip_id, "total_stops": total_stops, "by_type": summary_dict}


# Bulk Operations Endpoints


@router.delete("/bulk", response_model=BulkOperationResult, status_code=200)
async def bulk_delete_stops(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Bulk Delete Stops**

    Delete multiple stops in a single operation for improved efficiency.

    **Features:**
    - Delete up to 100 stops at once
    - Automatic route recomputation after deletion
    - Transactional safety (all or nothing)
    - Permission validation for each stop
    - Detailed results for each operation

    **Request Body:**
    ```json
    {
      "ids": ["stop_id_1", "stop_id_2", "stop_id_3"],
      "force": false
    }
    ```

    **Response:**
    ```json
    {
      "total_items": 3,
      "successful": 2,
      "failed": 1,
      "skipped": 0,
      "items": [
        {
          "id": "stop_id_1",
          "status": "success",
          "operation": "delete"
        },
        {
          "id": "stop_id_2",
          "status": "failed",
          "error": "Permission denied",
          "operation": "delete"
        }
      ]
    }
    ```

    **Use Cases:**
    - Clear all stops from a day
    - Remove multiple unwanted stops
    - Cleanup operations
    """
    bulk_service = BulkOperationService(db)

    async def pre_delete_hook(stop: Stop):
        """Hook to handle stop-specific logic before deletion"""
        # Log the deletion for audit purposes
        logger.info(f"Deleting stop {stop.id} from day {stop.day_id}")

    async def post_delete_hook(stop: Stop):
        """Hook to handle post-deletion logic"""
        # Trigger route recomputation for the affected day
        try:
            compute_req = RouteComputeRequest(profile="car", optimize=True)
            await routing_compute_route(stop.day_id, compute_req, db)
        except Exception as e:
            logger.warning(f"Failed to recompute route after stop deletion: {e}")

    return await bulk_service.bulk_delete(
        model_class=Stop,
        ids=request.ids,
        user_id=current_user.id,
        force=request.force,
        pre_delete_hook=pre_delete_hook,
        post_delete_hook=post_delete_hook,
    )


@router.patch("/bulk", response_model=BulkOperationResult, status_code=200)
async def bulk_update_stops(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Bulk Update Stops**

    Update multiple stops in a single operation for improved efficiency.

    **Features:**
    - Update up to 100 stops at once
    - Field-level validation and filtering
    - Automatic route recomputation if positions change
    - Transactional safety
    - Permission validation for each stop

    **Allowed Update Fields:**
    - `duration_min`: Duration at the stop
    - `notes`: Stop notes/description
    - `seq`: Sequence number (triggers route recomputation)
    - `stop_type`: Stop type (accommodation, food, etc.)

    **Request Body:**
    ```json
    {
      "updates": [
        {
          "id": "stop_id_1",
          "data": {
            "duration_min": 60,
            "notes": "Updated notes"
          }
        },
        {
          "id": "stop_id_2",
          "data": {
            "seq": 3,
            "stop_type": "food"
          }
        }
      ]
    }
    ```

    **Use Cases:**
    - Batch update stop durations
    - Change multiple stop types
    - Update notes for multiple stops
    - Reorder multiple stops
    """
    bulk_service = BulkOperationService(db)

    # Define allowed fields for bulk updates
    allowed_fields = ["duration_min", "notes", "seq", "stop_type"]

    async def pre_update_hook(stop: Stop, update_data: dict):
        """Hook to handle stop-specific logic before update"""
        # Validate stop type if being updated
        if "stop_type" in update_data:
            try:
                StopType(update_data["stop_type"])
            except ValueError:
                raise ValueError(f"Invalid stop_type: {update_data['stop_type']}")

        return update_data

    async def post_update_hook(stop: Stop, update_data: dict):
        """Hook to handle post-update logic"""
        # Trigger route recomputation if sequence changed
        if "seq" in update_data:
            try:
                compute_req = RouteComputeRequest(profile="car", optimize=True)
                await routing_compute_route(stop.day_id, compute_req, db)
            except Exception as e:
                logger.warning(f"Failed to recompute route after stop update: {e}")

    return await bulk_service.bulk_update(
        model_class=Stop,
        updates=request.updates,
        user_id=current_user.id,
        allowed_fields=allowed_fields,
        pre_update_hook=pre_update_hook,
        post_update_hook=post_update_hook,
    )


@router.post("/bulk/reorder", response_model=BulkOperationResult, status_code=200)
async def bulk_reorder_stops(
    day_id: str,
    request: BulkReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Bulk Reorder Stops**

    Reorder multiple stops within a day in a single operation.

    **Features:**
    - Reorder up to 50 stops at once
    - Automatic route recomputation
    - Validates sequence numbers
    - Ensures no duplicate positions
    - Scoped to specific day

    **Request Body:**
    ```json
    {
      "items": [
        {"id": "stop_id_1", "seq": 1},
        {"id": "stop_id_2", "seq": 2},
        {"id": "stop_id_3", "seq": 3}
      ]
    }
    ```

    **Response:**
    ```json
    {
      "total_items": 3,
      "successful": 3,
      "failed": 0,
      "items": [
        {
          "id": "stop_id_1",
          "status": "success",
          "operation": "reorder",
          "data": {"new_sequence": 1}
        }
      ]
    }
    ```

    **Use Cases:**
    - Drag-and-drop reordering in UI
    - Optimize stop order
    - Reorganize itinerary
    """
    # Validate day exists and user has access
    day = (
        db.query(Day)
        .join(Trip)
        .filter(Day.id == day_id, Trip.created_by == current_user.id)
        .first()
    )

    if not day:
        raise HTTPException(status_code=404, detail="Day not found or access denied")

    bulk_service = BulkOperationService(db)

    # Perform bulk reorder scoped to the specific day
    result = await bulk_service.bulk_reorder(
        model_class=Stop,
        reorder_items=request.items,
        user_id=current_user.id,
        sequence_field="seq",
        scope_field="day_id",
        scope_value=day_id,
    )

    # Trigger route recomputation if any reordering was successful
    if result.successful > 0:
        try:
            compute_req = RouteComputeRequest(profile="car", optimize=True)
            await routing_compute_route(day_id, compute_req, db)
            logger.info(f"Route recomputed after bulk reorder for day {day_id}")
        except Exception as e:
            logger.warning(f"Failed to recompute route after bulk reorder: {e}")
            # Add warning to result but don't fail the operation
            result.errors.append(
                f"Reorder successful but route recomputation failed: {str(e)}"
            )

    return result


# Sequence Management Endpoints


@router.post("/{stop_id}/sequence", response_model=SequenceOperationResult)
async def reorder_stop_sequence(
    stop_id: str,
    request: SequenceOperationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Smart Sequence Management for Stops**

    Perform intelligent sequence operations to avoid manual sequence number conflicts.

    **Supported Operations:**
    - `move_up`: Move stop up one position
    - `move_down`: Move stop down one position
    - `move_to_top`: Move stop to first position
    - `move_to_bottom`: Move stop to last position
    - `insert_after`: Insert stop after another stop
    - `insert_before`: Insert stop before another stop
    - `move_to_position`: Move stop to specific position

    **Benefits:**
    - ✅ **Conflict-free**: Automatically handles sequence number conflicts
    - ✅ **Collaborative-safe**: Works correctly with multiple users
    - ✅ **Atomic operations**: All changes in single transaction
    - ✅ **Auto-route update**: Triggers route recomputation

    **Examples:**

    Move up one position:
    ```json
    {"operation": "move_up"}
    ```

    Insert after another stop:
    ```json
    {
      "operation": "insert_after",
      "target_id": "other_stop_id"
    }
    ```

    Move to specific position:
    ```json
    {
      "operation": "move_to_position",
      "target_position": 3
    }
    ```
    """
    # Get the stop and verify ownership
    stop = (
        db.query(Stop)
        .join(Day)
        .join(Trip)
        .filter(Stop.id == stop_id, Trip.created_by == current_user.id)
        .first()
    )

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found or access denied")

    # Initialize sequence manager
    seq_manager = SequenceManager(db)

    # Perform the sequence operation scoped to the day
    result = seq_manager.reorder_sequence(
        model_class=Stop,
        item_id=stop_id,
        operation=request.operation,
        target_id=request.target_id,
        target_position=request.target_position,
        scope_filters={"day_id": stop.day_id},
        sequence_field="seq",
    )

    # Trigger route recomputation if operation was successful
    if result.get("success"):
        try:
            compute_req = RouteComputeRequest(profile="car", optimize=True)
            await routing_compute_route(stop.day_id, compute_req, db)
            logger.info(
                f"Route recomputed after sequence operation for day {stop.day_id}"
            )
        except Exception as e:
            logger.warning(f"Failed to recompute route after sequence operation: {e}")
            # Don't fail the sequence operation, just log the warning

    return SequenceOperationResult(**result)
