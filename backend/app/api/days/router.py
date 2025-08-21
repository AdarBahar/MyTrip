"""
Days API router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trip import Trip
from app.models.day import Day, DayStatus
from app.models.stop import Stop
from app.schemas.day import (
    DayCreate, DayUpdate, Day as DaySchema, DayList, 
    DayWithStops, DayListWithStops
)

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
                'has_route': False  # TODO: Check for route versions when implemented
            }
            days_list.append(DayWithStops(**day_dict))
        
        return DayListWithStops(
            days=days_list,
            total=len(days_list),
            trip_id=trip_id
        )
    else:
        # Simple query without extra info
        days = db.query(Day).filter(
            Day.trip_id == trip_id,
            Day.deleted_at.is_(None)
        ).order_by(Day.seq).all()
        
        return DayList(
            days=[DaySchema.model_validate(day) for day in days],
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
        date=day_data.date,
        status=day_data.status,
        rest_day=day_data.rest_day,
        notes=day_data.notes
    )
    
    db.add(day)
    db.commit()
    db.refresh(day)
    
    return DaySchema.model_validate(day)


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
    
    return DaySchema.model_validate(day)


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
    
    return DaySchema.model_validate(day)


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
