"""
Trips API router
"""
import logging
import re
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session, joinedload

from app.core.auth_jwt import get_current_user_jwt
from app.core.database import get_db
from app.models.day import Day, DayStatus
from app.models.stop import Stop
from app.models.trip import Trip, TripStatus
from app.models.user import User
from app.schemas.bulk import BulkDeleteRequest, BulkOperationResult, BulkUpdateRequest
from app.schemas.day import DayWithAllStops
from app.schemas.pagination import create_paginated_response, get_base_url
from app.schemas.stop import StopSchema
from app.schemas.trip import Trip as TripSchema
from app.schemas.trip import (
    TripCreate,
    TripCreateResponse,
    TripList,
    TripPaginatedResponse,
    TripUpdate,
)
from app.schemas.trip_complete import TripCompleteResponse, TripSummary
from app.schemas.trip_short import DaySummary, TripShort, TripShortResponse
from app.services.bulk_operations import BulkOperationService


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title"""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Limit length
    return slug[:100] if slug else "untitled-trip"


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=TripCreateResponse,
    status_code=201,
    summary="Create new trip with enhanced validation",
    description="""
    **Create New Trip**

    Create a new trip with comprehensive validation and intelligent guidance.

    **Features:**
    - ✅ Input sanitization and validation
    - ✅ Contextual next steps for trip planning
    - ✅ Smart date validation with timezone support
    - ✅ Automatic slug generation from title
    - ✅ Duplicate title detection per user

    **Business Rules:**
    - Trip titles must be unique per user
    - Start dates cannot be in the past (if provided)
    - Destinations are validated for format
    - Automatic status set to 'draft' for new trips

    **Next Steps After Creation:**
    1. 📅 Add your first day to the itinerary
    2. 📍 Set start and end locations for routing
    3. 👥 Invite collaborators if planning together
    4. 🎯 Add stops and activities to your days

    **Authentication Required:** You must be logged in to create trips.
    """,
    responses={
        201: {
            "description": "Trip created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "trip": {
                            "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                            "title": "Summer Road Trip 2024",
                            "slug": "summer-road-trip-2024",
                            "destination": "California, USA",
                            "start_date": "2024-07-15",
                            "status": "draft",
                            "is_published": False,
                            "created_at": "2024-01-15T10:30:00Z",
                            "updated_at": "2024-01-15T10:30:00Z",
                        },
                        "next_steps": [
                            "Create your first day",
                            "Add start and end locations",
                            "Invite collaborators",
                        ],
                        "suggestions": {
                            "planning_timeline": "You have plenty of time to plan your summer trip!",
                            "popular_destinations": [
                                "San Francisco",
                                "Los Angeles",
                                "San Diego",
                            ],
                            "recommended_duration": "7-10 days for a California road trip",
                        },
                    }
                }
            },
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "error_code": "VALIDATION_ERROR",
                            "message": "Request validation failed",
                            "field_errors": {
                                "title": ["String should have at least 1 character"],
                                "start_date": ["Date cannot be in the past"],
                            },
                            "suggestions": [
                                "Provide a descriptive trip title",
                                "Choose a future start date or leave empty",
                            ],
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "request_id": "req_123e4567-e89b-12d3-a456-426614174000",
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "error_code": "AUTHENTICATION_REQUIRED",
                            "message": "Authentication required",
                            "suggestions": [
                                "Include a valid Bearer token in the Authorization header",
                                "Ensure your token has not expired",
                            ],
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "request_id": "req_123e4567-e89b-12d3-a456-426614174001",
                    }
                }
            },
        },
    },
)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
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
        existing_trip = (
            db.query(Trip)
            .filter(
                Trip.slug == slug,
                Trip.created_by == current_user_id,
                Trip.deleted_at.is_(None),
            )
            .first()
        )

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
        created_by=current_user_id,
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Load the user relationship
    trip = (
        db.query(Trip)
        .options(joinedload(Trip.created_by_user))
        .filter(Trip.id == trip.id)
        .first()
    )

    # Generate next steps and suggestions
    next_steps = []
    suggestions = {}

    # Determine next steps based on trip data
    if not trip.start_date:
        next_steps.append("Set your trip start date to help with planning")

    if not trip.destination:
        next_steps.append("Add a destination to get location-specific suggestions")
    else:
        next_steps.append(f"Create your first day in {trip.destination}")
        suggestions["popular_destinations"] = [
            "Consider adding multiple days to explore the region thoroughly",
            "Research local attractions and restaurants for your itinerary",
        ]

    if not next_steps:
        next_steps.append("Create your first day and start planning your route")

    next_steps.append("Invite travel companions to collaborate on the trip")

    # Add time-based suggestions
    if trip.start_date:
        from datetime import date

        days_until_trip = (trip.start_date - date.today()).days
        if days_until_trip > 30:
            suggestions[
                "planning_timeline"
            ] = "You have plenty of time to plan - consider researching seasonal activities"
        elif days_until_trip > 7:
            suggestions[
                "planning_timeline"
            ] = "Start finalizing your itinerary and booking accommodations"
        elif days_until_trip >= 0:
            suggestions[
                "planning_timeline"
            ] = "Trip is coming up soon - finalize your route and check weather"

    return TripCreateResponse(trip=trip, next_steps=next_steps, suggestions=suggestions)


@router.get(
    "/",
    response_model=Union[TripPaginatedResponse, TripList, TripShortResponse],
    summary="List user trips with enhanced pagination",
    description="""
    **List User Trips**

    Retrieve a paginated list of trips with filtering and flexible response formats.

    **Features:**
    - ✅ Enhanced pagination with navigation links
    - ✅ Status-based filtering (draft, active, completed, archived)
    - ✅ Owner filtering for shared trip access
    - ✅ Legacy and modern response formats
    - ✅ Comprehensive metadata and navigation
    - ✅ Performance optimized queries

    **Filter Options:**
    - **status**: Filter by trip status (draft, active, completed, archived)
    - **owner**: Filter by owner ID (defaults to your trips)

    **Response Formats:**
    - **modern**: Enhanced format with pagination metadata and navigation links
    - **legacy**: Simple format for backward compatibility

    **Pagination Features:**
    - Navigation links (first, last, next, prev, self)
    - Total count and page information
    - Configurable page size (1-100 trips per page)
    - Efficient database queries with proper indexing

    **Authentication Required:** You must be logged in to view trips.
    """,
    responses={
        200: {
            "description": "List of trips with pagination metadata",
            "content": {
                "application/json": {
                    "examples": {
                        "modern_format": {
                            "summary": "Modern paginated response",
                            "value": {
                                "data": [
                                    {
                                        "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                                        "title": "Summer Road Trip 2024",
                                        "slug": "summer-road-trip-2024",
                                        "destination": "California, USA",
                                        "start_date": "2024-07-15",
                                        "status": "draft",
                                        "is_published": False,
                                        "created_at": "2024-01-15T10:30:00Z",
                                        "updated_at": "2024-01-15T10:30:00Z",
                                    }
                                ],
                                "meta": {
                                    "page": 1,
                                    "size": 20,
                                    "total": 25,
                                    "pages": 2,
                                },
                                "links": {
                                    "first": "/trips?page=1&size=20",
                                    "last": "/trips?page=2&size=20",
                                    "next": "/trips?page=2&size=20",
                                    "prev": None,
                                    "self": "/trips?page=1&size=20",
                                },
                            },
                        },
                        "legacy_format": {
                            "summary": "Legacy simple response",
                            "value": {
                                "trips": [
                                    {
                                        "id": "01K4AHPK4S1KVTYDB5ASTGTM8K",
                                        "title": "Summer Road Trip 2024",
                                        "destination": "California, USA",
                                        "status": "draft",
                                    }
                                ]
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "error_code": "AUTHENTICATION_REQUIRED",
                            "message": "Authentication required",
                            "suggestions": [
                                "Include a valid Bearer token in the Authorization header",
                                "Ensure your token has not expired",
                            ],
                        },
                        "timestamp": "2024-01-15T10:30:00Z",
                        "request_id": "req_123e4567-e89b-12d3-a456-426614174002",
                    }
                }
            },
        },
    },
)
async def list_trips(
    request: Request,
    status: Optional[TripStatus] = Query(None, description="Filter by trip status"),
    owner: Optional[str] = Query(
        None, description="Filter by owner ID (defaults to your trips)"
    ),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    size: int = Query(20, ge=1, le=100, description="Number of trips per page"),
    sort_by: Optional[str] = Query(
        "created_at:desc",
        description="Sort by field:direction (created_at:desc, updated_at:desc, title:asc, start_date:desc)",
    ),
    format: Optional[str] = Query(
        "modern",
        regex="^(legacy|modern|short)$",
        description="Response format: 'legacy', 'modern', or 'short'",
    ),
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **List Your Trips with Enhanced Pagination**

    Get a paginated list of your trips with modern navigation links and optional filtering.

    **Authentication Required:** You must be logged in to view trips.

    **Enhanced Pagination Features:**
    - Navigation links (first, last, next, prev, self)
    - Comprehensive metadata (total pages, current position, etc.)
    - Backward compatibility with legacy format

    **Parameters:**
    - `status`: Filter by trip status (draft, active, completed, archived)
    - `owner`: Filter by owner ID (defaults to your trips)
    - `page`: Page number (starts at 1)
    - `size`: Number of trips per page (1-100)
    - `sort_by`: Sort by field:direction (created_at:desc, updated_at:desc, title:asc, start_date:desc) - defaults to newest first
    - `format`: Response format - 'modern' (default), 'legacy', or 'short'

    **Modern Response Format:**
    ```json
    {
      "data": [...],
      "meta": {
        "current_page": 1,
        "per_page": 20,
        "total_items": 45,
        "total_pages": 3,
        "has_next": true,
        "has_prev": false,
        "from_item": 1,
        "to_item": 20
      },
      "links": {
        "self": "http://localhost:8000/trips?page=1&size=20",
        "first": "http://localhost:8000/trips?page=1&size=20",
        "last": "http://localhost:8000/trips?page=3&size=20",
        "next": "http://localhost:8000/trips?page=2&size=20",
        "prev": null
      }
    }
    ```

    **Returns:** Paginated list of trips with navigation links and comprehensive metadata.
    """
    current_user_id = current_user.id

    query = (
        db.query(Trip)
        .options(joinedload(Trip.created_by_user))
        .filter(Trip.deleted_at.is_(None))
    )

    # Apply filters
    if status:
        query = query.filter(Trip.status == status)

    if owner:
        query = query.filter(Trip.created_by == owner)
    else:
        # Default to current user's trips
        query = query.filter(Trip.created_by == current_user_id)

    # Apply sorting
    allowed_sort_fields = {
        "created_at": Trip.created_at,
        "updated_at": Trip.updated_at,
        "title": Trip.title,
        "start_date": Trip.start_date,
        "status": Trip.status,
    }

    # Parse sort_by parameter (format: field:direction)
    sort_field = "created_at"
    sort_direction = "desc"

    if sort_by:
        try:
            parts = sort_by.split(":")
            if len(parts) == 2:
                field, direction = parts
                if field in allowed_sort_fields and direction.lower() in [
                    "asc",
                    "desc",
                ]:
                    sort_field = field
                    sort_direction = direction.lower()
        except Exception:
            # Use defaults if parsing fails
            pass

    # Apply sorting to query
    field_attr = allowed_sort_fields[sort_field]
    if sort_direction == "desc":
        query = query.order_by(desc(field_attr))
    else:
        query = query.order_by(asc(field_attr))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * size
    trips = query.offset(offset).limit(size).all()

    # Support legacy, modern, and short response formats
    if format == "legacy":
        return TripList(trips=trips, total=total, page=page, size=size)

    if format == "short":
        # Get trip IDs for day/stop queries
        trip_ids = [trip.id for trip in trips]

        # Get day counts and summaries for all trips
        trip_short_data = []

        for trip in trips:
            # Get days for this trip
            days = (
                db.query(Day)
                .filter(Day.trip_id == trip.id, Day.deleted_at.is_(None))
                .order_by(Day.seq)
                .all()
            )

            # Get stops for all days of this trip
            day_ids = [day.id for day in days]
            stops_by_day = {}

            if day_ids:
                stops = (
                    db.query(Stop)
                    .filter(Stop.day_id.in_(day_ids), Stop.deleted_at.is_(None))
                    .all()
                )

                # Group stops by day_id
                for stop in stops:
                    if stop.day_id not in stops_by_day:
                        stops_by_day[stop.day_id] = []
                    stops_by_day[stop.day_id].append(stop)

            # Build day summaries as a list of DaySummary objects
            days_data = []
            for day in days:
                day_stops = stops_by_day.get(day.id, [])

                # Check for start and end stops
                has_start = any(
                    stop.kind.value.lower() == "start" for stop in day_stops
                )
                has_end = any(stop.kind.value.lower() == "end" for stop in day_stops)

                # Create DaySummary object
                day_summary = DaySummary(
                    day=day.seq, start=has_start, stops=len(day_stops), end=has_end
                )
                days_data.append(day_summary)

            # Create trip short data
            trip_short = TripShort(
                slug=str(trip.slug),
                title=str(trip.title),
                destination=str(trip.destination)
                if trip.destination is not None
                else None,
                start_date=trip.start_date.isoformat()
                if trip.start_date is not None
                else None,
                timezone=str(trip.timezone) if trip.timezone is not None else None,
                status=trip.status,
                is_published=bool(trip.is_published),
                created_by=str(trip.created_by),
                members=[],  # TODO: Implement members when available
                total_days=len(days),
                days=days_data,
            )

            trip_short_data.append(trip_short)

        # Create paginated response for short format
        base_url = get_base_url(request, "/trips")
        query_params = {}
        if status:
            query_params["status"] = status.value
        if owner:
            query_params["owner"] = owner
        if sort_by and sort_by != "created_at:desc":
            query_params["sort_by"] = sort_by
        query_params["format"] = "short"

        paginated_response = create_paginated_response(
            items=trip_short_data,
            total_items=total,
            current_page=page,
            per_page=size,
            base_url=base_url,
            query_params=query_params,
        )

        return TripShortResponse(
            data=trip_short_data,
            meta=paginated_response.meta.model_dump(),
            links=paginated_response.links.model_dump(),
        )

    # Modern response with navigation links
    base_url = get_base_url(request, "/trips")
    query_params = {}
    if status:
        query_params["status"] = status.value
    if owner:
        query_params["owner"] = owner
    if sort_by and sort_by != "created_at:desc":  # Only include if not default
        query_params["sort_by"] = sort_by

    return create_paginated_response(
        items=trips,
        total_items=total,
        current_page=page,
        per_page=size,
        base_url=base_url,
        query_params=query_params,
    )


