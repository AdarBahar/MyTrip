"""
Route geometry builder service
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from shapely.geometry import LineString

from app.services.routing.base import RoutePoint, RoutingProvider
from app.schemas.route_optimization import (
    LocationRequest, 
    RouteGeometry, 
    GeometryBounds, 
    OptimizationGeometry
)

logger = logging.getLogger(__name__)


class GeometryBuilder:
    """Service for building route geometry and bounds"""
    
    def __init__(self, routing_provider: RoutingProvider):
        self.routing_provider = routing_provider
    
    async def build_route_geometry(
        self,
        ordered_locations: List[LocationRequest],
        vehicle_profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[OptimizationGeometry, List[str]]:
        """
        Build route geometry from ordered locations
        
        Args:
            ordered_locations: Ordered list of locations
            vehicle_profile: Vehicle profile for routing
            options: Additional routing options
            
        Returns:
            Tuple of (OptimizationGeometry, warnings)
        """
        warnings = []
        
        if len(ordered_locations) < 2:
            # Return empty geometry for insufficient points
            empty_geometry = OptimizationGeometry(
                format="geojson",
                route=RouteGeometry(
                    type="LineString",
                    coordinates=[]
                ),
                bounds=GeometryBounds(
                    min_lat=0.0,
                    min_lng=0.0,
                    max_lat=0.0,
                    max_lng=0.0
                )
            )
            warnings.append("Insufficient points for route geometry")
            return empty_geometry, warnings
        
        try:
            # Convert to RoutePoints
            route_points = [
                RoutePoint(lat=loc.lat, lon=loc.lng, name=loc.name)
                for loc in ordered_locations
            ]
            
            # Get route from routing provider
            route_result = await self.routing_provider.compute_route(
                route_points, vehicle_profile, options
            )
            
            # Extract coordinates from route geometry
            if route_result.geometry and hasattr(route_result.geometry, 'coords'):
                # Convert Shapely LineString to GeoJSON coordinates
                coordinates = [[coord[0], coord[1]] for coord in route_result.geometry.coords]
            else:
                # Fallback to straight lines between points
                coordinates = [[loc.lng, loc.lat] for loc in ordered_locations]
                warnings.append("Route geometry not available, using straight lines")
            
            # Calculate bounds
            bounds = self._calculate_bounds(coordinates)
            
            geometry = OptimizationGeometry(
                format="geojson",
                route=RouteGeometry(
                    type="LineString",
                    coordinates=coordinates
                ),
                bounds=bounds
            )
            
            return geometry, warnings
            
        except Exception as e:
            logger.warning(f"Failed to build route geometry: {e}")
            
            # Fallback to straight line geometry
            coordinates = [[loc.lng, loc.lat] for loc in ordered_locations]
            bounds = self._calculate_bounds(coordinates)
            
            geometry = OptimizationGeometry(
                format="geojson",
                route=RouteGeometry(
                    type="LineString",
                    coordinates=coordinates
                ),
                bounds=bounds
            )
            
            warnings.append("Route geometry service unavailable, using straight lines")
            return geometry, warnings
    
    def _calculate_bounds(self, coordinates: List[List[float]]) -> GeometryBounds:
        """Calculate bounding box for coordinates"""
        
        if not coordinates:
            return GeometryBounds(
                min_lat=0.0,
                min_lng=0.0,
                max_lat=0.0,
                max_lng=0.0
            )
        
        lngs = [coord[0] for coord in coordinates]
        lats = [coord[1] for coord in coordinates]
        
        return GeometryBounds(
            min_lat=min(lats),
            min_lng=min(lngs),
            max_lat=max(lats),
            max_lng=max(lngs)
        )
    
    def create_fallback_geometry(
        self,
        ordered_locations: List[LocationRequest]
    ) -> OptimizationGeometry:
        """Create fallback geometry using straight lines"""
        
        coordinates = [[loc.lng, loc.lat] for loc in ordered_locations]
        bounds = self._calculate_bounds(coordinates)
        
        return OptimizationGeometry(
            format="geojson",
            route=RouteGeometry(
                type="LineString",
                coordinates=coordinates
            ),
            bounds=bounds
        )
