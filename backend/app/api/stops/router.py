"""
Stops API router
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.day import Day
from app.models.stop import Stop, StopType, StopKind
from app.models.place import Place
from app.schemas.stop import (
    StopCreate, StopUpdate, Stop as StopSchema, StopList,
    StopWithPlace, StopTypeInfo, StopReorder, StopBulkReorder,
    StopsSummary
)

router = APIRouter()


def ensure_inherited_start_for_next_day(trip_id: str, current_day: Day, db: Session) -> Optional[Stop]:
    """Ensure Day N+1 has a START stop equal to Day N's END place.
    Returns the created Stop if created, else None.
    """
    # Find next day by sequence
    next_day = db.query(Day).filter(
        Day.trip_id == trip_id,
        Day.seq == current_day.seq + 1,
        Day.deleted_at.is_(None)
    ).first()
    if not next_day:
        return None

    # If a START already exists for the next day, do nothing
    existing_start = db.query(Stop).filter(
        Stop.trip_id == trip_id,
        Stop.day_id == next_day.id,
        Stop.kind == StopKind.START
    ).first()
    if existing_start:
        return None

    # Get previous day's END stop
    prev_end = db.query(Stop).filter(
        Stop.trip_id == trip_id,
        Stop.day_id == current_day.id,
        Stop.kind == StopKind.END
    ).order_by(Stop.seq.desc()).first()
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


def ensure_inherited_start_for_current_day(trip_id: str, current_day: Day, db: Session) -> Optional[Stop]:
    """Ensure current day (N) has a START from previous day's END if none exists."""
    # If day is the first, nothing to inherit
    if current_day.seq <= 1:
        return None

    # If a START already exists for current day, nothing to do
    existing_start = db.query(Stop).filter(
        Stop.trip_id == trip_id,
        Stop.day_id == current_day.id,
        Stop.kind == StopKind.START
    ).first()
    if existing_start:
        return None

    # Find previous day
    prev_day = db.query(Day).filter(
        Day.trip_id == trip_id,
        Day.seq == current_day.seq - 1,
        Day.deleted_at.is_(None)
    ).first()
    if not prev_day:
        return None

    # Get END from previous day
    prev_end = db.query(Stop).filter(
        Stop.trip_id == trip_id,
        Stop.day_id == prev_day.id,
        Stop.kind == StopKind.END
    ).order_by(Stop.seq.desc()).first()
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
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    ).first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Verify ownership (for now, only owners can manage stops)
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this trip")
    
    return trip


def get_day_and_verify_access(day_id: str, trip_id: str, current_user: User, db: Session) -> Day:
    """Get day and verify user has access"""
    day = db.query(Day).filter(
        Day.id == day_id,
        Day.trip_id == trip_id,
        Day.deleted_at.is_(None)
    ).first()
    
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    
    # Verify trip access
    get_trip_and_verify_access(trip_id, current_user, db)
    
    return day


@router.get("/types", response_model=List[StopTypeInfo])
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
            color="#8B5CF6"
        ),
        StopTypeInfo(
            type=StopType.FOOD,
            label="Food & Drink",
            description="Restaurants, cafes, bars, food trucks",
            icon="utensils",
            color="#F59E0B"
        ),
        StopTypeInfo(
            type=StopType.ATTRACTION,
            label="Attractions",
            description="Museums, landmarks, monuments",
            icon="camera",
            color="#EF4444"
        ),
        StopTypeInfo(
            type=StopType.ACTIVITY,
            label="Activities",
            description="Tours, sports, entertainment",
            icon="activity",
            color="#10B981"
        ),
        StopTypeInfo(
            type=StopType.SHOPPING,
            label="Shopping",
            description="Stores, markets, malls",
            icon="shopping-bag",
            color="#F97316"
        ),
        StopTypeInfo(
            type=StopType.GAS,
            label="Fuel & Charging",
            description="Gas stations, EV charging",
            icon="fuel",
            color="#6B7280"
        ),
        StopTypeInfo(
            type=StopType.TRANSPORT,
            label="Transportation",
            description="Airports, train stations, ports",
            icon="plane",
            color="#3B82F6"
        ),
        StopTypeInfo(
            type=StopType.SERVICES,
            label="Services",
            description="Banks, hospitals, repair shops",
            icon="tool",
            color="#8B5CF6"
        ),
        StopTypeInfo(
            type=StopType.NATURE,
            label="Nature",
            description="Parks, beaches, trails, viewpoints",
            icon="tree-pine",
            color="#059669"
        ),
        StopTypeInfo(
            type=StopType.CULTURE,
            label="Culture",
            description="Museums, theaters, galleries",
            icon="palette",
            color="#DC2626"
        ),
        StopTypeInfo(
            type=StopType.NIGHTLIFE,
            label="Nightlife",
            description="Bars, clubs, entertainment venues",
            icon="moon",
            color="#7C3AED"
        ),
        StopTypeInfo(
            type=StopType.OTHER,
            label="Other",
            description="Miscellaneous stops",
            icon="map-pin",
            color="#6B7280"
        )
    ]
    
    return stop_types