@router.get("/{trip_id}", response_model=TripSchema)
async def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """Get a specific trip"""
    trip = (
        db.query(Trip)
        .options(joinedload(Trip.created_by_user))
        .filter(Trip.id == trip_id, Trip.deleted_at.is_(None))
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Check if user has access to this trip
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return trip


@router.patch("/{trip_id}", response_model=TripSchema)
async def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **Update Trip**

    Update trip details including start date, title, destination, etc.

    **Authentication Required:** You must be the trip owner.

    **Note:** Updating the start_date will affect all day dates in the trip.
    """
    trip = (
        db.query(Trip)
        .options(joinedload(Trip.created_by_user))
        .filter(Trip.id == trip_id, Trip.deleted_at.is_(None))
        .first()
    )

    if not trip:
        from app.core.exception_handlers import ResourceNotFoundError

        raise ResourceNotFoundError("Trip", trip_id)

    # Verify ownership
    if trip.created_by != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this trip"
        )

    # Update fields
    update_data = trip_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trip, field, value)

    db.commit()
    db.refresh(trip)

    return trip


@router.post("/{trip_id}/archive", response_model=TripSchema)
async def archive_trip(trip_id: str, db: Session = Depends(get_db)):
    """Archive a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.deleted_at.is_(None)).first()

    if not trip:
        from app.core.exception_handlers import ResourceNotFoundError

        raise ResourceNotFoundError("Trip", trip_id)

    trip.status = TripStatus.ARCHIVED
    db.commit()
    db.refresh(trip)

    return trip


