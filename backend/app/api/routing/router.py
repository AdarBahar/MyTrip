"""
Routing API router
"""
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
import logging
import asyncio

from app.core.database import get_db
from app.models.day import Day
from app.models.stop import Stop, StopKind
from app.models.place import Place
from app.models.route import RouteVersion, RouteLeg as RouteLegModel
from app.models.trip import Trip
from app.schemas.route import (
    RouteComputeRequest,
    RoutePreview,
    RouteCommitRequest,
    RouteVersionSchema,
    RouteVersionList,
    RouteVersionUpdate,
    DayRouteActiveSummary,
    BulkDayRouteSummaryRequest,
    BulkDayRouteSummaryResponse,
    DayRouteBreakdownRequest,
    DayRouteBreakdownResponse,
)
from app.services.routing import (
    get_routing_provider,
    RoutePoint,
    RouteResult as RouteResultData,
    RouteLeg as RouteLegData,
)
from app.services.routing.base import RoutingRateLimitError
from app.services.routing.day_route_breakdown import compute_day_route_breakdown
from shapely.geometry import LineString
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for route previews (in production, use Redis)
route_previews: Dict[str, Dict[str, Any]] = {}

# Simple haversine distance in kilometers
from math import radians, sin, cos, sqrt, atan2

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


@router.post("/days/{day_id}/route/compute", response_model=RoutePreview)
async def compute_route(
    day_id: str, request: RouteComputeRequest, db: Session = Depends(get_db)
):
    """Compute a route for a day"""

    # Get day and validate
    day = db.query(Day).filter(Day.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Get stops for the day
    stops = (
        db.query(Stop)
        .join(Place)
        .filter(Stop.day_id == day_id)
        .order_by(Stop.seq)
        .all()
    )

    if len(stops) < 2:
        raise HTTPException(
            status_code=400, detail="At least 2 stops are required for routing"
        )

    # Convert stops to route points
    route_points = []
    for stop in stops:
        route_points.append(
            RoutePoint(
                lat=float(stop.place.lat),
                lon=float(stop.place.lon),
                name=stop.place.name,
            )
        )

    # Get routing provider and compute route (with optional optimization and leg breakdown)
    try:
        provider = get_routing_provider()
        options = request.options.model_dump() if request.options else {}

        # Identify START, END, VIA
        ordered_stops = stops  # already ordered by seq
        start_stop = next(
            (s for s in ordered_stops if s.kind == StopKind.START), ordered_stops[0]
        )
        end_stop = next(
            (s for s in reversed(ordered_stops) if s.kind == StopKind.END),
            ordered_stops[-1],
        )
        via_stops = [s for s in ordered_stops if s.kind == StopKind.VIA]

        # Fixed stops: DB flag or explicitly provided
        explicit_fixed = set(request.fixed_stop_ids or [])
        fixed_ids = {s.id for s in ordered_stops if s.fixed} | explicit_fixed

        # Build optimized order if requested (respect fixed anchors)
        def dist(a, b):
            return haversine_km(float(a.place.lat), float(a.place.lon), float(b.place.lat), float(b.place.lon))

        async def optimize_segment(seg_start, candidates, seg_end):
            # If provider supports matrix, use it for better ordering; else NN fallback
            if hasattr(provider, 'supports_matrix') and provider.supports_matrix() and candidates:
                points_for_matrix = [
                    RoutePoint(lat=float(seg_start.place.lat), lon=float(seg_start.place.lon), name=seg_start.place.name),
                    *[RoutePoint(lat=float(s.place.lat), lon=float(s.place.lon), name=s.place.name) for s in candidates],
                    RoutePoint(lat=float(seg_end.place.lat), lon=float(seg_end.place.lon), name=seg_end.place.name),
                ]
                # Compute matrix with graceful fallback
                try:
                    matrix = await provider.compute_matrix(points_for_matrix, profile=request.profile, options=options)
                except Exception as e:
                    logger.warning(f"Matrix computation failed: {e}; falling back to greedy NN")
                    return sorted(candidates, key=lambda s: dist(seg_start, s))
                # Validate matrix shape
                n = len(candidates)
                try:
                    if not getattr(matrix, 'durations_min', None):
                        raise ValueError('Missing durations_min in matrix result')
                    rows = len(matrix.durations_min)
                    cols = len(matrix.durations_min[0]) if rows else 0
                    expected = n + 2
                    if rows != expected or cols != expected:
                        raise ValueError(f'Unexpected matrix size {rows}x{cols}, expected {expected}x{expected}')
                except Exception as e:
                    logger.warning(f"Matrix validation failed: {e}; falling back to greedy NN")
                    return sorted(candidates, key=lambda s: dist(seg_start, s))
                # Build NN over matrix (indexes: 0 is start, 1..n are candidates, n+1 is end)
                remaining = list(range(1, n+1))
                order_idx: list[int] = []
                cur = 0
                while remaining:
                    nxt_rel = min(remaining, key=lambda i: matrix.durations_min[cur][i])
                    order_idx.append(nxt_rel)
                    remaining.remove(nxt_rel)
                    cur = nxt_rel
                return [candidates[i-1] for i in order_idx]
            else:
                remaining = candidates[:]
                ordered = []
                cur = seg_start
                while remaining:
                    nxt = min(remaining, key=lambda s: dist(cur, s))
                    ordered.append(nxt)
                    remaining.remove(nxt)
                    cur = nxt
                return ordered

        # Split VIA stops by fixed flag
        via_fixed = [s for s in via_stops if s.id in fixed_ids]
        via_nonfixed = [s for s in via_stops if s.id not in fixed_ids]

        if request.optimize:
            if not via_fixed:
                # Optimize all non-fixed VIAs between START and END regardless of DB seq
                optimized_via = await optimize_segment(start_stop, via_nonfixed, end_stop) if via_nonfixed else []
                final_stops = [start_stop, *optimized_via, end_stop]
            else:
                # Use fixed VIAs as anchors but include all non-fixed VIAs regardless of seq
                anchors = [start_stop] + sorted(via_fixed, key=lambda s: s.seq) + [end_stop]
                optimized_order = []
                remaining = list(via_nonfixed)
                for ai, aj in zip(anchors, anchors[1:]):
                    if not optimized_order:
                        optimized_order.append(ai)
                    if remaining:
                        try:
                            seg_opt = await optimize_segment(ai, remaining, aj)
                        except Exception:
                            seg_opt = remaining
                        optimized_order.extend(seg_opt)
                        remaining = []
                    optimized_order.append(aj)
                # Remove duplicates while preserving order
                seen = set()
                final_stops = []
                for s in optimized_order:
                    if s.id not in seen:
                        seen.add(s.id)
                        final_stops.append(s)
        else:
            # Not optimizing: include all VIAs (fixed first by seq, then the rest by seq)
            via_in_seq = sorted(via_stops, key=lambda s: s.seq)
            final_order = [start_stop, *[s for s in via_in_seq if s.id not in {start_stop.id, end_stop.id}], end_stop]
            seen = set()
            final_stops = []
            for s in final_order:
                if s.id not in seen:
                    seen.add(s.id)
                    final_stops.append(s)

        # Build points from final order
        points = [
            RoutePoint(
                lat=float(s.place.lat), lon=float(s.place.lon), name=s.place.name
            )
            for s in final_stops
        ]

        # Compute per-leg routes and aggregate totals
        legs_data: list[RouteLegData] = []
        coords: list[tuple] = []
        total_km = 0.0
        total_min = 0.0
        for i in range(len(points) - 1):
            pair_result = await provider.compute_route(
                points=[points[i], points[i + 1]],
                profile=request.profile,
                options=options,
            )
            total_km += pair_result.total_km
            total_min += pair_result.total_min
            # use pair geometry as leg geometry
            legs_data.append(
                RouteLegData(
                    distance_km=pair_result.total_km,
                    duration_min=pair_result.total_min,
                    geometry=pair_result.geometry,
                    instructions=(
                        pair_result.legs[0].instructions if pair_result.legs else []
                    ),
                    meta={},
                )
            )
            seg_coords = list(pair_result.geometry.coords)
            if coords and seg_coords and coords[-1] == seg_coords[0]:
                coords.extend(seg_coords[1:])
            else:
                coords.extend(seg_coords)
        full_geometry = LineString(coords) if coords else LineString()

        # Compute warnings: baseline detour vs START->END (or first->last)
        warnings: list[Dict[str, Any]] = []
        try:
            base_points = [points[0], points[-1]]
            baseline = await provider.compute_route(
                points=base_points, profile=request.profile, options=options
            )
            if baseline.total_min > 0:
                detour_ratio = (
                    total_min / baseline.total_min if baseline.total_min else None
                )
                if detour_ratio and detour_ratio > settings.ROUTE_DETOUR_RATIO_THRESHOLD:
                    warnings.append(
                        {
                            "type": "detour",
                            "ratio": round(detour_ratio, 2),
                            "extra_min": round(total_min - baseline.total_min, 1),
                        }
                    )
                # Per-stop impact (approximate) in parallel with a cap
                via_stops = [s for s in final_stops if s.kind == StopKind.VIA]
                sem = asyncio.Semaphore(4)
                async def eval_stop(s):
                    async with sem:
                        test_points = [
                            points[0],
                            RoutePoint(lat=float(s.place.lat), lon=float(s.place.lon), name=s.place.name),
                            points[-1],
                        ]
                        try:
                            test = await provider.compute_route(points=test_points, profile=request.profile, options=options)
                            return s.id, test.total_min - baseline.total_min
                        except Exception as e:
                            logger.debug(f"Per-stop detour failed for {s.id}: {e}")
                            return s.id, None
                results = await asyncio.gather(*(eval_stop(s) for s in via_stops[:8]))
                for sid, extra in results:
                    if extra is None:
                        continue
                    if extra > baseline.total_min * settings.ROUTE_STOP_OFFENDER_RATIO:
                        warnings.append({"type": "stop_detour", "stop_id": sid, "extra_min": round(extra, 1)})
        except Exception as e:
            logger.debug(f"Baseline detour check failed: {e}")

        # Synthesize a RouteResult to store in preview
        synth_result = RouteResultData(
            total_km=total_km,
            total_min=total_min,
            geometry=full_geometry,
            legs=legs_data,
            debug={},
        )

        # Generate preview token
        preview_token = str(uuid.uuid4())

        # Store preview data
        route_previews[preview_token] = {
            "day_id": day_id,
            "profile": request.profile,
            "options": options,
            "result": synth_result,
            "stops_snapshot": [
                {
                    "id": s.id,
                    "place_id": s.place_id,
                    "seq": s.seq,
                    "kind": s.kind.value,
                    "place_name": s.place.name,
                    "lat": float(s.place.lat),
                    "lon": float(s.place.lon),
                }
                for s in final_stops
            ],
            "proposed_order": [s.id for s in final_stops],
            "warnings": warnings,
        }

        # Convert geometry to GeoJSON
        geometry_geojson = {
            "type": "LineString",
            "coordinates": list(full_geometry.coords),
        }

        return RoutePreview(
            total_km=total_km,
            total_min=total_min,
            geometry=geometry_geojson,
            legs=[
                {
                    "distance_km": leg.distance_km,
                    "duration_min": leg.duration_min,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": list(leg.geometry.coords),
                    },
                    "instructions": leg.instructions,
                }
                for leg in legs_data
            ],
            debug={},
            preview_token=preview_token,
            proposed_order=[s.id for s in final_stops],
            warnings=warnings,
        )

    except RoutingRateLimitError as e:
        # Map provider rate limit to 429 for the client
        raise HTTPException(status_code=429, detail="Routing temporarily unavailable due to provider rate limiting. Please try again in a minute.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Route computation failed: {str(e)}"
        )


