"""
Days API router
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.day import Day, DayStatus
from app.models.route import RouteVersion
from app.models.stop import Stop, StopKind
from app.models.trip import Trip
from app.models.user import User
from app.schemas.bulk import (
    BulkDeleteRequest,
    BulkOperationResult,
    BulkUpdateRequest,
)
from app.schemas.day import Day as DaySchema
from app.schemas.day import (
    DayCreate,
    DayList,
    DayListSummary,
    DayListWithStops,
    DayLocations,
    DaysCompleteResponse,
    DayUpdate,
    DayWithAllStops,
    DayWithStops,
)
from app.schemas.place import PlaceSchema
from app.schemas.stop import Stop as StopSchema
from app.services.bulk_operations import BulkOperationService
from app.services.filtering import FilterCondition, FilteringService, SortCondition

router = APIRouter()
logger = logging.getLogger(__name__)


def get_trip_and_verify_access(trip_id: str, current_user: User, db: Session) -> Trip:
    """Get trip and verify user has access to it"""
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
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@router.get("", response_model=DayList)
async def list_days(
    trip_id: str,
    include_stops: bool = Query(
        False, description="Include stops count and route info"
    ),
    # Enhanced filtering and sorting
    filter_string: Optional[str] = Query(
        None, description="Advanced filters: field:operator:value"
    ),
    sort_string: Optional[str] = Query(
        None, description="Sort: field:direction,field2:direction2"
    ),
    status: Optional[str] = Query(None, description="Filter by day status"),
    date_from: Optional[date] = Query(None, description="Filter days from this date"),
    date_to: Optional[date] = Query(None, description="Filter days until this date"),
    search: Optional[str] = Query(None, description="Search in day titles"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Enhanced List Days in Trip**

    Get all days for a specific trip with advanced filtering and sorting capabilities.

    **Enhanced Features:**
    - ✅ **Multi-attribute filtering**: Filter by status, date range, title, etc.
    - ✅ **Flexible sorting**: Sort by date, sequence, title, status, etc.
    - ✅ **Search functionality**: Search across day titles
    - ✅ **Date range filters**: Filter by date range
    - ✅ **String-based filters**: Advanced filter syntax

    **Filter Examples:**
    - `filter_string=status:eq:completed,date:gte:2024-01-01`
    - `sort_string=date:asc,title:asc`
    - `search=jerusalem` (searches day titles)
    - `date_from=2024-01-01&date_to=2024-12-31` (date range)

    **Supported Filter Fields:**
    - `date`, `title`, `status`, `seq`, `created_at`, `updated_at`

    **Supported Sort Fields:**
    - `date`, `seq`, `title`, `status`, `created_at`, `updated_at`

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Initialize filtering service
    filtering_service = FilteringService()

    # Build base query
    base_query = db.query(Day).filter(Day.trip_id == trip_id, Day.deleted_at.is_(None))

    # Enhanced filtering
    filter_conditions = []

    # Parse filter string
    if filter_string:
        filter_conditions.extend(filtering_service.parse_filter_string(filter_string))

    # Legacy status filter (for backward compatibility)
    if status:
        filter_conditions.append(FilterCondition("status", "eq", status))

    # Date range filters
    if date_from:
        filter_conditions.append(FilterCondition("date", "gte", date_from))
    if date_to:
        filter_conditions.append(FilterCondition("date", "lte", date_to))

    # Search functionality
    if search:
        base_query = base_query.filter(Day.title.ilike(f"%{search}%"))

    # Apply advanced filters
    allowed_filter_fields = [
        "date",
        "title",
        "status",
        "seq",
        "created_at",
        "updated_at",
    ]
    base_query = filtering_service.apply_filters(
        base_query, Day, filter_conditions, allowed_filter_fields
    )

    # Enhanced sorting
    sort_conditions = []
    if sort_string:
        sort_conditions = filtering_service.parse_sort_string(sort_string)

    # Apply sorting with default fallback
    allowed_sort_fields = ["date", "seq", "title", "status", "created_at", "updated_at"]
    default_sort = SortCondition("seq", "asc")
    base_query = filtering_service.apply_sorting(
        base_query, Day, sort_conditions, allowed_sort_fields, default_sort
    )

    if include_stops:
        # Query with stops count and route info
        days_query = (
            base_query.add_columns(func.count(Stop.id).label("stops_count"))
            .outerjoin(Stop)
            .group_by(Day.id)
        )

        days_with_counts = days_query.all()

        days_list = []
        for day, stops_count in days_with_counts:
            day_dict = {
                **day.__dict__,
                "stops_count": stops_count,
                "has_route": False,  # TODO: Check for route versions when implemented
                "trip_start_date": trip.start_date,  # Add for calculated_date
            }
            days_list.append(DayWithStops(**day_dict))

        return DayListWithStops(days=days_list, total=len(days_list), trip_id=trip_id)
    else:
        # Simple query without extra info but include trip start_date for calculated_date
        days = base_query.all()

        # Add trip start_date to each day for calculated_date
        days_with_trip_date = []
        for day in days:
            day_dict = day.__dict__.copy()
            day_dict["trip_start_date"] = trip.start_date
            days_with_trip_date.append(DaySchema.model_validate(day_dict))

        return DayList(days=days_with_trip_date, total=len(days), trip_id=trip_id)


@router.get("/summary", response_model=DayListSummary)
async def list_days_with_locations(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List days and include start/end places for each day in a single call.
    Note: This route must appear before the dynamic '/{day_id}' to avoid being captured by it.
    """
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Fetch all days ordered by seq
    days = (
        db.query(Day)
        .filter(Day.trip_id == trip_id, Day.deleted_at.is_(None))
        .order_by(Day.seq)
        .all()
    )
    day_by_seq = {d.seq: d for d in days}

    # Fetch START/END stops for all days in one query, eager-loading place
    if days:
        stops = (
            db.query(Stop)
            .options(joinedload(Stop.place))
            .filter(
                Stop.trip_id == trip_id,
                Stop.day_id.in_([d.id for d in days]),
                Stop.kind.in_([StopKind.START, StopKind.VIA, StopKind.END]),
            )
            .order_by(Stop.day_id, Stop.seq)
            .all()
        )
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
        if str(s.kind).lower().endswith("start"):
            loc.start = place_obj
        elif str(s.kind).lower().endswith("end"):
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
                coords = (
                    rv.geojson.get("coordinates")
                    if isinstance(rv.geojson, dict)
                    else None
                )
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
        dd["trip_start_date"] = trip.start_date
        days_with_trip_date.append(DaySchema.model_validate(dd))

    return DayListSummary(
        days=days_with_trip_date,
        locations=list(locs_map.values()),
        total=len(days),
        trip_id=trip_id,
    )