@router.get("/{trip_id}/days/{day_id}/stops", response_model=StopList)
async def list_stops(
    trip_id: str,
    day_id: str,
    include_place: bool = Query(False, description="Include place information"),
    stop_type: Optional[str] = Query(None, description="Filter by stop type (case-insensitive)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **List Stops for Day**
    
    Get all stops for a specific day, ordered by sequence number.
    
    **Authentication Required:** You must be the trip owner.
    """
    # Verify access and load day
    day = get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Ensure inherited START exists for current day (auto-fill from previous day END)
    ensure_inherited_start_for_current_day(trip_id, day, db)

    # Build query
    query = db.query(Stop)

    if include_place:
        # Eager-load place and avoid N+1
        query = query.options(joinedload(Stop.place))

    query = query.filter(
        Stop.day_id == day_id,
        Stop.trip_id == trip_id
    )

    # Optional stop_type filter (case-insensitive string)
    if stop_type:
        # Try to coerce string into enum by name or value
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
    # Also support case-insensitive string filter for stop_type
    else:
        try:
            # Accept stop_type as string (e.g., 'food') from query
            from fastapi import Request  # type: ignore
        except Exception:
            Request = None  # noqa

    stops = query.order_by(Stop.seq).all()


    
    # Convert to response format
    stops_data = []
    for stop in stops:
        stop_dict = {
            'id': stop.id,
            'day_id': stop.day_id,
            'trip_id': stop.trip_id,
            'place_id': stop.place_id,
            'seq': stop.seq,
            'kind': stop.kind.value.lower(),
            'fixed': stop.fixed,
            'notes': stop.notes,
            'stop_type': stop.stop_type.value.lower(),
            'arrival_time': stop.arrival_time.strftime('%H:%M:%S') if stop.arrival_time else None,
            'departure_time': stop.departure_time.strftime('%H:%M:%S') if stop.departure_time else None,
            'duration_minutes': stop.duration_minutes,
            'booking_info': stop.booking_info,
            'contact_info': stop.contact_info,
            'cost_info': stop.cost_info,
            'priority': stop.priority,
            'created_at': stop.created_at.isoformat(),
            'updated_at': stop.updated_at.isoformat()
        }

        if include_place:
            if stop.place:
                stop_dict['place'] = {
                    'id': stop.place.id,
                    'name': stop.place.name,
                    'address': stop.place.address,
                    'lat': float(stop.place.lat),
                    'lon': float(stop.place.lon),
                    'meta': stop.place.meta
                }
            else:
                # Place not loaded, let's fetch it manually
                place = db.query(Place).filter(Place.id == stop.place_id).first()
                if place:
                    stop_dict['place'] = {
                        'id': place.id,
                        'name': place.name,
                        'address': place.address,
                        'lat': float(place.lat),
                        'lon': float(place.lon),
                        'meta': place.meta
                    }

        stops_data.append(stop_dict)

    return {'stops': stops_data}


@router.post("/{trip_id}/days/{day_id}/stops", response_model=StopSchema)
async def create_stop(
    trip_id: str,
    day_id: str,
    stop_data: StopCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Create New Stop**
    
    Add a new stop to a specific day.
    
    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)
    
    # Verify place exists
    place = db.query(Place).filter(Place.id == stop_data.place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    
    # Check if sequence number is already taken
    existing_stop = db.query(Stop).filter(
        Stop.day_id == day_id,
        Stop.seq == stop_data.seq
    ).first()
    
    if existing_stop:
        raise HTTPException(
            status_code=400, 
            detail=f"Sequence number {stop_data.seq} is already taken"
        )
    
    # Create stop
    stop = Stop(
        day_id=day_id,
        trip_id=trip_id,
        **stop_data.model_dump()
    )
    
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

    return StopSchema.model_validate(stop)


@router.get("/{trip_id}/days/{day_id}/stops/{stop_id}", response_model=StopSchema)
async def get_stop(
    trip_id: str,
    day_id: str,
    stop_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get Specific Stop**
    
    Get details for a specific stop.
    
    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)
    
    # Get stop
    stop = db.query(Stop).filter(
        Stop.id == stop_id,
        Stop.day_id == day_id,
        Stop.trip_id == trip_id
    ).first()
    
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
    db: Session = Depends(get_db)
):
    """
    **Update Stop**

    Update stop details including type, timing, notes, etc.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get stop
    stop = db.query(Stop).filter(
        Stop.id == stop_id,
        Stop.day_id == day_id,
        Stop.trip_id == trip_id
    ).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # If updating place_id, verify place exists
    if stop_data.place_id and stop_data.place_id != stop.place_id:
        place = db.query(Place).filter(Place.id == stop_data.place_id).first()
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

    # If updating sequence, check for conflicts
    if stop_data.seq and stop_data.seq != stop.seq:
        existing_stop = db.query(Stop).filter(
            Stop.day_id == day_id,
            Stop.seq == stop_data.seq,
            Stop.id != stop_id
        ).first()

        if existing_stop:
            raise HTTPException(
                status_code=400,
                detail=f"Sequence number {stop_data.seq} is already taken"
            )

    # Update fields
    update_data = stop_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stop, field, value)

    db.commit()
    db.refresh(stop)

    return StopSchema.model_validate(stop)


@router.delete("/{trip_id}/days/{day_id}/stops/{stop_id}")
async def delete_stop(
    trip_id: str,
    day_id: str,
    stop_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Delete Stop**

    Remove a stop from the day.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get stop
    stop = db.query(Stop).filter(
        Stop.id == stop_id,
        Stop.day_id == day_id,
        Stop.trip_id == trip_id
    ).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # Delete stop
    db.delete(stop)
    db.commit()

    return {"message": "Stop deleted successfully"}


@router.post("/{trip_id}/days/{day_id}/stops/reorder")
async def reorder_stops(
    trip_id: str,
    day_id: str,
    reorder_data: StopBulkReorder,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Reorder Stops**

    Bulk reorder stops within a day by updating their sequence numbers.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_day_and_verify_access(day_id, trip_id, current_user, db)

    # Get all stops for the day
    stops = db.query(Stop).filter(
        Stop.day_id == day_id,
        Stop.trip_id == trip_id
    ).all()

    stop_dict = {stop.id: stop for stop in stops}

    # Validate all stop IDs exist
    for reorder in reorder_data.reorders:
        if reorder.stop_id not in stop_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Stop {reorder.stop_id} not found"
            )

    # Check for sequence conflicts
    new_sequences = [r.new_seq for r in reorder_data.reorders]
    if len(new_sequences) != len(set(new_sequences)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate sequence numbers in reorder request"
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

    return {"message": f"Reordered {len(reorder_data.reorders)} stops successfully"}


@router.get("/{trip_id}/stops/summary", response_model=StopsSummary)
async def get_trip_stops_summary(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get Trip Stops Summary**

    Get a summary of all stops across all days in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify access
    get_trip_and_verify_access(trip_id, current_user, db)

    # Get stops summary by type
    summary = db.query(
        Stop.stop_type,
        func.count(Stop.id).label('count')
    ).filter(
        Stop.trip_id == trip_id
    ).group_by(Stop.stop_type).all()

    # Get total stops count
    total_stops = db.query(func.count(Stop.id)).filter(
        Stop.trip_id == trip_id
    ).scalar()

    # Format response
    summary_dict = {stop_type.value.lower(): 0 for stop_type in StopType}
    for stop_type, count in summary:
        summary_dict[stop_type.value.lower()] = count

    return {
        "trip_id": trip_id,
        "total_stops": total_stops,
        "by_type": summary_dict
    }
