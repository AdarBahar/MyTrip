"""
GraphHopper Self-hosted routing provider
"""
import httpx
from typing import List, Dict, Any, Optional
from shapely.geometry import LineString
import logging

from app.services.routing.base import (
    RoutingProvider,
    RoutePoint,
    RouteLeg,
    RouteResult
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphHopperSelfHostProvider(RoutingProvider):
    """GraphHopper self-hosted routing provider"""

    def __init__(self):
        self.base_url = settings.GRAPHHOPPER_BASE_URL.rstrip("/")

    def build_request(
        self,
        points: List[RoutePoint],
        profile: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build request parameters for self-hosted GraphHopper"""

        # Convert points to GraphHopper format
        point_params = []
        for point in points:
            point_params.append([point.lat, point.lon])

        params = {
            "profile": profile,
            "points": point_params,
            "points_encoded": False,
            "instructions": True,
            "calc_points": True,
            "debug": True,
            "elevation": False,
            "turn_costs": True if profile in ["car", "motorcycle"] else False
        }

        # Add options
        if options:
            if "avoid_highways" in options and options["avoid_highways"]:
                params["avoid"] = "motorway"
            if "avoid_tolls" in options and options["avoid_tolls"]:
                params["avoid"] = params.get("avoid", "") + ",toll"

        return params

    async def compute_route(
        self,
        points: List[RoutePoint],
        profile: str = "car",
        options: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """Compute route using self-hosted GraphHopper"""

        if len(points) < 2:
            raise ValueError("At least 2 points are required for routing")

        if options is None:
            options = {}

        # Build request
        request_data = self.build_request(points, profile, options)

        # Make API request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/route",
                    json=request_data,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()

            except httpx.HTTPError as e:
                logger.error(f"Self-hosted GraphHopper error: {e}")
                raise Exception(f"Routing service error: {e}")

        # Parse response
        return self._parse_response(data)

    def _parse_response(self, data: Dict[str, Any]) -> RouteResult:
        """Parse GraphHopper API response"""

        if "message" in data:
            raise Exception(f"GraphHopper error: {data['message']}")

        paths = data.get("paths", [])
        if not paths:
            raise Exception("No route found")

        path = paths[0]  # Take first path

        # Extract total distance and time
        total_km = path.get("distance", 0) / 1000.0  # Convert m to km
        total_min = path.get("time", 0) / 60000.0    # Convert ms to min

        # Extract geometry
        coordinates = path.get("points", {}).get("coordinates", [])
        if not coordinates:
            raise Exception("No route geometry found")

        # Convert to LineString (GraphHopper returns [lon, lat] format)
        geometry = LineString([(coord[0], coord[1]) for coord in coordinates])

        # Extract legs
        legs = []
        instructions = path.get("instructions", [])

        # Group instructions into legs (simplified approach)
        if instructions:
            leg = RouteLeg(
                distance_km=total_km,
                duration_min=total_min,
                geometry=geometry,
                instructions=instructions,
                meta={}
            )
            legs.append(leg)

        return RouteResult(
            total_km=total_km,
            total_min=total_min,
            geometry=geometry,
            legs=legs,
            debug=data.get("info", {})
        )

    def supports_map_match(self) -> bool:
        return True

    def supports_matrix(self) -> bool:
        return True