@router.post("", response_model=DaySchema, status_code=201)
async def create_day(
    trip_id: str,
    day_data: DayCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        max_seq = (
            db.query(func.max(Day.seq))
            .filter(Day.trip_id == trip_id, Day.deleted_at.is_(None))
            .scalar()
            or 0
        )
        seq = max_seq + 1
    else:
        seq = day_data.seq

        # Check if sequence number already exists
        existing_day = (
            db.query(Day)
            .filter(Day.trip_id == trip_id, Day.seq == seq, Day.deleted_at.is_(None))
            .first()
        )

        if existing_day:
            raise HTTPException(
                status_code=400, detail=f"Day with sequence number {seq} already exists"
            )

    # Create day
    day = Day(
        trip_id=trip_id,
        seq=seq,
        status=day_data.status,
        rest_day=day_data.rest_day,
        notes=day_data.notes,
    )

    db.add(day)
    db.commit()
    db.refresh(day)

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict["trip_start_date"] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.get("/{day_id}", response_model=DaySchema)
async def get_day(
    trip_id: str,
    day_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Get Specific Day**

    Get details for a specific day in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Get day
    day = (
        db.query(Day)
        .filter(Day.id == day_id, Day.trip_id == trip_id, Day.deleted_at.is_(None))
        .first()
    )

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict["trip_start_date"] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.patch("/{day_id}", response_model=DaySchema)
async def update_day(
    trip_id: str,
    day_id: str,
    day_data: DayUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Update Day**

    Update details for a specific day in the trip.

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

    # Get day
    day = (
        db.query(Day)
        .filter(Day.id == day_id, Day.trip_id == trip_id, Day.deleted_at.is_(None))
        .first()
    )

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Check sequence number conflicts if updating seq
    if day_data.seq is not None and day_data.seq != day.seq:
        existing_day = (
            db.query(Day)
            .filter(
                Day.trip_id == trip_id,
                Day.seq == day_data.seq,
                Day.deleted_at.is_(None),
                Day.id != day_id,
            )
            .first()
        )

        if existing_day:
            raise HTTPException(
                status_code=400,
                detail=f"Day with sequence number {day_data.seq} already exists",
            )

    # Update fields
    update_data = day_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(day, field, value)

    db.commit()
    db.refresh(day)

    # Add trip start_date for calculated_date
    day_dict = day.__dict__.copy()
    day_dict["trip_start_date"] = trip.start_date

    return DaySchema.model_validate(day_dict)


@router.delete("/{day_id}", status_code=204)
async def delete_day(
    trip_id: str,
    day_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
    day = (
        db.query(Day)
        .filter(Day.id == day_id, Day.trip_id == trip_id, Day.deleted_at.is_(None))
        .first()
    )

    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Soft delete the day (this will cascade to stops and routes via application logic)
    day.soft_delete()

    # TODO: Also soft delete associated stops and route versions
    # This should be handled by the soft delete cascade logic

    db.commit()

    # Return 204 No Content (no response body)
    return


# Bulk Operations Endpoints


@router.delete("/bulk", response_model=BulkOperationResult)
async def bulk_delete_days(
    trip_id: str,
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Bulk Delete Days**

    Delete multiple days from a trip in a single operation.

    **Features:**
    - Delete up to 20 days at once
    - Automatic cleanup of associated stops and routes
    - Transactional safety (all or nothing)
    - Permission validation for trip ownership
    - Cascade deletion of dependent resources

    **Request Body:**
    ```json
    {
      "ids": ["day_id_1", "day_id_2", "day_id_3"],
      "force": false
    }
    ```

    **Use Cases:**
    - Remove multiple days from itinerary
    - Clear trip and start over
    - Remove cancelled days
    """
    # Validate trip exists and user has access
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id, Trip.created_by == current_user.id)
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or access denied")

    bulk_service = BulkOperationService(db)

    async def pre_delete_hook(day: Day):
        """Hook to handle day-specific logic before deletion"""
        # Validate day belongs to the specified trip
        if day.trip_id != trip_id:
            raise ValueError(f"Day {day.id} does not belong to trip {trip_id}")

        # Log the deletion for audit purposes
        logger.info(f"Deleting day {day.id} from trip {trip_id}")

    async def post_delete_hook(day: Day):
        """Hook to handle post-deletion cleanup"""
        # Note: Cascade deletion should handle stops and routes automatically
        # This is just for logging/audit purposes
        logger.info(f"Day {day.id} deleted successfully")

    return await bulk_service.bulk_delete(
        model_class=Day,
        ids=request.ids,
        user_id=current_user.id,
        force=request.force,
        pre_delete_hook=pre_delete_hook,
        post_delete_hook=post_delete_hook,
    )


@router.patch("/bulk", response_model=BulkOperationResult)
async def bulk_update_days(
    trip_id: str,
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Bulk Update Days**

    Update multiple days in a trip in a single operation.

    **Features:**
    - Update up to 20 days at once
    - Field-level validation and filtering
    - Transactional safety
    - Permission validation for trip ownership

    **Allowed Update Fields:**
    - `title`: Day title/name
    - `date`: Day date (YYYY-MM-DD)
    - `status`: Day status (planned, active, completed)
    - `notes`: Day notes/description

    **Request Body:**
    ```json
    {
      "updates": [
        {
          "id": "day_id_1",
          "data": {
            "title": "Updated Day Title",
            "status": "completed"
          }
        },
        {
          "id": "day_id_2",
          "data": {
            "date": "2024-06-16",
            "notes": "Updated notes"
          }
        }
      ]
    }
    ```

    **Use Cases:**
    - Batch update day titles
    - Mark multiple days as completed
    - Update dates for multiple days
    - Add notes to multiple days
    """
    # Validate trip exists and user has access
    trip = (
        db.query(Trip)
        .filter(Trip.id == trip_id, Trip.created_by == current_user.id)
        .first()
    )

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or access denied")

    bulk_service = BulkOperationService(db)

    # Define allowed fields for bulk updates
    allowed_fields = ["title", "date", "status", "notes"]

    async def pre_update_hook(day: Day, update_data: dict):
        """Hook to handle day-specific logic before update"""
        # Validate day belongs to the specified trip
        if day.trip_id != trip_id:
            raise ValueError(f"Day {day.id} does not belong to trip {trip_id}")

        # Validate status if being updated
        if "status" in update_data:
            try:
                DayStatus(update_data["status"])
            except ValueError:
                raise ValueError(f"Invalid status: {update_data['status']}")

        # Validate date format if being updated
        if "date" in update_data:
            from datetime import datetime

            try:
                datetime.strptime(str(update_data["date"]), "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {update_data['date']}. Use YYYY-MM-DD"
                )

        return update_data

    return await bulk_service.bulk_update(
        model_class=Day,
        updates=request.updates,
        user_id=current_user.id,
        allowed_fields=allowed_fields,
        pre_update_hook=pre_update_hook,
    )


@router.get("/complete", response_model=DaysCompleteResponse)
async def list_days_complete(
    trip_id: str,
    include_place: bool = Query(
        False, description="Include place information with stops"
    ),
    include_route_info: bool = Query(False, description="Include route information"),
    status: Optional[str] = Query(None, description="Filter days by status"),
    day_limit: Optional[int] = Query(
        None, ge=1, le=50, description="Limit number of days returned"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Get Complete Days with All Stops**

    Get all days for a trip with complete stops information in a single request.

    **Features:**
    - ✅ **Complete nested structure**: All days with all their stops
    - ✅ **Proper ordering**: Days by sequence (1, 2, 3...), stops by sequence within each day
    - ✅ **Optional place details**: Include place information for each stop
    - ✅ **Route information**: Include route data if available
    - ✅ **Filtering**: Filter days by status
    - ✅ **Performance optimized**: Single query with eager loading

    **Query Parameters:**
    - `include_place`: Include place details with stops (default: false)
    - `include_route_info`: Include route information (default: false)
    - `status`: Filter days by status (active, completed, etc.)
    - `day_limit`: Limit number of days returned (1-50)

    **Response Structure:**
    - Days ordered by sequence (1, 2, 3...)
    - Stops ordered by sequence within each day (START → VIA → END)
    - Complete stop details including place information
    - Summary statistics (total days, total stops)

    **Authentication Required:** You must be the trip owner.
    """
    # Verify trip access
    trip = get_trip_and_verify_access(trip_id, current_user, db)

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

    if not days:
        return DaysCompleteResponse(
            trip_id=trip_id, days=[], total_days=0, total_stops=0
        )

    # Get all stops for these days in one query
    day_ids = [day.id for day in days]
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

    # Build response with days and their stops
    days_with_stops = []
    total_stops = 0

    for day in days:
        day_stops = stops_by_day.get(day.id, [])
        total_stops += len(day_stops)

        # Convert stops to schema
        stop_schemas = []
        for stop in day_stops:
            stop_dict = stop.__dict__.copy()
            if include_place and stop.place:
                stop_dict["place"] = stop.place
            stop_schemas.append(StopSchema.model_validate(stop_dict))

        # Create day with all stops
        day_dict = day.__dict__.copy()
        day_dict["trip_start_date"] = trip.start_date
        day_dict["stops"] = stop_schemas
        day_dict["stops_count"] = len(day_stops)
        day_dict["has_route"] = False  # TODO: Check for route versions when implemented

        days_with_stops.append(DayWithAllStops.model_validate(day_dict))

    return DaysCompleteResponse(
        trip_id=trip_id,
        days=days_with_stops,
        total_days=len(days),
        total_stops=total_stops,
    )