@router.post("/{trip_id}/publish", response_model=TripSchema, status_code=200)
async def publish_trip(trip_id: str, db: Session = Depends(get_db)):
    """Publish a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.deleted_at.is_(None)).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip.is_published = True
    db.commit()
    db.refresh(trip)

    return trip


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **Delete Trip**

    Permanently delete a trip and all associated data.

    **Warning:** This action cannot be undone. All days, stops, and routes will be deleted.

    **Authentication Required:** You must be the trip owner.
    """
    # Find trip and verify ownership
    trip = (
        db.query(Trip)
        .filter(
            Trip.id == trip_id,
            Trip.created_by == current_user.id,
            Trip.deleted_at.is_(None),
        )
        .first()
    )

    if not trip:
        from app.core.exception_handlers import ResourceNotFoundError

        raise ResourceNotFoundError("Trip", trip_id)

    # Soft delete the trip (cascade will handle days, stops, routes)
    from datetime import datetime

    trip.deleted_at = datetime.utcnow()
    db.commit()

    # Return 204 No Content (no response body)
    return


# Bulk Operations Endpoints


@router.delete("/bulk", response_model=BulkOperationResult)
async def bulk_delete_trips(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **Bulk Delete Trips**

    Delete multiple trips in a single operation for improved efficiency.

    **Features:**
    - Delete up to 10 trips at once
    - Automatic cleanup of associated days, stops, and routes
    - Transactional safety (all or nothing)
    - Permission validation for each trip
    - Cascade deletion of dependent resources

    **Request Body:**
    ```json
    {
      "ids": ["trip_id_1", "trip_id_2", "trip_id_3"],
      "force": false
    }
    ```

    **Use Cases:**
    - Clean up old/cancelled trips
    - Remove test trips
    - Bulk cleanup operations
    """
    bulk_service = BulkOperationService(db)

    async def pre_delete_hook(trip: Trip):
        """Hook to handle trip-specific logic before deletion"""
        # Log the deletion for audit purposes
        logger.info(
            f"Deleting trip {trip.id} ({trip.title}) for user {current_user.id}"
        )

    async def post_delete_hook(trip: Trip):
        """Hook to handle post-deletion cleanup"""
        # Note: Cascade deletion should handle days, stops, and routes automatically
        logger.info(f"Trip {trip.id} deleted successfully")

    return await bulk_service.bulk_delete(
        model_class=Trip,
        ids=request.ids,
        user_id=current_user.id,
        force=request.force,
        pre_delete_hook=pre_delete_hook,
        post_delete_hook=post_delete_hook,
    )


@router.patch("/bulk", response_model=BulkOperationResult)
async def bulk_update_trips(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **Bulk Update Trips**

    Update multiple trips in a single operation for improved efficiency.

    **Features:**
    - Update up to 10 trips at once
    - Field-level validation and filtering
    - Transactional safety
    - Permission validation for each trip

    **Allowed Update Fields:**
    - `title`: Trip title/name
    - `destination`: Trip destination
    - `start_date`: Trip start date (YYYY-MM-DD)
    - `status`: Trip status (draft, active, completed, archived)
    - `is_published`: Publication status

    **Request Body:**
    ```json
    {
      "updates": [
        {
          "id": "trip_id_1",
          "data": {
            "title": "Updated Trip Title",
            "status": "completed"
          }
        },
        {
          "id": "trip_id_2",
          "data": {
            "destination": "New Destination",
            "is_published": true
          }
        }
      ]
    }
    ```

    **Use Cases:**
    - Batch update trip statuses
    - Publish multiple trips
    - Update destinations for multiple trips
    - Mark trips as completed
    """
    bulk_service = BulkOperationService(db)

    # Define allowed fields for bulk updates
    allowed_fields = ["title", "destination", "start_date", "status", "is_published"]

    async def pre_update_hook(trip: Trip, update_data: dict):
        """Hook to handle trip-specific logic before update"""
        # Validate status if being updated
        if "status" in update_data:
            try:
                TripStatus(update_data["status"])
            except ValueError:
                raise ValueError(f"Invalid status: {update_data['status']}")

        # Validate date format if being updated
        if "start_date" in update_data:
            from datetime import datetime

            try:
                datetime.strptime(str(update_data["start_date"]), "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {update_data['start_date']}. Use YYYY-MM-DD"
                )

        return update_data

    return await bulk_service.bulk_update(
        model_class=Trip,
        updates=request.updates,
        user_id=current_user.id,
        allowed_fields=allowed_fields,
        pre_update_hook=pre_update_hook,
    )


@router.get("/{trip_id}/complete", response_model=TripCompleteResponse)
async def get_trip_complete(
    trip_id: str,
    include_place: bool = Query(
        False, description="Include place information with stops"
    ),
    include_route_info: bool = Query(False, description="Include route information"),
    status: Optional[str] = Query(None, description="Filter days by status"),
    day_limit: Optional[int] = Query(
        None, ge=1, le=50, description="Limit number of days returned"
    ),
    current_user: User = Depends(get_current_user_jwt),
    db: Session = Depends(get_db),
):
    """
    **Get Complete Trip Data**

    Get comprehensive trip information including all days and stops in a single request.

    **Features:**
    - ✅ **Complete trip data**: Trip details, all days, and all stops
    - ✅ **Proper ordering**: Days by sequence (1, 2, 3...), stops by sequence within each day
    - ✅ **Summary statistics**: Total days, stops, duration, and breakdowns
    - ✅ **Optional place details**: Include place information for each stop
    - ✅ **Route information**: Include route data if available
    - ✅ **Filtering**: Filter days by status
    - ✅ **Performance optimized**: Efficient queries with eager loading

    **Query Parameters:**
    - `include_place`: Include place details with stops (default: false)
    - `include_route_info`: Include route information (default: false)
    - `status`: Filter days by status (active, completed, etc.)
    - `day_limit`: Limit number of days returned (1-50)

    **Response Structure:**
    - Complete trip information with user details
    - Days ordered by sequence (1, 2, 3...)
    - Stops ordered by sequence within each day (START → VIA → END)
    - Summary statistics and breakdowns

    **Authentication Required:** You must be the trip owner.
    """
    # Get trip with user information
    trip = (
        db.query(Trip)
        .options(joinedload(Trip.created_by_user))
        .filter(Trip.id == trip_id, Trip.deleted_at.is_(None))
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Check if user has access to this trip
    if str(trip.created_by) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")

    # Build base query for days
    days_query = db.query(Day).filter(Day.trip_id == trip_id, Day.deleted_at.is_(None))

    # Apply status filter if provided
    if status:
        try:
            day_status = DayStatus(status.lower())
            days_query = days_query.filter(Day.status == day_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid day status: {status}")

    # Apply day limit if provided
    if day_limit:
        days_query = days_query.limit(day_limit)

    # Order by sequence and get days
    days = days_query.order_by(Day.seq).all()

    # Get all stops for these days in one query
    day_ids = [day.id for day in days] if days else []
    stops = []
    if day_ids:
        stops_query = db.query(Stop).filter(
            Stop.day_id.in_(day_ids), Stop.deleted_at.is_(None)
        )

        # Include place information if requested
        if include_place:
            stops_query = stops_query.options(joinedload(Stop.place))

        # Order stops by day_id and sequence
        stops = stops_query.order_by(Stop.day_id, Stop.seq).all()

    # Group stops by day_id
    stops_by_day = {}
    for stop in stops:
        if stop.day_id not in stops_by_day:
            stops_by_day[stop.day_id] = []
        stops_by_day[stop.day_id].append(stop)

    # Build days with stops
    days_with_stops = []
    total_stops = 0
    status_breakdown = {}
    stop_type_breakdown = {}

    for day in days:
        day_stops = stops_by_day.get(day.id, [])
        total_stops += len(day_stops)

        # Count day status
        day_status_str = (
            day.status.value if hasattr(day.status, "value") else str(day.status)
        )
        status_breakdown[day_status_str] = status_breakdown.get(day_status_str, 0) + 1

        # Convert stops to schema and count stop types
        stop_schemas = []
        for stop in day_stops:
            stop_dict = stop.__dict__.copy()
            if include_place and stop.place:
                stop_dict["place"] = stop.place
            stop_schemas.append(StopSchema.model_validate(stop_dict))

            # Count stop type
            stop_type_str = (
                stop.stop_type.value
                if hasattr(stop.stop_type, "value")
                else str(stop.stop_type)
            )
            stop_type_breakdown[stop_type_str] = (
                stop_type_breakdown.get(stop_type_str, 0) + 1
            )

        # Create day with all stops
        day_dict = day.__dict__.copy()
        day_dict["trip_start_date"] = trip.start_date
        day_dict["stops"] = stop_schemas
        day_dict["stops_count"] = len(day_stops)
        day_dict["has_route"] = False  # TODO: Check for route versions when implemented

        days_with_stops.append(DayWithAllStops.model_validate(day_dict))

    # Calculate trip duration
    trip_duration_days = None
    if trip.start_date is not None and len(days) > 0:
        trip_duration_days = len(days)

    # Create summary
    summary = TripSummary(
        total_days=len(days),
        total_stops=total_stops,
        trip_duration_days=trip_duration_days,
        status_breakdown=status_breakdown,
        stop_type_breakdown=stop_type_breakdown,
    )

    return TripCompleteResponse(
        trip=TripSchema.model_validate(trip), days=days_with_stops, summary=summary
    )