@router.get("/days/{day_id}/routes", response_model=RouteVersionList)
async def list_saved_routes(day_id: str, db: Session = Depends(get_db)):
    """List saved route versions for a day (active first)."""
    routes = (
        db.query(RouteVersion)
        .filter(RouteVersion.day_id == day_id)
        .order_by(RouteVersion.is_active.desc(), RouteVersion.is_primary.desc(), RouteVersion.version.desc())
        .all()
    )
    return RouteVersionList(routes=routes)


@router.patch("/days/{day_id}/routes/{route_version_id}/activate", response_model=RouteVersionSchema)
async def activate_route_version(day_id: str, route_version_id: str, db: Session = Depends(get_db)):
    """Set a specific route version as the active (default) for the day."""
    rv = db.query(RouteVersion).filter(RouteVersion.id == route_version_id, RouteVersion.day_id == day_id).with_for_update().first()
    if not rv:
        raise HTTPException(status_code=404, detail="Route version not found")
    # Lock all versions for this day to avoid races
    db.query(RouteVersion).filter(RouteVersion.day_id == day_id).with_for_update().all()
    # Deactivate all for the day, then activate selected
    db.query(RouteVersion).filter(RouteVersion.day_id == day_id, RouteVersion.is_active == True).update({"is_active": False})
    rv.is_active = True
    db.commit()
    db.refresh(rv)
    return rv


