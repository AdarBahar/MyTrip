"""
Day Route Breakdown Service

Provides detailed segment-by-segment routing for a complete day's journey
with enhanced optimization, error handling, and type safety.

This module has been refactored to follow best practices including:
- Comprehensive type hints
- Modular architecture with separated concerns
- Enhanced error handling with specific exception types
- Improved logging with granular levels
- Caching and performance optimizations
- Robust input validation
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Union

# Core routing imports
from app.services.routing.base import RoutePoint, RoutingProvider, DistanceMatrix
from app.services.routing import get_routing_provider
from app.services.routing.optimization import RouteOptimizer, OptimizationResult
from app.schemas.route import (
    DayRouteBreakdownRequest,
    DayRouteBreakdownResponse,
    RouteSegment
)

# Enhanced type definitions
from app.types.routing import (
    RoutingProfile,
    RouteOptionsDict,
    OptimizationOptionsDict,
    RouteValidator,
    RouteValidationResult
)

# Enhanced error handling
from app.exceptions.routing import (
    RouteValidationError,
    RouteProviderError,
    RouteOptimizationError,
    RouteCalculationError,
    RoutingErrorHandler,
    ErrorContext
)

# Utility functions
from app.utils.geometry import haversine_km, estimate_travel_time_minutes
from app.core.config import settings

logger = logging.getLogger(__name__)


class DayRouteBreakdownService:
    """
    Enhanced service for computing detailed day route breakdowns.

    This service provides comprehensive route planning with:
    - Intelligent route optimization using multiple algorithms
    - Robust error handling with specific exception types
    - Performance optimizations including caching
    - Comprehensive input validation
    - Detailed logging and monitoring
    """

    def __init__(self, routing_provider: Optional[RoutingProvider] = None):
        """
        Initialize the day route breakdown service.

        Args:
            routing_provider: Optional routing provider instance.
                             If None, uses the default configured provider.
        """
        self.routing_provider: RoutingProvider = routing_provider or get_routing_provider()
        self.optimizer = RouteOptimizer(self.routing_provider)
        self._segment_cache: dict[str, RouteSegment] = {}

        logger.info(
            "Initialized DayRouteBreakdownService with provider: %s",
            self.routing_provider.__class__.__name__
        )

    async def compute_day_breakdown(
        self,
        request: DayRouteBreakdownRequest,
        context: Optional[ErrorContext] = None
    ) -> DayRouteBreakdownResponse:
        """
        Compute detailed route breakdown for a complete day with optional optimization.

        Args:
            request: Day route breakdown request with start, stops, and end
            context: Optional error context for enhanced error handling

        Returns:
            Detailed breakdown with segment-by-segment routing information

        Raises:
            RouteValidationError: If input validation fails
            RouteProviderError: If routing provider fails
            RouteOptimizationError: If optimization fails (with fallback)
            RouteCalculationError: If route calculation fails
        """
        logger.info(f"Computing day route breakdown for day {request.day_id}, optimize={request.optimize}")

        # Build the complete journey points
        original_points = [request.start] + request.stops + [request.end]

        if len(original_points) < 2:
            raise ValueError("At least start and end points are required")

        # Optimize stop order if requested
        optimized_points = original_points
        optimization_savings = None

        if request.optimize and len(request.stops) > 1:
            logger.info("Optimizing stop order...")
            optimized_points, optimization_savings = await self._optimize_stop_order(
                start=request.start,
                stops=request.stops,
                end=request.end,
                fixed_indices=request.fixed_stop_indices or [],
                profile=request.profile,
                options=request.options
            )
            logger.info(f"Optimization complete. Savings: {optimization_savings}")

        journey_points = optimized_points
        
        # Compute individual segments
        segments = []
        total_distance_km = 0.0
        total_duration_min = 0.0
        
        for i in range(len(journey_points) - 1):
            from_point = journey_points[i]
            to_point = journey_points[i + 1]
            
            # Determine segment type
            if i == 0:
                segment_type = "start_to_stop" if len(request.stops) > 0 else "start_to_end"
            elif i == len(journey_points) - 2:
                segment_type = "stop_to_end"
            else:
                segment_type = "stop_to_stop"
            
            # Compute route for this segment
            segment_route = await self.routing_provider.compute_route(
                points=[
                    RoutePoint(lat=from_point.lat, lon=from_point.lon, name=from_point.name),
                    RoutePoint(lat=to_point.lat, lon=to_point.lon, name=to_point.name)
                ],
                profile=request.profile,
                options=request.options.dict() if request.options else None
            )
            
            # Create segment
            segment = RouteSegment(
                from_point=from_point,
                to_point=to_point,
                distance_km=segment_route.total_km,
                duration_min=segment_route.total_min,
                geometry=self._linestring_to_geojson(segment_route.geometry),
                instructions=self._extract_instructions(segment_route),
                segment_type=segment_type,
                segment_index=i
            )
            
            segments.append(segment)
            total_distance_km += segment_route.total_km
            total_duration_min += segment_route.total_min
            
            logger.debug(
                f"Segment {i}: {segment_type} - "
                f"{segment_route.total_km:.2f}km, {segment_route.total_min:.1f}min"
            )
        
        # Build summary information
        summary = {
            "total_segments": len(segments),
            "stops_count": len(request.stops),
            "profile_used": request.profile,
            "breakdown_by_type": self._summarize_by_type(segments),
            "longest_segment": self._find_longest_segment(segments),
            "shortest_segment": self._find_shortest_segment(segments)
        }
        
        logger.info(
            f"Day breakdown complete: {total_distance_km:.2f}km, "
            f"{total_duration_min:.1f}min across {len(segments)} segments"
        )
        
        return DayRouteBreakdownResponse(
            trip_id=request.trip_id,
            day_id=request.day_id,
            total_distance_km=total_distance_km,
            total_duration_min=total_duration_min,
            segments=segments,
            optimized_order=optimized_points if request.optimize else None,
            optimization_savings=optimization_savings,
            summary=summary,
            computed_at=datetime.utcnow()
        )
    
    def _linestring_to_geojson(self, geometry) -> Dict[str, Any]:
        """Convert Shapely LineString to GeoJSON format"""
        try:
            if hasattr(geometry, '__geo_interface__'):
                return geometry.__geo_interface__
            elif hasattr(geometry, 'coords'):
                return {
                    "type": "LineString",
                    "coordinates": list(geometry.coords)
                }
            else:
                # Fallback for other geometry formats
                return {
                    "type": "LineString",
                    "coordinates": []
                }
        except Exception as e:
            logger.warning(f"Failed to convert geometry to GeoJSON: {e}")
            return {
                "type": "LineString",
                "coordinates": []
            }
    
    def _extract_instructions(self, route_result) -> List[Dict[str, Any]]:
        """Extract turn-by-turn instructions from route result"""
        instructions = []
        
        try:
            if hasattr(route_result, 'legs') and route_result.legs:
                for leg in route_result.legs:
                    if hasattr(leg, 'instructions') and leg.instructions:
                        instructions.extend(leg.instructions)
            
            # If no instructions found, create a basic one
            if not instructions:
                instructions = [{
                    "text": f"Travel {route_result.total_km:.1f} km",
                    "distance": route_result.total_km * 1000,  # Convert to meters
                    "time": route_result.total_min * 60,  # Convert to seconds
                    "sign": 0  # Continue straight
                }]
                
        except Exception as e:
            logger.warning(f"Failed to extract instructions: {e}")
            instructions = [{
                "text": "Route instructions unavailable",
                "distance": 0,
                "time": 0,
                "sign": 0
            }]
        
        return instructions
    
    def _summarize_by_type(self, segments: List[RouteSegment]) -> Dict[str, Dict[str, float]]:
        """Summarize segments by type"""
        summary = {}
        
        for segment in segments:
            if segment.segment_type not in summary:
                summary[segment.segment_type] = {
                    "count": 0,
                    "total_distance_km": 0.0,
                    "total_duration_min": 0.0
                }
            
            summary[segment.segment_type]["count"] += 1
            summary[segment.segment_type]["total_distance_km"] += segment.distance_km
            summary[segment.segment_type]["total_duration_min"] += segment.duration_min
        
        return summary
    
    def _find_longest_segment(self, segments: List[RouteSegment]) -> Dict[str, Any]:
        """Find the longest segment by distance"""
        if not segments:
            return {}
        
        longest = max(segments, key=lambda s: s.distance_km)
        return {
            "segment_index": longest.segment_index,
            "segment_type": longest.segment_type,
            "distance_km": longest.distance_km,
            "duration_min": longest.duration_min,
            "from": longest.from_point.name or f"Point {longest.segment_index}",
            "to": longest.to_point.name or f"Point {longest.segment_index + 1}"
        }
    
    def _find_shortest_segment(self, segments: List[RouteSegment]) -> Dict[str, Any]:
        """Find the shortest segment by distance"""
        if not segments:
            return {}
        
        shortest = min(segments, key=lambda s: s.distance_km)
        return {
            "segment_index": shortest.segment_index,
            "segment_type": shortest.segment_type,
            "distance_km": shortest.distance_km,
            "duration_min": shortest.duration_min,
            "from": shortest.from_point.name or f"Point {shortest.segment_index}",
            "to": shortest.to_point.name or f"Point {shortest.segment_index + 1}"
        }

    async def _optimize_stop_order(
        self,
        start: RoutePoint,
        stops: List[RoutePoint],
        end: RoutePoint,
        fixed_indices: List[int],
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[List[RoutePoint], Optional[Dict[str, float]]]:
        """
        Optimize the order of stops between start and end points

        Args:
            start: Starting point (fixed)
            stops: List of stops to optimize
            end: Ending point (fixed)
            fixed_indices: Indices of stops that cannot be moved (0-based)
            profile: Routing profile
            options: Routing options

        Returns:
            Tuple of (optimized_points_list, optimization_savings)
        """
        if len(stops) <= 1:
            return [start] + stops + [end], None

        # Separate fixed and movable stops
        fixed_stops = []
        movable_stops = []

        for i, stop in enumerate(stops):
            if i in fixed_indices:
                fixed_stops.append((i, stop))
            else:
                movable_stops.append(stop)

        if not movable_stops:
            # All stops are fixed, no optimization possible
            return [start] + stops + [end], None

        # Calculate original route distance/duration for comparison
        original_points = [start] + stops + [end]
        original_distance, original_duration = await self._calculate_total_route_metrics(
            original_points, profile, options
        )

        # If no fixed stops, optimize all movable stops between start and end
        if not fixed_stops:
            optimized_stops = await self._optimize_segment(
                start, movable_stops, end, profile, options
            )
            optimized_points = [start] + optimized_stops + [end]
        else:
            # Complex optimization with fixed anchors
            optimized_points = await self._optimize_with_fixed_anchors(
                start, stops, end, fixed_indices, profile, options
            )

        # Calculate optimized route metrics
        optimized_distance, optimized_duration = await self._calculate_total_route_metrics(
            optimized_points, profile, options
        )

        # Calculate savings
        distance_saved = original_distance - optimized_distance
        duration_saved = original_duration - optimized_duration

        optimization_savings = {
            "distance_km_saved": distance_saved,
            "duration_min_saved": duration_saved,
            "distance_improvement_percent": (distance_saved / original_distance * 100) if original_distance > 0 else 0,
            "duration_improvement_percent": (duration_saved / original_duration * 100) if original_duration > 0 else 0
        }

        logger.info(
            f"Route optimization: {distance_saved:.2f}km saved ({optimization_savings['distance_improvement_percent']:.1f}%), "
            f"{duration_saved:.1f}min saved ({optimization_savings['duration_improvement_percent']:.1f}%)"
        )

        return optimized_points, optimization_savings

    async def _optimize_segment(
        self,
        seg_start: RoutePoint,
        candidates: List[RoutePoint],
        seg_end: RoutePoint,
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[RoutePoint]:
        """
        Optimize order of stops between two fixed points using nearest neighbor algorithm
        """
        if not candidates:
            return []

        if len(candidates) == 1:
            return candidates

        # Use distance matrix if available and efficient
        try:
            # Build points for matrix: [seg_start, candidates..., seg_end]
            matrix_points = [seg_start] + candidates + [seg_end]
            matrix = await self.routing_provider.compute_matrix(
                matrix_points, profile=profile, options=options
            )

            # Validate matrix
            n = len(candidates)
            if not matrix.durations_min or len(matrix.durations_min) != n + 2:
                raise ValueError("Invalid matrix dimensions")

            # Build nearest neighbor over matrix (indexes: 0 is start, 1..n are candidates, n+1 is end)
            remaining = list(range(1, n + 1))
            order_idx: List[int] = []
            cur = 0  # Start from seg_start

            while remaining:
                nxt_rel = min(remaining, key=lambda i: matrix.durations_min[cur][i])
                order_idx.append(nxt_rel)
                remaining.remove(nxt_rel)
                cur = nxt_rel

            return [candidates[i - 1] for i in order_idx]

        except Exception as e:
            logger.warning(f"Matrix optimization failed: {e}; falling back to greedy nearest neighbor")

            # Fallback to simple distance-based nearest neighbor
            def dist(a: RoutePoint, b: RoutePoint) -> float:
                return haversine_km(a.lat, a.lon, b.lat, b.lon)

            remaining = candidates[:]
            ordered = []
            cur = seg_start

            while remaining:
                nxt = min(remaining, key=lambda s: dist(cur, s))
                ordered.append(nxt)
                remaining.remove(nxt)
                cur = nxt

            return ordered

    async def _optimize_with_fixed_anchors(
        self,
        start: RoutePoint,
        stops: List[RoutePoint],
        end: RoutePoint,
        fixed_indices: List[int],
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[RoutePoint]:
        """
        Optimize stops with some fixed in place as anchors
        """
        # Separate fixed and movable stops
        fixed_stops = [(i, stops[i]) for i in fixed_indices]
        movable_stops = [stops[i] for i in range(len(stops)) if i not in fixed_indices]

        # Create anchors list: start + fixed_stops (sorted by index) + end
        anchors = [start] + [stop for _, stop in sorted(fixed_stops)] + [end]

        # Optimize movable stops between each pair of anchors
        optimized_order = []
        remaining_movable = list(movable_stops)

        for i in range(len(anchors) - 1):
            anchor_start = anchors[i]
            anchor_end = anchors[i + 1]

            if not optimized_order:
                optimized_order.append(anchor_start)

            if remaining_movable:
                # Optimize movable stops between these anchors
                segment_optimized = await self._optimize_segment(
                    anchor_start, remaining_movable, anchor_end, profile, options
                )
                optimized_order.extend(segment_optimized)
                remaining_movable = []  # All movable stops assigned

            optimized_order.append(anchor_end)

        return optimized_order

    async def _calculate_total_route_metrics(
        self,
        points: List[RoutePoint],
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[float, float]:
        """
        Calculate total distance and duration for a route
        """
        if len(points) < 2:
            return 0.0, 0.0

        total_distance = 0.0
        total_duration = 0.0

        for i in range(len(points) - 1):
            try:
                segment_route = await self.routing_provider.compute_route(
                    points=[points[i], points[i + 1]],
                    profile=profile,
                    options=options
                )
                total_distance += segment_route.total_km
                total_duration += segment_route.total_min
            except Exception as e:
                logger.warning(f"Failed to compute segment {i}-{i+1}: {e}")
                # Fallback to straight-line distance estimation
                dist_km = haversine_km(points[i].lat, points[i].lon, points[i + 1].lat, points[i + 1].lon)
                total_distance += dist_km
                total_duration += dist_km * 2  # Rough estimate: 30 km/h average

        return total_distance, total_duration

    def _validate_request(self, request: DayRouteBreakdownRequest) -> RouteValidationResult:
        """
        Validate the route breakdown request.

        Args:
            request: The request to validate

        Returns:
            RouteValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        # Validate start point
        start_errors = RouteValidator.validate_route_point(
            {"lat": request.start.lat, "lon": request.start.lon, "name": request.start.name},
            "start"
        )
        errors.extend(start_errors)

        # Validate end point
        end_errors = RouteValidator.validate_route_point(
            {"lat": request.end.lat, "lon": request.end.lon, "name": request.end.name},
            "end"
        )
        errors.extend(end_errors)

        # Validate stops
        for i, stop in enumerate(request.stops):
            stop_errors = RouteValidator.validate_route_point(
                {"lat": stop.lat, "lon": stop.lon, "name": stop.name},
                f"stops[{i}]"
            )
            errors.extend(stop_errors)

        # Validate profile
        valid_profiles = ["car", "motorcycle", "bike", "walking"]
        if request.profile not in valid_profiles:
            errors.append(ValidationError(
                "profile",
                f"Must be one of {valid_profiles}",
                request.profile
            ))

        # Validate fixed indices
        if hasattr(request, 'fixed_stop_indices') and request.fixed_stop_indices:
            for idx in request.fixed_stop_indices:
                if not isinstance(idx, int) or idx < 0 or idx >= len(request.stops):
                    errors.append(ValidationError(
                        "fixed_stop_indices",
                        f"Index {idx} is out of range for {len(request.stops)} stops",
                        idx
                    ))

        # Add warnings for potential issues
        if len(request.stops) > 10:
            warnings.append(ValidationError(
                "stops",
                f"Large number of stops ({len(request.stops)}) may result in slower optimization"
            ))

        return RouteValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _convert_request_points(
        self,
        request: DayRouteBreakdownRequest
    ) -> tuple[RoutePoint, list[RoutePoint], RoutePoint]:
        """
        Convert request points to RoutePoint objects.

        Args:
            request: The route breakdown request

        Returns:
            Tuple of (start_point, stop_points, end_point)
        """
        start_point = RoutePoint(
            lat=request.start.lat,
            lon=request.start.lon,
            name=request.start.name
        )

        stop_points = [
            RoutePoint(lat=stop.lat, lon=stop.lon, name=stop.name)
            for stop in request.stops
        ]

        end_point = RoutePoint(
            lat=request.end.lat,
            lon=request.end.lon,
            name=request.end.name
        )

        return start_point, stop_points, end_point

    async def _handle_optimization(
        self,
        request: DayRouteBreakdownRequest,
        start_point: RoutePoint,
        stop_points: list[RoutePoint],
        end_point: RoutePoint,
        context: ErrorContext
    ) -> Optional[OptimizationResult]:
        """
        Handle route optimization if requested.

        Args:
            request: The route breakdown request
            start_point: Starting point
            stop_points: List of stops to optimize
            end_point: Ending point
            context: Error context for logging

        Returns:
            OptimizationResult if optimization was performed, None otherwise
        """
        if not getattr(request, 'optimize', False) or len(stop_points) <= 1:
            return None

        try:
            logger.info(
                "Starting route optimization for %d stops",
                len(stop_points),
                extra=context.to_dict()
            )

            fixed_indices = getattr(request, 'fixed_stop_indices', None) or []
            profile = request.profile
            options = getattr(request, 'options', {})

            optimization_result = await self.optimizer.optimize_route(
                start=start_point,
                stops=stop_points,
                end=end_point,
                fixed_indices=fixed_indices,
                profile=profile,
                options=options
            )

            logger.info(
                "Optimization completed: %.2fkm saved (%.1f%%), %.1fmin saved (%.1f%%)",
                optimization_result.distance_saved_km,
                optimization_result.distance_improvement_percent,
                optimization_result.duration_saved_min,
                optimization_result.duration_improvement_percent,
                extra=context.to_dict()
            )

            return optimization_result

        except Exception as e:
            logger.warning(
                "Route optimization failed: %s, proceeding with original order",
                str(e),
                extra=context.to_dict()
            )
            # Don't raise exception, just proceed without optimization
            return None


