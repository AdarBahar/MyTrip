"""
Routing API router
"""
import json
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.day import Day
from app.models.stop import Stop
from app.models.place import Place
from app.models.route import RouteVersion, RouteLeg
from app.schemas.route import (
    RouteComputeRequest, RoutePreview, RouteCommitRequest,
    RouteVersionSchema, RouteVersionList
)
from app.services.routing import get_routing_provider, RoutePoint

router = APIRouter()

# In-memory storage for route previews (in production, use Redis)
route_previews: Dict[str, Dict[str, Any]] = {}


@router.post("/days/{day_id}/route/compute", response_model=RoutePreview)
async def compute_route(
    day_id: str,
    request: RouteComputeRequest,
    db: Session = Depends(get_db)
):
    """Compute a route for a day"""

    # Get day and validate
    day = db.query(Day).filter(Day.id == day_id).first()
    if not day:
        raise HTTPException(status_code=404, detail="Day not found")

    # Get stops for the day
    stops = db.query(Stop).join(Place).filter(
        Stop.day_id == day_id
    ).order_by(Stop.seq).all()

    if len(stops) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 stops are required for routing"
        )

    # Convert stops to route points
    route_points = []
    for stop in stops:
        route_points.append(RoutePoint(
            lat=float(stop.place.lat),
            lon=float(stop.place.lon),
            name=stop.place.name
        ))

    # Get routing provider and compute route
    try:
        provider = get_routing_provider()
        options = request.options.model_dump() if request.options else {}

        result = await provider.compute_route(
            points=route_points,
            profile=request.profile,
            options=options
        )

        # Generate preview token
        preview_token = str(uuid.uuid4())

        # Store preview data
        route_previews[preview_token] = {
            "day_id": day_id,
            "profile": request.profile,
            "result": result,
            "stops_snapshot": [
                {
                    "id": stop.id,
                    "place_id": stop.place_id,
                    "seq": stop.seq,
                    "kind": stop.kind.value,
                    "place_name": stop.place.name,
                    "lat": float(stop.place.lat),
                    "lon": float(stop.place.lon)
                }
                for stop in stops
            ]
        }

        # Convert geometry to GeoJSON
        geometry_geojson = {
            "type": "LineString",
            "coordinates": list(result.geometry.coords)
        }

        # Store geometry as WKT for database
        geometry_wkt = result.geometry.wkt

        return RoutePreview(
            total_km=result.total_km,
            total_min=result.total_min,
            geometry=geometry_geojson,
            legs=[
                {
                    "distance_km": leg.distance_km,
                    "duration_min": leg.duration_min,
                    "geometry": {
                        "type": "LineString",
                        "coordinates": list(leg.geometry.coords)
                    },
                    "instructions": leg.instructions
                }
                for leg in result.legs
            ],
            debug=result.debug,
            preview_token=preview_token
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Route computation failed: {str(e)}"
        )


@router.post("/days/{day_id}/route/commit", response_model=RouteVersionSchema)
async def commit_route(
    day_id: str,
    request: RouteCommitRequest,
    db: Session = Depends(get_db)
):
    """Commit a computed route as a new version"""

    # Get preview data
    if request.preview_token not in route_previews:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired preview token"
        )

    preview_data = route_previews[request.preview_token]

    if preview_data["day_id"] != day_id:
        raise HTTPException(
            status_code=400,
            detail="Preview token does not match day"
        )

    # TODO: Get current user from authentication
    current_user_id = "demo-user-id"  # Placeholder

    try:
        # Get next version number
        max_version = db.query(RouteVersion).filter(
            RouteVersion.day_id == day_id
        ).count()

        next_version = max_version + 1

        # Deactivate current active route
        db.query(RouteVersion).filter(
            RouteVersion.day_id == day_id,
            RouteVersion.is_active == True
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
            geojson={
                "type": "LineString",
                "coordinates": list(result.geometry.coords)
            },
            totals={
                "distance_km": result.total_km,
                "duration_min": result.total_min
            },
            stop_snapshot=preview_data["stops_snapshot"],
            created_by=current_user_id
        )

        db.add(route_version)
        db.flush()  # Get the ID

        # Create route legs
        for i, leg in enumerate(result.legs):
            route_leg = RouteLeg(
                route_version_id=route_version.id,
                seq=i + 1,
                distance_km=leg.distance_km,
                duration_min=leg.duration_min,
                geometry_wkt=leg.geometry.wkt,
                geojson={
                    "type": "LineString",
                    "coordinates": list(leg.geometry.coords)
                },
                meta=leg.meta
            )
            db.add(route_leg)

        db.commit()
        db.refresh(route_version)

        # Clean up preview
        del route_previews[request.preview_token]

        return route_version

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to commit route: {str(e)}"
        )