@router.patch("/days/{day_id}/routes/{route_version_id}/primary", response_model=RouteVersionSchema)
async def set_primary_route_version(day_id: str, route_version_id: str, db: Session = Depends(get_db)):
    """Mark a specific route version as primary (recommended)."""
    rv = db.query(RouteVersion).filter(RouteVersion.id == route_version_id, RouteVersion.day_id == day_id).with_for_update().first()
    if not rv:
        raise HTTPException(status_code=404, detail="Route version not found")
    # Lock all versions for this day to avoid races
    db.query(RouteVersion).filter(RouteVersion.day_id == day_id).with_for_update().all()
    # Clear primary for the day, then set selected
    db.query(RouteVersion).filter(RouteVersion.day_id == day_id, RouteVersion.is_primary == True).update({"is_primary": False})
    rv.is_primary = True
    db.commit()
    db.refresh(rv)
    return rv


@router.patch("/days/{day_id}/routes/{route_version_id}", response_model=RouteVersionSchema)
async def update_route_version(day_id: str, route_version_id: str, body: RouteVersionUpdate, db: Session = Depends(get_db)):
    """Update route version metadata (e.g., rename)."""
    rv = db.query(RouteVersion).filter(RouteVersion.id == route_version_id, RouteVersion.day_id == day_id).first()
    if not rv:
        raise HTTPException(status_code=404, detail="Route version not found")
    if body.name is not None:
        rv.name = body.name
    db.commit()
    db.refresh(rv)
    return rv


