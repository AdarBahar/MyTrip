"""
Route optimization algorithms and utilities.

This module provides various algorithms for optimizing route order,
including nearest neighbor heuristics and TSP-based approaches.
"""
import asyncio
import logging
from typing import Optional, Union
from dataclasses import dataclass

from app.services.routing.base import RoutePoint, RoutingProvider, DistanceMatrix
from app.utils.geometry import haversine_km, estimate_travel_time_minutes

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of route optimization containing optimized order and metrics."""
    optimized_points: list[RoutePoint]
    original_distance_km: float
    optimized_distance_km: float
    original_duration_min: float
    optimized_duration_min: float
    
    @property
    def distance_saved_km(self) -> float:
        """Distance saved through optimization."""
        return self.original_distance_km - self.optimized_distance_km
    
    @property
    def duration_saved_min(self) -> float:
        """Duration saved through optimization."""
        return self.original_duration_min - self.optimized_duration_min
    
    @property
    def distance_improvement_percent(self) -> float:
        """Percentage improvement in distance."""
        if self.original_distance_km <= 0:
            return 0.0
        return (self.distance_saved_km / self.original_distance_km) * 100.0
    
    @property
    def duration_improvement_percent(self) -> float:
        """Percentage improvement in duration."""
        if self.original_duration_min <= 0:
            return 0.0
        return (self.duration_saved_min / self.original_duration_min) * 100.0


class RouteOptimizer:
    """
    Route optimization service using various algorithms.
    
    Provides multiple optimization strategies including nearest neighbor
    heuristics and more sophisticated TSP-based approaches.
    """
    
    def __init__(self, routing_provider: RoutingProvider):
        """
        Initialize the route optimizer.
        
        Args:
            routing_provider: Routing provider for distance/duration calculations
        """
        self.routing_provider = routing_provider
        self._route_cache: dict[str, tuple[float, float]] = {}
    
    async def optimize_route(
        self,
        start: RoutePoint,
        stops: list[RoutePoint],
        end: RoutePoint,
        fixed_indices: Optional[list[int]] = None,
        profile: str = "car",
        options: Optional[dict] = None
    ) -> OptimizationResult:
        """
        Optimize route order for minimum distance/time.
        
        Args:
            start: Starting point (fixed)
            stops: List of stops to optimize
            end: Ending point (fixed)
            fixed_indices: Indices of stops that cannot be moved (0-based)
            profile: Routing profile
            options: Additional routing options
            
        Returns:
            OptimizationResult with optimized order and metrics
        """
        if len(stops) <= 1:
            # No optimization needed for single stop
            original_points = [start] + stops + [end]
            distance, duration = await self._calculate_route_metrics(
                original_points, profile, options
            )
            return OptimizationResult(
                optimized_points=original_points,
                original_distance_km=distance,
                optimized_distance_km=distance,
                original_duration_min=duration,
                optimized_duration_min=duration
            )
        
        # Calculate original route metrics
        original_points = [start] + stops + [end]
        original_distance, original_duration = await self._calculate_route_metrics(
            original_points, profile, options
        )
        
        # Perform optimization
        if not fixed_indices:
            # Simple case: optimize all stops
            optimized_stops = await self._optimize_segment(
                start, stops, end, profile, options
            )
            optimized_points = [start] + optimized_stops + [end]
        else:
            # Complex case: optimize around fixed stops
            optimized_points = await self._optimize_with_fixed_anchors(
                start, stops, end, fixed_indices, profile, options
            )
        
        # Calculate optimized route metrics
        optimized_distance, optimized_duration = await self._calculate_route_metrics(
            optimized_points, profile, options
        )
        
        return OptimizationResult(
            optimized_points=optimized_points,
            original_distance_km=original_distance,
            optimized_distance_km=optimized_distance,
            original_duration_min=original_duration,
            optimized_duration_min=optimized_duration
        )
    
    async def _optimize_segment(
        self,
        seg_start: RoutePoint,
        candidates: list[RoutePoint],
        seg_end: RoutePoint,
        profile: str,
        options: Optional[dict] = None
    ) -> list[RoutePoint]:
        """
        Optimize order of stops between two fixed points.
        
        Uses distance matrix when available, falls back to nearest neighbor
        with haversine distance.
        """
        if not candidates:
            return []
        
        if len(candidates) == 1:
            return candidates
        
        try:
            # Try to use distance matrix for accurate optimization
            return await self._matrix_based_optimization(
                seg_start, candidates, seg_end, profile, options
            )
        except Exception as e:
            logger.warning(f"Matrix optimization failed: {e}, using fallback")
            return self._greedy_nearest_neighbor(seg_start, candidates, seg_end)
    
    async def _matrix_based_optimization(
        self,
        seg_start: RoutePoint,
        candidates: list[RoutePoint],
        seg_end: RoutePoint,
        profile: str,
        options: Optional[dict] = None
    ) -> list[RoutePoint]:
        """Optimize using distance matrix for accurate results."""
        # Build points for matrix: [seg_start, candidates..., seg_end]
        matrix_points = [seg_start] + candidates + [seg_end]
        matrix = await self.routing_provider.compute_matrix(
            matrix_points, profile=profile, options=options
        )
        
        # Validate matrix
        n = len(candidates)
        if not matrix.durations_min or len(matrix.durations_min) != n + 2:
            raise ValueError("Invalid matrix dimensions")
        
        # Nearest neighbor over matrix (0=start, 1..n=candidates, n+1=end)
        remaining = list(range(1, n + 1))
        order_idx: list[int] = []
        current = 0  # Start from seg_start
        
        while remaining:
            next_idx = min(remaining, key=lambda i: matrix.durations_min[current][i])
            order_idx.append(next_idx)
            remaining.remove(next_idx)
            current = next_idx
        
        return [candidates[i - 1] for i in order_idx]
    
    def _greedy_nearest_neighbor(
        self,
        seg_start: RoutePoint,
        candidates: list[RoutePoint],
        seg_end: RoutePoint
    ) -> list[RoutePoint]:
        """Fallback optimization using haversine distance."""
        remaining = candidates[:]
        ordered = []
        current = seg_start
        
        while remaining:
            nearest = min(remaining, key=lambda s: haversine_km(
                current.lat, current.lon, s.lat, s.lon
            ))
            ordered.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        return ordered

    async def _optimize_with_fixed_anchors(
        self,
        start: RoutePoint,
        stops: list[RoutePoint],
        end: RoutePoint,
        fixed_indices: list[int],
        profile: str,
        options: Optional[dict] = None
    ) -> list[RoutePoint]:
        """
        Optimize route with some stops fixed in position.

        Divides the route into segments between fixed points and optimizes
        each segment independently.
        """
        # Create anchor points (fixed stops + start/end)
        anchors = [(start, -1)]  # (point, original_index)

        for i, stop in enumerate(stops):
            if i in fixed_indices:
                anchors.append((stop, i))

        anchors.append((end, len(stops)))
        anchors.sort(key=lambda x: x[1])  # Sort by original position

        # Optimize segments between anchors
        optimized_stops = []

        for i in range(len(anchors) - 1):
            seg_start_point, seg_start_idx = anchors[i]
            seg_end_point, seg_end_idx = anchors[i + 1]

            # Find movable stops in this segment
            segment_candidates = []
            for j, stop in enumerate(stops):
                if j not in fixed_indices and seg_start_idx < j < seg_end_idx:
                    segment_candidates.append(stop)

            # Add fixed stop at start of segment (if it's a stop, not start/end)
            if seg_start_idx >= 0:
                optimized_stops.append(stops[seg_start_idx])

            # Optimize movable stops in segment
            if segment_candidates:
                optimized_segment = await self._optimize_segment(
                    seg_start_point, segment_candidates, seg_end_point,
                    profile, options
                )
                optimized_stops.extend(optimized_segment)

        return optimized_stops

    async def _calculate_route_metrics(
        self,
        points: list[RoutePoint],
        profile: str,
        options: Optional[dict] = None
    ) -> tuple[float, float]:
        """
        Calculate total distance and duration for a route.

        Returns:
            Tuple of (total_distance_km, total_duration_min)
        """
        if len(points) < 2:
            return 0.0, 0.0

        total_distance = 0.0
        total_duration = 0.0

        # Use caching to avoid redundant calculations
        for i in range(len(points) - 1):
            from_point = points[i]
            to_point = points[i + 1]

            cache_key = f"{from_point.lat},{from_point.lon}-{to_point.lat},{to_point.lon}-{profile}"

            if cache_key in self._route_cache:
                distance, duration = self._route_cache[cache_key]
            else:
                try:
                    # Try routing provider first
                    route_result = await self.routing_provider.compute_route(
                        [from_point, to_point], profile=profile, options=options
                    )
                    distance = route_result.total_distance_km
                    duration = route_result.total_duration_min
                except Exception as e:
                    logger.warning(f"Route calculation failed: {e}, using fallback")
                    # Fallback to haversine + estimated time
                    distance = haversine_km(
                        from_point.lat, from_point.lon,
                        to_point.lat, to_point.lon
                    )
                    duration = estimate_travel_time_minutes(distance, profile)

                # Cache the result
                self._route_cache[cache_key] = (distance, duration)

            total_distance += distance
            total_duration += duration

        return total_distance, total_duration

    def clear_cache(self) -> None:
        """Clear the route calculation cache."""
        self._route_cache.clear()
