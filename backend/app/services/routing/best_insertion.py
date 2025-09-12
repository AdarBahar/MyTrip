"""
Best Insertion Algorithm for fast route optimization.

This module implements the "best insertion" algorithm for O(n) route optimization,
providing instant feedback when adding stops to a route without full re-optimization.
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from app.services.routing.base import RoutePoint, RoutingProvider
from app.utils.geometry import haversine_km, estimate_travel_time_minutes
from app.exceptions.routing import RouteCalculationError

logger = logging.getLogger(__name__)


@dataclass
class InsertionResult:
    """Result of best insertion calculation."""
    best_position: int  # Index where to insert the new stop
    insertion_cost: float  # Additional cost (time or distance) of insertion
    total_cost_before: float  # Total cost before insertion
    total_cost_after: float  # Total cost after insertion
    cost_type: str  # "time" or "distance"


class BestInsertionOptimizer:
    """
    Fast best insertion optimizer for interactive route editing.
    
    Implements the best insertion heuristic which finds the optimal position
    to insert a new stop into an existing route with O(n) complexity.
    
    This provides instant feedback for users adding stops without requiring
    full route re-optimization.
    """
    
    def __init__(self, routing_provider: RoutingProvider):
        """
        Initialize best insertion optimizer.
        
        Args:
            routing_provider: Routing provider for distance/time calculations
        """
        self.routing_provider = routing_provider
        self._matrix_cache: Dict[str, Dict[str, float]] = {}
    
    async def find_best_insertion_position(
        self,
        current_route: List[RoutePoint],
        new_stop: RoutePoint,
        profile: str = "car",
        optimize_for: str = "time",
        options: Optional[Dict[str, Any]] = None
    ) -> InsertionResult:
        """
        Find the best position to insert a new stop into an existing route.
        
        Args:
            current_route: Current route points (including start and end)
            new_stop: New stop to insert
            profile: Routing profile
            optimize_for: "time" or "distance"
            options: Additional routing options
            
        Returns:
            InsertionResult with best position and cost analysis
            
        Raises:
            RouteCalculationError: If insertion calculation fails
        """
        if len(current_route) < 2:
            raise RouteCalculationError(
                "Current route must have at least start and end points",
                fallback_used=False
            )
        
        try:
            # Build matrix including all current points + new stop
            all_points = current_route + [new_stop]
            matrix = await self._get_or_compute_matrix(
                all_points, profile, optimize_for, options
            )
            
            # Find best insertion position
            best_position, insertion_cost = self._calculate_best_insertion(
                current_route, new_stop, matrix, optimize_for
            )
            
            # Calculate total costs
            total_cost_before = self._calculate_total_cost(current_route, matrix, optimize_for)
            total_cost_after = total_cost_before + insertion_cost
            
            logger.debug(
                f"Best insertion: position {best_position}, cost +{insertion_cost:.2f} "
                f"({optimize_for}), total: {total_cost_before:.2f} -> {total_cost_after:.2f}"
            )
            
            return InsertionResult(
                best_position=best_position,
                insertion_cost=insertion_cost,
                total_cost_before=total_cost_before,
                total_cost_after=total_cost_after,
                cost_type=optimize_for
            )
            
        except Exception as e:
            logger.error(f"Best insertion calculation failed: {e}")
            if isinstance(e, RouteCalculationError):
                raise
            raise RouteCalculationError(
                f"Failed to calculate best insertion: {str(e)}",
                fallback_used=False
            )
    
    async def insert_stop_at_best_position(
        self,
        current_route: List[RoutePoint],
        new_stop: RoutePoint,
        profile: str = "car",
        optimize_for: str = "time",
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[RoutePoint], InsertionResult]:
        """
        Insert a new stop at the best position in the current route.
        
        Args:
            current_route: Current route points
            new_stop: New stop to insert
            profile: Routing profile
            optimize_for: "time" or "distance"
            options: Additional routing options
            
        Returns:
            Tuple of (updated_route, insertion_result)
        """
        insertion_result = await self.find_best_insertion_position(
            current_route, new_stop, profile, optimize_for, options
        )
        
        # Insert stop at best position
        updated_route = current_route.copy()
        updated_route.insert(insertion_result.best_position, new_stop)
        
        logger.info(
            f"Inserted stop '{new_stop.name}' at position {insertion_result.best_position}, "
            f"cost increase: +{insertion_result.insertion_cost:.2f} {optimize_for}"
        )
        
        return updated_route, insertion_result
    
    async def _get_or_compute_matrix(
        self,
        points: List[RoutePoint],
        profile: str,
        optimize_for: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[Tuple[int, int], float]:
        """
        Get or compute distance/time matrix for points.
        
        Uses caching to avoid redundant matrix calculations.
        Falls back to haversine distance if matrix computation fails.
        
        Returns:
            Dictionary mapping (from_idx, to_idx) to cost value
        """
        # Create cache key
        point_key = "_".join([f"{p.lat:.6f},{p.lon:.6f}" for p in points])
        cache_key = f"{point_key}_{profile}_{optimize_for}"
        
        if cache_key in self._matrix_cache:
            return self._matrix_cache[cache_key]
        
        try:
            # Try to use routing provider matrix
            matrix_result = await self.routing_provider.compute_matrix(
                points, profile=profile, options=options
            )
            
            # Convert to our format
            cost_matrix = {}
            n = len(points)
            
            for i in range(n):
                for j in range(n):
                    if optimize_for == "time":
                        cost = matrix_result.durations_min[i][j] if matrix_result.durations_min else 0.0
                    else:  # distance
                        cost = matrix_result.distances_km[i][j] if matrix_result.distances_km else 0.0
                    
                    cost_matrix[(i, j)] = cost
            
            # Cache result
            self._matrix_cache[cache_key] = cost_matrix
            return cost_matrix
            
        except Exception as e:
            logger.warning(f"Matrix computation failed, using haversine fallback: {e}")
            
            # Fallback to haversine distance
            cost_matrix = {}
            n = len(points)
            
            for i in range(n):
                for j in range(n):
                    if i == j:
                        cost_matrix[(i, j)] = 0.0
                    else:
                        distance = haversine_km(
                            points[i].lat, points[i].lon,
                            points[j].lat, points[j].lon
                        )
                        
                        if optimize_for == "time":
                            cost = estimate_travel_time_minutes(distance, profile)
                        else:
                            cost = distance
                        
                        cost_matrix[(i, j)] = cost
            
            # Cache fallback result
            self._matrix_cache[cache_key] = cost_matrix
            return cost_matrix
    
    def _calculate_best_insertion(
        self,
        current_route: List[RoutePoint],
        new_stop: RoutePoint,
        matrix: Dict[Tuple[int, int], float],
        optimize_for: str
    ) -> Tuple[int, float]:
        """
        Calculate the best position to insert new stop using matrix data.
        
        Implements the classic best insertion algorithm:
        For each position i, calculate: cost(i, new) + cost(new, i+1) - cost(i, i+1)
        
        Args:
            current_route: Current route points
            new_stop: New stop to insert
            matrix: Cost matrix for all points
            optimize_for: "time" or "distance"
            
        Returns:
            Tuple of (best_position, insertion_cost)
        """
        n = len(current_route)
        new_stop_idx = n  # New stop is last in the matrix
        
        best_position = 1  # Default to position 1 (after start)
        best_cost = float('inf')
        
        # Try inserting between each consecutive pair
        for i in range(n - 1):
            j = i + 1
            
            # Calculate insertion cost: cost(i -> new) + cost(new -> j) - cost(i -> j)
            cost_i_to_new = matrix.get((i, new_stop_idx), 0.0)
            cost_new_to_j = matrix.get((new_stop_idx, j), 0.0)
            cost_i_to_j = matrix.get((i, j), 0.0)
            
            insertion_cost = cost_i_to_new + cost_new_to_j - cost_i_to_j
            
            if insertion_cost < best_cost:
                best_cost = insertion_cost
                best_position = j  # Insert before position j
        
        return best_position, best_cost
    
    def _calculate_total_cost(
        self,
        route: List[RoutePoint],
        matrix: Dict[Tuple[int, int], float],
        optimize_for: str
    ) -> float:
        """
        Calculate total cost for a route using matrix data.
        
        Args:
            route: Route points
            matrix: Cost matrix
            optimize_for: "time" or "distance"
            
        Returns:
            Total route cost
        """
        total_cost = 0.0
        
        for i in range(len(route) - 1):
            cost = matrix.get((i, i + 1), 0.0)
            total_cost += cost
        
        return total_cost
    
    def clear_cache(self) -> None:
        """Clear the matrix cache."""
        self._matrix_cache.clear()
        logger.debug("Best insertion matrix cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        return {
            "cached_matrices": len(self._matrix_cache),
            "total_cache_size": sum(len(matrix) for matrix in self._matrix_cache.values())
        }