@router.post("/days/{day_id}/route/commit", response_model=RouteVersionSchema)
async def commit_route(
    day_id: str, request: RouteCommitRequest, db: Session = Depends(get_db)
):
    """Commit a computed route as a new version"""

    # Get preview data
    if request.preview_token not in route_previews:
        raise HTTPException(status_code=400, detail="Invalid or expired preview token")

    preview_data = route_previews[request.preview_token]

    if preview_data["day_id"] != day_id:
        raise HTTPException(status_code=400, detail="Preview token does not match day")

    # Determine creator (use trip owner)
    day = db.query(Day).filter(Day.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")
    trip = db.query(Trip).filter(Trip.id == day.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    current_user_id = trip.created_by

    try:
        # Get next version number
        max_version = db.query(func.max(RouteVersion.version)).filter(RouteVersion.day_id == day_id).scalar() or 0
        next_version = int(max_version) + 1

        # Deactivate current active route
        db.query(RouteVersion).filter(
            RouteVersion.day_id == day_id, RouteVersion.is_active == True
        ).update({"is_active": False})

        result = preview_data["result"]

        # Create new route version
        route_version = RouteVersion(
            day_id=day_id,
            version=next_version,
            is_active=True,
            is_primary=next_version == 1,  # First route is primary
            name=request.name,
            profile_used=preview_data["profile"],
            total_km=result.total_km,
            total_min=result.total_min,
            geometry_wkt=result.geometry.wkt,
            geojson={"type": "LineString", "coordinates": list(result.geometry.coords)},
            totals={
                "distance_km": result.total_km,
                "duration_min": result.total_min,
                "options": preview_data.get("options") or {}
            },
            stop_snapshot=preview_data["stops_snapshot"],
            created_by=current_user_id,
        )

        db.add(route_version)
        db.flush()  # Get the ID

        # Create route legs
        for i, leg in enumerate(result.legs):
            route_leg = RouteLegModel(
                route_version_id=route_version.id,
                seq=i + 1,
                distance_km=leg.distance_km,
                duration_min=leg.duration_min,
                geometry_wkt=leg.geometry.wkt,
                geojson={
                    "type": "LineString",
                    "coordinates": list(leg.geometry.coords),
                },
                meta=leg.meta,
            )
            db.add(route_leg)

        db.commit()
        db.refresh(route_version)

        # Clean up preview
        del route_previews[request.preview_token]

        return route_version
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit route: {str(e)}")

@router.get("/days/{day_id}/active-summary", response_model=DayRouteActiveSummary)
async def get_day_active_summary(day_id: str, db: Session = Depends(get_db)):
    """Return lightweight active route summary for a single day.
    Does not call external routing. Uses saved active route version if present.
    """
    day = db.query(Day).filter(Day.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Start/End from stops if available
    stops = (
        db.query(Stop).options(joinedload(Stop.place))
        .filter(Stop.day_id == day_id, Stop.kind.in_([StopKind.START, StopKind.END]))
        .order_by(Stop.seq)
        .all()
    )
    start = None
    end = None
    for s in stops:
        obj = None
        if s.place:
            obj = {
                "id": s.place.id,
                "name": s.place.name,
                "address": s.place.address,
                "lat": float(s.place.lat),
                "lon": float(s.place.lon),
                "meta": s.place.meta or {},
            }
        if s.kind == StopKind.START:
            start = obj
        elif s.kind == StopKind.END:
            end = obj

    rv = (
        db.query(RouteVersion)
        .filter(RouteVersion.day_id == day_id, RouteVersion.is_active == True)
        .order_by(RouteVersion.version.desc())
        .first()
    )
    coords = None
    total_km = None
    total_min = None
    route_version_id = None
    if rv:
        route_version_id = rv.id
        if rv.geojson and isinstance(rv.geojson, dict):
            coords = rv.geojson.get("coordinates")
        if rv.total_km is not None:
            try: total_km = float(rv.total_km)
            except Exception: pass
        if rv.total_min is not None:
            try: total_min = float(rv.total_min)
            except Exception: pass

    return DayRouteActiveSummary(
        day_id=day_id,
        start=start,
        end=end,
        route_total_km=total_km,
        route_total_min=total_min,
        route_coordinates=coords,
        route_version_id=route_version_id,
    )


@router.post("/days/bulk-active-summaries", response_model=BulkDayRouteSummaryResponse)
async def get_bulk_active_summaries(body: BulkDayRouteSummaryRequest, db: Session = Depends(get_db)):
    """Return lightweight active route summaries for multiple days.
    """
    day_ids = list(dict.fromkeys(body.day_ids or []))
    if not day_ids:
        return BulkDayRouteSummaryResponse(summaries=[])

    # Fetch days to validate
    days = db.query(Day).filter(Day.id.in_(day_ids)).all()
    valid_ids = {d.id for d in days}

    # Stops for START/END for all days
    stops = (
        db.query(Stop).options(joinedload(Stop.place))
        .filter(Stop.day_id.in_(list(valid_ids)), Stop.kind.in_([StopKind.START, StopKind.END]))
        .order_by(Stop.day_id, Stop.seq)
        .all()
    )
    start_map = {did: None for did in valid_ids}
    end_map = {did: None for did in valid_ids}
    for s in stops:
        obj = None
        if s.place:
            obj = {
                "id": s.place.id,
                "name": s.place.name,
                "address": s.place.address,
                "lat": float(s.place.lat),
                "lon": float(s.place.lon),
                "meta": s.place.meta or {},
            }
        if s.kind == StopKind.START:
            start_map[s.day_id] = obj
        elif s.kind == StopKind.END:
            end_map[s.day_id] = obj

    # Active route versions for all days
    rvs = (
        db.query(RouteVersion)
        .filter(RouteVersion.day_id.in_(list(valid_ids)), RouteVersion.is_active == True)
        .order_by(RouteVersion.day_id, RouteVersion.version.desc())
        .all()
    )
    latest_by_day = {}
    for rv in rvs:
        # Keep the first encountered (due to desc order by version per day)
        if rv.day_id not in latest_by_day:
            latest_by_day[rv.day_id] = rv

    summaries = []
    for did in day_ids:
        if did not in valid_ids:
            continue
        rv = latest_by_day.get(did)
        coords = None
        total_km = None
        total_min = None
        route_version_id = None
        if rv:
            route_version_id = rv.id
            if rv.geojson and isinstance(rv.geojson, dict):
                coords = rv.geojson.get("coordinates")
            if rv.total_km is not None:
                try: total_km = float(rv.total_km)
                except Exception: pass
            if rv.total_min is not None:
                try: total_min = float(rv.total_min)
                except Exception: pass
        summaries.append(DayRouteActiveSummary(
            day_id=did,
            start=start_map.get(did),
            end=end_map.get(did),
            route_total_km=total_km,
            route_total_min=total_min,
            route_coordinates=coords,
            route_version_id=route_version_id,
        ))

    return BulkDayRouteSummaryResponse(summaries=summaries)


@router.post("/days/route-breakdown", response_model=DayRouteBreakdownResponse)
async def compute_day_route_breakdown_endpoint(
    request: DayRouteBreakdownRequest,
    db: Session = Depends(get_db)
):
    """
    Compute detailed route breakdown for a complete day's journey

    This endpoint provides segment-by-segment routing information:
    - Start to Stop 1
    - Stop 1 to Stop 2
    - Stop 2 to Stop 3
    - ...
    - Stop N to End

    Each segment includes:
    - Distance in kilometers
    - Duration in minutes
    - Turn-by-turn instructions
    - Route geometry (GeoJSON)

    The response also includes total distance and duration for the entire day.
    """
    try:
        # Validate that the trip and day exist
        day = db.query(Day).filter(Day.id == request.day_id).first()
        if not day:
            raise HTTPException(status_code=404, detail="Day not found")

        trip = db.query(Trip).filter(Trip.id == request.trip_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")

        # Verify day belongs to trip
        if day.trip_id != request.trip_id:
            raise HTTPException(
                status_code=400,
                detail="Day does not belong to the specified trip"
            )

        # Validate points
        if not request.start:
            raise HTTPException(status_code=400, detail="Start point is required")

        if not request.end:
            raise HTTPException(status_code=400, detail="End point is required")

        # Compute the detailed breakdown
        logger.info(
            f"Computing route breakdown for trip {request.trip_id}, "
            f"day {request.day_id} with {len(request.stops)} stops"
        )

        breakdown = await compute_day_route_breakdown(request)

        logger.info(
            f"Route breakdown computed: {breakdown.total_distance_km:.2f}km, "
            f"{breakdown.total_duration_min:.1f}min across {len(breakdown.segments)} segments"
        )

        return breakdown

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to compute day route breakdown: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute route breakdown: {str(e)}"
        )
