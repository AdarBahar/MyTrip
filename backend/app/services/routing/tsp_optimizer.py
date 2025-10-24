"""
TSP-based route optimization service
"""
import logging
import math
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

from app.services.routing.base import RoutePoint, RoutingProvider, DistanceMatrix
from app.schemas.route_optimization import LocationRequest, LocationType, Objective

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of route optimization"""
    ordered_locations: List[LocationRequest]
    total_distance_km: float
    total_duration_min: float
    leg_distances_km: List[float]
    leg_durations_min: List[float]
    computation_notes: List[str]


class TSPOptimizer:
    """TSP-based route optimizer using nearest neighbor + 2-opt"""
    
    def __init__(self, routing_provider: RoutingProvider):
        self.routing_provider = routing_provider
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance in kilometers"""
        R = 6371.0  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    async def optimize_route(
        self,
        locations: List[LocationRequest],
        objective: Objective,
        vehicle_profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Optimize route order using TSP algorithms
        
        Args:
            locations: List of locations to optimize
            objective: Optimization objective (time or distance)
            vehicle_profile: Vehicle profile for routing
            options: Additional routing options
            
        Returns:
            OptimizationResult with optimized order
        """
        computation_notes = []
        
        # Separate locations by type
        start_loc = next(loc for loc in locations if loc.type == LocationType.START)
        end_loc = next(loc for loc in locations if loc.type == LocationType.END)
        stops = [loc for loc in locations if loc.type == LocationType.STOP]
        
        # Separate fixed and flexible stops
        fixed_stops = [(i, stop) for i, stop in enumerate(stops) if stop.fixed_seq]
        flexible_stops = [stop for stop in stops if not stop.fixed_seq]
        
        computation_notes.append(f"Optimizing {len(flexible_stops)} flexible stops with {len(fixed_stops)} fixed stops")
        
        # If no flexible stops, just arrange by sequence
        if not flexible_stops:
            ordered_stops = self._arrange_fixed_stops(stops)
            computation_notes.append("No flexible stops to optimize")
        else:
            # Use TSP optimization for flexible stops
            ordered_stops = await self._optimize_with_tsp(
                start_loc, stops, end_loc, objective, vehicle_profile, options
            )
            computation_notes.append("Applied TSP optimization with nearest neighbor + 2-opt")
        
        # Build final ordered list
        ordered_locations = [start_loc] + ordered_stops + [end_loc]
        
        # Calculate route metrics
        total_distance, total_duration, leg_distances, leg_durations = await self._calculate_route_metrics(
            ordered_locations, vehicle_profile, options
        )
        
        return OptimizationResult(
            ordered_locations=ordered_locations,
            total_distance_km=total_distance,
            total_duration_min=total_duration,
            leg_distances_km=leg_distances,
            leg_durations_min=leg_durations,
            computation_notes=computation_notes
        )
    
    def _arrange_fixed_stops(self, stops: List[LocationRequest]) -> List[LocationRequest]:
        """Arrange stops by their fixed sequence numbers"""
        return sorted(stops, key=lambda s: s.seq if s.seq is not None else float('inf'))
    
    async def _optimize_with_tsp(
        self,
        start_loc: LocationRequest,
        stops: List[LocationRequest],
        end_loc: LocationRequest,
        objective: Objective,
        vehicle_profile: str,
        options: Optional[Dict[str, Any]]
    ) -> List[LocationRequest]:
        """Optimize flexible stops using TSP algorithms"""
        
        # Separate fixed and flexible stops
        fixed_stops = {stop.seq: stop for stop in stops if stop.fixed_seq and stop.seq is not None}
        flexible_stops = [stop for stop in stops if not stop.fixed_seq]
        
        if not flexible_stops:
            # Only fixed stops, arrange by sequence
            return self._arrange_fixed_stops(stops)
        
        # Create distance matrix for all locations
        all_locations = [start_loc] + stops + [end_loc]
        try:
            matrix = await self._get_distance_matrix(all_locations, vehicle_profile, options, objective)
        except Exception as e:
            logger.warning(f"Failed to get routing matrix, falling back to haversine: {e}")
            matrix = self._create_haversine_matrix(all_locations, objective)
        
        # Apply nearest neighbor + 2-opt for flexible stops
        optimized_flexible = self._nearest_neighbor_with_2opt(
            flexible_stops, matrix, all_locations, objective
        )
        
        # Merge fixed and optimized flexible stops
        return self._merge_fixed_and_flexible(fixed_stops, optimized_flexible, len(stops))
    
    async def _get_distance_matrix(
        self,
        locations: List[LocationRequest],
        vehicle_profile: str,
        options: Optional[Dict[str, Any]],
        objective: Objective
    ) -> Dict[Tuple[int, int], float]:
        """Get distance/time matrix from routing provider"""
        
        # Convert to RoutePoints
        route_points = [
            RoutePoint(lat=loc.lat, lon=loc.lng, name=loc.name)
            for loc in locations
        ]
        
        # Get matrix from routing provider
        if self.routing_provider.supports_matrix():
            matrix_result = await self.routing_provider.compute_matrix(
                route_points, vehicle_profile, options
            )
            
            # Convert to our format
            result = {}
            for i in range(len(locations)):
                for j in range(len(locations)):
                    if objective == Objective.DISTANCE:
                        result[(i, j)] = matrix_result.distances_km[i][j]
                    else:  # TIME
                        result[(i, j)] = matrix_result.durations_min[i][j]
            
            return result
        else:
            # Fallback to haversine
            return self._create_haversine_matrix(locations, objective)
    
    def _create_haversine_matrix(
        self,
        locations: List[LocationRequest],
        objective: Objective
    ) -> Dict[Tuple[int, int], float]:
        """Create distance matrix using haversine distance"""
        
        matrix = {}
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations):
                if i == j:
                    matrix[(i, j)] = 0.0
                else:
                    distance_km = self.haversine_distance(loc1.lat, loc1.lng, loc2.lat, loc2.lng)
                    if objective == Objective.DISTANCE:
                        matrix[(i, j)] = distance_km
                    else:  # TIME - estimate time based on distance
                        # Rough estimate: 50 km/h average speed
                        matrix[(i, j)] = distance_km / 50.0 * 60.0  # minutes
        
        return matrix
    
    def _nearest_neighbor_with_2opt(
        self,
        flexible_stops: List[LocationRequest],
        matrix: Dict[Tuple[int, int], float],
        all_locations: List[LocationRequest],
        objective: Objective
    ) -> List[LocationRequest]:
        """Apply nearest neighbor + 2-opt optimization"""
        
        if len(flexible_stops) <= 1:
            return flexible_stops
        
        # Create mapping from locations to matrix indices
        location_to_index = {id(loc): i for i, loc in enumerate(all_locations)}
        
        # Nearest neighbor construction
        tour = self._nearest_neighbor_tour(flexible_stops, matrix, location_to_index)
        
        # 2-opt improvement
        improved_tour = self._two_opt_improvement(tour, matrix, location_to_index)
        
        return improved_tour
    
    def _nearest_neighbor_tour(
        self,
        stops: List[LocationRequest],
        matrix: Dict[Tuple[int, int], float],
        location_to_index: Dict[int, int]
    ) -> List[LocationRequest]:
        """Construct initial tour using nearest neighbor"""

        if not stops:
            return []

        tour = [stops[0]]
        # Use list instead of set since LocationRequest objects are not hashable
        remaining = list(stops[1:])

        while remaining:
            current = tour[-1]
            current_idx = location_to_index[id(current)]

            # Find nearest unvisited stop
            nearest = min(
                remaining,
                key=lambda stop: matrix.get((current_idx, location_to_index[id(stop)]), float('inf'))
            )

            tour.append(nearest)
            remaining.remove(nearest)

        return tour
    
    def _two_opt_improvement(
        self,
        tour: List[LocationRequest],
        matrix: Dict[Tuple[int, int], float],
        location_to_index: Dict[int, int]
    ) -> List[LocationRequest]:
        """Improve tour using 2-opt swaps"""
        
        if len(tour) < 4:
            return tour
        
        improved = True
        current_tour = tour[:]
        
        while improved:
            improved = False
            
            for i in range(len(current_tour) - 2):
                for j in range(i + 2, len(current_tour)):
                    # Try 2-opt swap
                    new_tour = current_tour[:]
                    new_tour[i+1:j+1] = reversed(new_tour[i+1:j+1])
                    
                    if self._tour_cost(new_tour, matrix, location_to_index) < self._tour_cost(current_tour, matrix, location_to_index):
                        current_tour = new_tour
                        improved = True
                        break
                
                if improved:
                    break
        
        return current_tour
    
    def _tour_cost(
        self,
        tour: List[LocationRequest],
        matrix: Dict[Tuple[int, int], float],
        location_to_index: Dict[int, int]
    ) -> float:
        """Calculate total cost of a tour"""
        
        if len(tour) < 2:
            return 0.0
        
        total_cost = 0.0
        for i in range(len(tour) - 1):
            from_idx = location_to_index[id(tour[i])]
            to_idx = location_to_index[id(tour[i + 1])]
            total_cost += matrix.get((from_idx, to_idx), 0.0)
        
        return total_cost
    
    def _merge_fixed_and_flexible(
        self,
        fixed_stops: Dict[int, LocationRequest],
        flexible_stops: List[LocationRequest],
        total_stops: int
    ) -> List[LocationRequest]:
        """Merge fixed and flexible stops into final order"""
        
        result = [None] * total_stops
        flexible_iter = iter(flexible_stops)
        
        # Place fixed stops at their positions
        for seq, stop in fixed_stops.items():
            if 1 <= seq <= total_stops:
                result[seq - 1] = stop
        
        # Fill remaining positions with flexible stops
        for i in range(total_stops):
            if result[i] is None:
                try:
                    result[i] = next(flexible_iter)
                except StopIteration:
                    break
        
        # Filter out None values and return
        return [stop for stop in result if stop is not None]
    
    async def _calculate_route_metrics(
        self,
        ordered_locations: List[LocationRequest],
        vehicle_profile: str,
        options: Optional[Dict[str, Any]]
    ) -> Tuple[float, float, List[float], List[float]]:
        """Calculate route metrics for ordered locations"""
        
        if len(ordered_locations) < 2:
            return 0.0, 0.0, [], []
        
        # Convert to RoutePoints
        route_points = [
            RoutePoint(lat=loc.lat, lon=loc.lng, name=loc.name)
            for loc in ordered_locations
        ]
        
        try:
            # Try to get actual route
            route_result = await self.routing_provider.compute_route(
                route_points, vehicle_profile, options
            )
            
            # Calculate leg metrics from route legs
            leg_distances = []
            leg_durations = []
            
            if route_result.legs:
                for leg in route_result.legs:
                    leg_distances.append(leg.distance_km)
                    leg_durations.append(leg.duration_min)
            else:
                # Fallback to haversine estimates
                for i in range(len(ordered_locations) - 1):
                    loc1, loc2 = ordered_locations[i], ordered_locations[i + 1]
                    distance = self.haversine_distance(loc1.lat, loc1.lng, loc2.lat, loc2.lng)
                    leg_distances.append(distance)
                    leg_durations.append(distance / 50.0 * 60.0)  # 50 km/h estimate
            
            return route_result.total_km, route_result.total_min, leg_distances, leg_durations
            
        except Exception as e:
            logger.warning(f"Failed to calculate route metrics, using haversine: {e}")
            
            # Fallback to haversine calculations
            total_distance = 0.0
            total_duration = 0.0
            leg_distances = []
            leg_durations = []
            
            for i in range(len(ordered_locations) - 1):
                loc1, loc2 = ordered_locations[i], ordered_locations[i + 1]
                distance = self.haversine_distance(loc1.lat, loc1.lng, loc2.lat, loc2.lng)
                duration = distance / 50.0 * 60.0  # 50 km/h estimate
                
                leg_distances.append(distance)
                leg_durations.append(duration)
                total_distance += distance
                total_duration += duration
            
            return total_distance, total_duration, leg_distances, leg_durations
