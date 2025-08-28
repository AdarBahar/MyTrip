"""
Days API router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from collections import defaultdict
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.day import Day, DayStatus
from app.models.stop import Stop, StopKind
from app.schemas.day import (
    DayCreate, DayUpdate, Day as DaySchema, DayList,
    DayWithStops, DayListWithStops, DayListSummary, DayLocations
)
from app.schemas.place import PlaceSchema
from app.models.route import RouteVersion

router = APIRouter()


def get_trip_and_verify_access(trip_id: str, current_user: User, db: Session) -> Trip:
    """Get trip and verify user has access to it"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.created_by == current_user.id,
        Trip.deleted_at.is_(None)
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@router.get("", response_model=DayList)
async def list_days(
    trip_id: str,
    include_stops: bool = Query(False, description="Include stops count and route info"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **List Days in Trip**

    Get all days for a specific trip, ordered by sequence number.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    if include_stops:
        # Query with stops count and route info
        days_query = db.query(
            Day,
            func.count(Stop.id).label('stops_count')
        ).outerjoin(Stop).filter(
            Day.trip_id == trip_id,
            Day.deleted_at.is_(None)
        ).group_by(Day.id).order_by(Day.seq)

        days_with_counts = days_query.all()

        days_list = []
        for day, stops_count in days_with_counts:
            day_dict = {
                **day.__dict__,
                'stops_count': stops_count,
                'has_route': False,  # TODO: Check for route versions when implemented
                'trip_start_date': trip.start_date  # Add for calculated_date
            }
            days_list.append(DayWithStops(**day_dict))

        return DayListWithStops(
            days=days_list,
            total=len(days_list),
            trip_id=trip_id
        )
    else:
        # Simple query without extra info but include trip start_date for calculated_date
        days = db.query(Day).join(Trip).filter(
            Day.trip_id == trip_id,
            Day.deleted_at.is_(None)
        ).order_by(Day.seq).all()

        # Add trip start_date to each day for calculated_date
        days_with_trip_date = []
        for day in days:
            day_dict = day.__dict__.copy()
            day_dict['trip_start_date'] = trip.start_date
            days_with_trip_date.append(DaySchema.model_validate(day_dict))

        return DayList(
            days=days_with_trip_date,
            total=len(days),
            trip_id=trip_id
        )
@router.get("/summary", response_model=DayListSummary)
async def list_days_with_locations(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List days and include start/end places for each day in a single call.
    Note: This route must appear before the dynamic '/{day_id}' to avoid being captured by it.
    """
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Fetch all days ordered by seq
    days = db.query(Day).filter(
        Day.trip_id == trip_id,
        Day.deleted_at.is_(None)
    ).order_by(Day.seq).all()
    day_by_seq = {d.seq: d for d in days}

    # Fetch START/END stops for all days in one query, eager-loading place
    if days:
        stops = db.query(Stop).options(joinedload(Stop.place)).filter(
            Stop.trip_id == trip_id,
            Stop.day_id.in_([d.id for d in days]),
            Stop.kind.in_([StopKind.START, StopKind.VIA, StopKind.END])
        ).order_by(Stop.day_id, Stop.seq).all()
    else:
        stops = []

    # Build mapping day_id -> DayLocations
    locs_map: dict[str, DayLocations] = {d.id: DayLocations(day_id=d.id) for d in days}

    for s in stops:
        loc = locs_map.get(s.day_id)
        if not loc:
            continue
        place_obj = None
        if s.place:
            place_obj = PlaceSchema.model_validate(s.place)
        if str(s.kind).lower().endswith('start'):
            loc.start = place_obj
        elif str(s.kind).lower().endswith('end'):
            loc.end = place_obj

    # Instead of calling the routing provider here (which can rate limit), attach saved active route if present
    for d in days:
        loc = locs_map.get(d.id)
        # If no loc entry, create an empty one to attach route
        if loc is None:
            loc = DayLocations(day_id=d.id)
            locs_map[d.id] = loc
        # Query active route version (current default) for the day
        rv = (
            db.query(RouteVersion)
            .filter(RouteVersion.day_id == d.id, RouteVersion.is_active == True)
            .order_by(RouteVersion.version.desc())
            .first()
        )
        if rv and rv.geojson:
            try:
                coords = rv.geojson.get("coordinates") if isinstance(rv.geojson, dict) else None
                if coords:
                    loc.route_coordinates = coords
                if rv.total_km is not None:
                    loc.route_total_km = float(rv.total_km)
                if rv.total_min is not None:
                    loc.route_total_min = float(rv.total_min)
            except Exception:
                pass

    # Add trip start_date for calculated_date
    days_with_trip_date = []
    for day in days:
        dd = day.__dict__.copy()
        dd['trip_start_date'] = trip.start_date
        days_with_trip_date.append(DaySchema.model_validate(dd))

    return DayListSummary(
        days=days_with_trip_date,
        locations=list(locs_map.values()),
        total=len(days),
        trip_id=trip_id
    )



@router.post("", response_model=DaySchema)
async def create_day(
    trip_id: str,
    day_data: DayCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Create New Day**

    Add a new day to the trip. If sequence number is not provided,
    it will be auto-generated as the next available number.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Auto-generate sequence number if not provided
    if day_data.seq is None:
        max_seq = db.query(func.max(Day.seq)).filter(
            Day.trip_id == trip_id,
            Day.deleted_at.is_(None)
        ).scalar() or 0
        seq = max_seq + 1
    else:
        seq = day_data.seq

        # Check if sequence number already exists
        existing_day = db.query(Day).filter(
            Day.trip_id == trip_id,
            Day.seq == seq,
            Day.deleted_at.is_(None)
        ).first()

        if existing_day:
            raise HTTPException(
                status_code=400,
                detail=f"Day with sequence number {seq} already exists"
            )

    # Create day
    day = Day(
        trip_id=trip_id,
        seq=seq,
        status=day_data.status,
        rest_day=day_data.rest_day,
        notes=day_data.notes
    )

    db.add(day)
    db.commit()
    db.refresh(day)

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict['trip_start_date'] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.get("/{day_id}", response_model=DaySchema)
async def get_day(
    trip_id: str,
    day_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Get Specific Day**

    Get details for a specific day in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Get day
    day = db.query(Day).filter(
        Day.id == day_id,
        Day.trip_id == trip_id,
        Day.deleted_at.is_(None)
    ).first()

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict['trip_start_date'] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.patch("/{day_id}", response_model=DaySchema)
async def update_day(
    trip_id: str,
    day_id: str,
    day_data: DayUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Update Day**

    Update details for a specific day in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Get day
    day = db.query(Day).filter(
        Day.id == day_id,
        Day.trip_id == trip_id,
        Day.deleted_at.is_(None)
    ).first()

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Check sequence number conflicts if updating seq
    if day_data.seq is not None and day_data.seq != day.seq:
        existing_day = db.query(Day).filter(
            Day.trip_id == trip_id,
            Day.seq == day_data.seq,
            Day.deleted_at.is_(None),
            Day.id != day_id
        ).first()

        if existing_day:
            raise HTTPException(
                status_code=400,
                detail=f"Day with sequence number {day_data.seq} already exists"
            )

    # Update fields
    update_data = day_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(day, field, value)

    db.commit()
    db.refresh(day)

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict['trip_start_date'] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.delete("/{day_id}")
async def delete_day(
    trip_id: str,
    day_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Delete Day**

    Soft delete a day from the trip. This will also soft delete
    all associated stops and routes.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Get day
    day = db.query(Day).filter(
        Day.id == day_id,
        Day.trip_id == trip_id,
        Day.deleted_at.is_(None)
    ).first()

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Soft delete the day (this will cascade to stops and routes via application logic)
    day.soft_delete()

    # TODO: Also soft delete associated stops and route versions
    # This should be handled by the soft delete cascade logic

    db.commit()

    return {"message": "Day deleted successfully"}


# TODO: Add reorder functionality in future enhancement
# @router.post("/{day_id}/reorder")
# async def reorder_day(...):
#     """Reorder days - to be implemented in future enhancement"""
#     pass
