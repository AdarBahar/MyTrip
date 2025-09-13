"""
Route Persistence Service

Handles automatic saving and updating of routes when route breakdown is computed.
Ensures route data stays in sync with trip configuration changes.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from shapely.geometry import LineString

from app.models.route import RouteVersion, RouteLeg as RouteLegModel
from app.models.day import Day
from app.models.stop import Stop
from app.schemas.route import DayRouteBreakdownRequest, DayRouteBreakdownResponse
from app.services.routing.base import RoutePoint, RouteLeg as RouteLegData, RouteResult

logger = logging.getLogger(__name__)


class RoutePersistenceService:
    """
    Service for persisting route breakdown results to the database.
    
    Automatically detects route changes and updates the database accordingly.
    Maintains route version history and ensures data consistency.
    """
    
    def __init__(self, db: Session):
        """
        Initialize route persistence service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def persist_route_breakdown(
        self,
        request: DayRouteBreakdownRequest,
        breakdown: DayRouteBreakdownResponse,
        user_id: Optional[str] = None
    ) -> Optional[RouteVersion]:
        """
        Persist route breakdown results to database if route has changed.
        
        Args:
            request: Original route breakdown request
            breakdown: Computed route breakdown response
            user_id: User ID for audit trail
            
        Returns:
            RouteVersion if route was saved, None if no changes detected
        """
        try:
            # Check if route has changed compared to current active route
            if not await self._should_persist_route(request, breakdown):
                logger.info(f"No route changes detected for day {request.day_id}, skipping persistence")
                return None
            
            # Create route result from breakdown
            route_result = self._breakdown_to_route_result(breakdown)
            
            # Save route to database
            route_version = await self._save_route_version(
                request, route_result, breakdown, user_id
            )
            
            logger.info(
                f"Route persisted for day {request.day_id}: "
                f"version {route_version.version}, "
                f"{route_result.total_distance_km:.2f}km, "
                f"{route_result.total_duration_min:.1f}min"
            )
            
            return route_version
            
        except Exception as e:
            logger.error(f"Failed to persist route breakdown for day {request.day_id}: {e}")
            # Don't fail the breakdown computation if persistence fails
            return None
    
    async def _should_persist_route(
        self,
        request: DayRouteBreakdownRequest,
        breakdown: DayRouteBreakdownResponse
    ) -> bool:
        """
        Determine if the route should be persisted based on changes.
        
        Args:
            request: Route breakdown request
            breakdown: Computed breakdown
            
        Returns:
            True if route should be persisted, False otherwise
        """
        # Get current active route for the day
        current_route = (
            self.db.query(RouteVersion)
            .filter(
                RouteVersion.day_id == request.day_id,
                RouteVersion.is_active == True
            )
            .first()
        )
        
        if not current_route:
            # No active route exists, should persist
            logger.info(f"No active route found for day {request.day_id}, will persist")
            return True
        
        # Check for significant changes
        distance_threshold = 0.1  # 100m
        duration_threshold = 1.0  # 1 minute
        
        distance_diff = abs(float(current_route.total_km) - breakdown.total_distance_km)
        duration_diff = abs(float(current_route.total_min) - breakdown.total_duration_min)
        
        if distance_diff > distance_threshold or duration_diff > duration_threshold:
            logger.info(
                f"Significant route changes detected for day {request.day_id}: "
                f"distance diff {distance_diff:.3f}km, duration diff {duration_diff:.1f}min"
            )
            return True
        
        # Check if stop configuration has changed
        if await self._has_stop_configuration_changed(request, current_route):
            logger.info(f"Stop configuration changed for day {request.day_id}")
            return True
        
        # Check if optimization settings changed
        current_options = current_route.totals.get("options", {}) if current_route.totals else {}
        new_optimize = request.optimize
        current_optimize = current_options.get("optimize", False)
        
        if new_optimize != current_optimize:
            logger.info(f"Optimization setting changed for day {request.day_id}: {current_optimize} -> {new_optimize}")
            return True
        
        return False
    
    async def _has_stop_configuration_changed(
        self,
        request: DayRouteBreakdownRequest,
        current_route: RouteVersion
    ) -> bool:
        """
        Check if the stop configuration has changed compared to saved route.
        
        Args:
            request: Current route request
            current_route: Saved route version
            
        Returns:
            True if stop configuration changed
        """
        # Get current stops from database
        current_stops = (
            self.db.query(Stop)
            .filter(Stop.day_id == request.day_id)
            .order_by(Stop.seq)
            .all()
        )
        
        # Compare stop count
        expected_stop_count = len(request.stops) + 2  # +2 for start and end
        if len(current_stops) != expected_stop_count:
            return True
        
        # Compare stop coordinates (simplified check)
        request_points = [request.start] + request.stops + [request.end]
        
        for i, stop in enumerate(current_stops):
            if i >= len(request_points):
                return True
                
            request_point = request_points[i]
            # Check if coordinates differ significantly (>10m)
            lat_diff = abs(float(stop.place.lat) - request_point.lat)
            lon_diff = abs(float(stop.place.lon) - request_point.lon)
            
            if lat_diff > 0.0001 or lon_diff > 0.0001:  # ~10m threshold
                return True
        
        return False
    
    def _breakdown_to_route_result(self, breakdown: DayRouteBreakdownResponse) -> RouteResult:
        """
        Convert route breakdown to RouteResult for persistence.
        
        Args:
            breakdown: Route breakdown response
            
        Returns:
            RouteResult for database storage
        """
        # Combine all segment geometries
        all_coordinates = []
        legs_data = []
        
        for segment in breakdown.segments:
            if segment.geometry and segment.geometry.get("coordinates"):
                coords = segment.geometry["coordinates"]
                if coords:
                    all_coordinates.extend(coords)
            
            # Create leg data
            leg = RouteLegData(
                distance_km=segment.distance_km,
                duration_min=segment.duration_min,
                geometry=LineString(segment.geometry["coordinates"]) if segment.geometry.get("coordinates") else None,
                instructions=segment.instructions or [],
                meta={
                    "segment_type": segment.segment_type,
                    "from_name": segment.from_name,
                    "to_name": segment.to_name
                }
            )
            legs_data.append(leg)
        
        # Create overall geometry
        if all_coordinates:
            # Remove duplicate consecutive coordinates
            unique_coords = [all_coordinates[0]]
            for coord in all_coordinates[1:]:
                if coord != unique_coords[-1]:
                    unique_coords.append(coord)
            geometry = LineString(unique_coords)
        else:
            geometry = LineString([(0, 0), (0, 0)])  # Fallback empty geometry
        
        return RouteResult(
            total_distance_km=breakdown.total_distance_km,
            total_duration_min=breakdown.total_duration_min,
            geometry=geometry,
            legs=legs_data,
            debug={}
        )
    
    async def _save_route_version(
        self,
        request: DayRouteBreakdownRequest,
        route_result: RouteResult,
        breakdown: DayRouteBreakdownResponse,
        user_id: Optional[str] = None
    ) -> RouteVersion:
        """
        Save route version to database.
        
        Args:
            request: Original request
            route_result: Route result data
            breakdown: Full breakdown response
            user_id: User ID for audit trail
            
        Returns:
            Created RouteVersion
        """
        # Get next version number
        max_version = (
            self.db.query(RouteVersion.version)
            .filter(RouteVersion.day_id == request.day_id)
            .order_by(RouteVersion.version.desc())
            .first()
        )
        next_version = (max_version[0] + 1) if max_version else 1
        
        # Deactivate current active route
        self.db.query(RouteVersion).filter(
            RouteVersion.day_id == request.day_id,
            RouteVersion.is_active == True
        ).update({"is_active": False})
        
        # Determine route name
        route_name = f"Route v{next_version}"
        if breakdown.optimization_savings:
            savings_pct = breakdown.optimization_savings.get("distance_improvement_percent", 0)
            if savings_pct > 0:
                route_name += f" (Optimized, {savings_pct:.1f}% better)"
        
        # Create route version
        route_version = RouteVersion(
            day_id=request.day_id,
            version=next_version,
            is_active=True,
            is_primary=next_version == 1,
            name=route_name,
            profile_used=request.profile,
            total_km=route_result.total_distance_km,
            total_min=route_result.total_duration_min,
            geometry_wkt=route_result.geometry.wkt,
            geojson={
                "type": "LineString",
                "coordinates": list(route_result.geometry.coords)
            },
            totals={
                "distance_km": route_result.total_distance_km,
                "duration_min": route_result.total_duration_min,
                "segments_count": len(breakdown.segments),
                "options": {
                    "optimize": request.optimize,
                    "profile": request.profile,
                    "fixed_stop_indices": request.fixed_stop_indices or []
                },
                "optimization_savings": breakdown.optimization_savings
            },
            stop_snapshot=self._create_stop_snapshot(request),
            created_by=user_id or "system"
        )
        
        self.db.add(route_version)
        self.db.flush()  # Get the ID
        
        # Save route legs
        for i, leg in enumerate(route_result.legs):
            route_leg = RouteLegModel(
                route_version_id=route_version.id,
                leg_index=i,
                distance_km=leg.distance_km,
                duration_min=leg.duration_min,
                geometry_wkt=leg.geometry.wkt if leg.geometry else None,
                instructions={
                    "steps": leg.instructions,
                    "meta": leg.meta
                },
                meta=leg.meta
            )
            self.db.add(route_leg)
        
        self.db.commit()
        self.db.refresh(route_version)
        
        return route_version
    
    def _create_stop_snapshot(self, request: DayRouteBreakdownRequest) -> List[Dict[str, Any]]:
        """
        Create stop snapshot for route version.
        
        Args:
            request: Route breakdown request
            
        Returns:
            Stop snapshot data
        """
        snapshot = []
        
        # Add start
        snapshot.append({
            "seq": 1,
            "kind": "START",
            "name": request.start.name,
            "lat": request.start.lat,
            "lon": request.start.lon,
            "fixed": True
        })
        
        # Add stops
        for i, stop in enumerate(request.stops):
            snapshot.append({
                "seq": i + 2,
                "kind": "VIA",
                "name": stop.name,
                "lat": stop.lat,
                "lon": stop.lon,
                "fixed": False
            })
        
        # Add end
        snapshot.append({
            "seq": len(request.stops) + 2,
            "kind": "END",
            "name": request.end.name,
            "lat": request.end.lat,
            "lon": request.end.lon,
            "fixed": True
        })
        
        return snapshot
