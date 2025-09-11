"""
Day Route Breakdown Service

Provides detailed segment-by-segment routing for a complete day's journey.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.services.routing.base import RoutePoint, RoutingProvider
from app.services.routing import get_routing_provider
from app.schemas.route import (
    DayRouteBreakdownRequest,
    DayRouteBreakdownResponse,
    RouteSegment
)

logger = logging.getLogger(__name__)


class DayRouteBreakdownService:
    """Service for computing detailed day route breakdowns"""
    
    def __init__(self):
        self.routing_provider: RoutingProvider = get_routing_provider()
    
    async def compute_day_breakdown(
        self, 
        request: DayRouteBreakdownRequest
    ) -> DayRouteBreakdownResponse:
        """
        Compute detailed route breakdown for a complete day
        
        Args:
            request: Day route breakdown request with start, stops, and end
            
        Returns:
            Detailed breakdown with segment-by-segment routing information
        """
        logger.info(f"Computing day route breakdown for day {request.day_id}")
        
        # Build the complete journey points
        journey_points = [request.start] + request.stops + [request.end]
        
        if len(journey_points) < 2:
            raise ValueError("At least start and end points are required")
        
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


# Global service instance
day_breakdown_service = DayRouteBreakdownService()


async def compute_day_route_breakdown(
    request: DayRouteBreakdownRequest
) -> DayRouteBreakdownResponse:
    """
    Compute detailed route breakdown for a day
    
    Args:
        request: Day route breakdown request
        
    Returns:
        Detailed breakdown response
    """
    return await day_breakdown_service.compute_day_breakdown(request)