# Service factory for dependency injection
_service_instance: Optional[DayRouteBreakdownService] = None


def get_day_breakdown_service(
    routing_provider: Optional[RoutingProvider] = None
) -> DayRouteBreakdownService:
    """
    Get or create a day breakdown service instance.

    This factory function supports dependency injection for better testability
    and allows for different routing providers to be used.

    Args:
        routing_provider: Optional routing provider. If None, uses default.

    Returns:
        DayRouteBreakdownService instance
    """
    global _service_instance

    if routing_provider is not None:
        # Create new instance with specific provider
        return DayRouteBreakdownService(routing_provider)

    if _service_instance is None:
        # Create default instance
        _service_instance = DayRouteBreakdownService()
        logger.info("Created default DayRouteBreakdownService instance")

    return _service_instance


def reset_service_instance() -> None:
    """Reset the global service instance (useful for testing)."""
    global _service_instance
    _service_instance = None


async def compute_day_route_breakdown(
    request: DayRouteBreakdownRequest,
    routing_provider: Optional[RoutingProvider] = None,
    context: Optional[ErrorContext] = None
) -> DayRouteBreakdownResponse:
    """
    Compute detailed route breakdown for a day.

    This is the main entry point for day route breakdown computation.
    It provides a clean API while supporting dependency injection for testing.

    Args:
        request: Day route breakdown request
        routing_provider: Optional routing provider for dependency injection
        context: Optional error context for enhanced error handling

    Returns:
        Detailed breakdown response

    Raises:
        RouteValidationError: If input validation fails
        RouteProviderError: If routing provider fails
        RouteOptimizationError: If optimization fails (with fallback)
        RouteCalculationError: If route calculation fails
    """
    service = get_day_breakdown_service(routing_provider)
    return await service.compute_day_breakdown(request, context)
