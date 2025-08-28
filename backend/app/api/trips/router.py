"""
Trips API router
"""
from typing import List, Optional
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trip import Trip, TripStatus
from app.schemas.trip import (
    TripCreate, TripUpdate, Trip as TripSchema, TripList
)


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Limit length
    return slug[:100] if slug else 'untitled-trip'

router = APIRouter()


@router.post("/", response_model=TripSchema)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Create a New Trip**

    Create a new road trip with the provided details.

    **Authentication Required:** You must be logged in to create trips.

    **Note:** The trip slug is auto-generated from the title and must be unique among your trips.
    """
    current_user_id = current_user.id

    # Generate slug from title
    base_slug = generate_slug(trip_data.title)
    slug = base_slug
    counter = 1

    # Ensure slug is unique for this user
    while True:
        existing_trip = db.query(Trip).filter(
            Trip.slug == slug,
            Trip.created_by == current_user_id,
            Trip.deleted_at.is_(None)
        ).first()

        if not existing_trip:
            break

        # If slug exists, append a number
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create trip
    trip = Trip(
        slug=slug,
        title=trip_data.title,
        destination=trip_data.destination,
        start_date=trip_data.start_date,
        timezone=trip_data.timezone,
        status=trip_data.status,
        is_published=trip_data.is_published,
        created_by=current_user_id
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Load the user relationship
    trip = db.query(Trip).options(joinedload(Trip.created_by_user)).filter(Trip.id == trip.id).first()

    return trip


@router.get("/", response_model=TripList)
async def list_trips(
    status: Optional[TripStatus] = Query(None),
    owner: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **List Your Trips**

    Get a paginated list of your trips with optional filtering.

    **Authentication Required:** You must be logged in to view trips.

    **Parameters:**
    - `status`: Filter by trip status (draft, active, completed, archived)
    - `owner`: Filter by owner ID (defaults to your trips)
    - `page`: Page number (starts at 1)
    - `size`: Number of trips per page (1-100)

    **Returns:** Paginated list of trips with metadata.
    """
    current_user_id = current_user.id

    query = db.query(Trip).options(joinedload(Trip.created_by_user)).filter(Trip.deleted_at.is_(None))

    # Apply filters
    if status:
        query = query.filter(Trip.status == status)

    if owner:
        query = query.filter(Trip.created_by == owner)
    else:
        # Default to current user's trips
        query = query.filter(Trip.created_by == current_user_id)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * size
    trips = query.offset(offset).limit(size).all()

    return TripList(
        trips=trips,
        total=total,
        page=page,
        size=size
    )


@router.get("/{trip_id}", response_model=TripSchema)
async def get_trip(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific trip"""
    trip = db.query(Trip).options(joinedload(Trip.created_by_user)).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@router.patch("/{trip_id}", response_model=TripSchema)
async def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Update Trip**

    Update trip details including start date, title, destination, etc.

    **Authentication Required:** You must be the trip owner.

    **Note:** Updating the start_date will affect all day dates in the trip.
    """
    trip = db.query(Trip).options(joinedload(Trip.created_by_user)).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Verify ownership
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this trip")

    # Update fields
    update_data = trip_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)

    db.commit()
    db.refresh(trip)

    return trip


@router.post("/{trip_id}/archive", response_model=TripSchema)
async def archive_trip(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Archive a trip"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.status = TripStatus.ARCHIVED
    db.commit()
    db.refresh(trip)

    return trip


@router.post("/{trip_id}/publish", response_model=TripSchema)
async def publish_trip(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Publish a trip"""
    trip = db.query(Trip).filter(
        Trip.id == trip_id,
        Trip.deleted_at.is_(None)
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.is_published = True
    db.commit()
    db.refresh(trip)

    return trip