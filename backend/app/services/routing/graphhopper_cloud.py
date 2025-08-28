"""
GraphHopper Cloud routing provider
"""
import httpx
from typing import List, Dict, Any, Optional
from shapely.geometry import LineString
import logging

from app.services.routing.base import (
    RoutingProvider,
    RoutePoint,
    RouteLeg,
    RouteResult,
    DistanceMatrix,
    RoutingRateLimitError,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class GraphHopperCloudProvider(RoutingProvider):
    """GraphHopper Cloud API routing provider"""

    def __init__(self):
        self.api_key = settings.GRAPHHOPPER_API_KEY
        self.base_url = "https://graphhopper.com/api/1"

        if not self.api_key:
            raise ValueError("GRAPHHOPPER_API_KEY is required for cloud mode")

    def build_request(
        self,
        points: List[RoutePoint],
        profile: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build request parameters for GraphHopper Cloud API"""

        # Convert points to GraphHopper format
        point_params = []
        for point in points:
            point_params.append(f"{point.lat},{point.lon}")

        params = {
            "key": self.api_key,
            "profile": profile,
            "points_encoded": False,
            "instructions": True,
            "calc_points": True,
            "debug": True,
            "elevation": False,
            "turn_costs": True if profile in ["car", "motorcycle"] else False
        }

        # Add points as repeated query params (?point=a&point=b)
        # httpx encodes list values as repeated keys
        params["point"] = point_params

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
        """Compute route using GraphHopper Cloud API"""

        if len(points) < 2:
            raise ValueError("At least 2 points are required for routing")

        if options is None:
            options = {}

        # Build request
        params = self.build_request(points, profile, options)

        # Make API request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/route",
                    params=params,
                    timeout=30.0
                )
                # If rate-limited, propagate a specific error the router can map to 429
                if response.status_code == 429:
                    raise RoutingRateLimitError("Routing provider rate limit exceeded (GraphHopper 429)")
                response.raise_for_status()
                data = response.json()

            except RoutingRateLimitError:
                # Bubble up as-is
                raise
            except httpx.HTTPError as e:
                logger.error(f"GraphHopper API error: {e}")
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

    async def compute_matrix(
        self,
        points: List[RoutePoint],
        profile: str = "car",
        options: Optional[Dict[str, Any]] = None,
    ) -> DistanceMatrix:
        """Compute distance/time matrix using GraphHopper Matrix API"""
        if len(points) < 2:
            raise ValueError("At least 2 points are required for a matrix")

        # Build points as lat,lon strings
        locs = [f"{p.lat},{p.lon}" for p in points]
        params = {
            "key": self.api_key,
            "profile": profile,
            "out_array": ["weights", "times", "distances"],
            "debug": False,
        }
        data = {"points": locs}

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/matrix",
                    params=params,
                    json=data,
                    timeout=30.0,
                )
                if resp.status_code == 429:
                    raise RoutingRateLimitError("Routing provider matrix rate limit exceeded (GraphHopper 429)")
                resp.raise_for_status()
                m = resp.json()
            except RoutingRateLimitError:
                raise
            except httpx.HTTPError as e:
                logger.error(f"GraphHopper Matrix error: {e}")
                raise Exception(f"Matrix service error: {e}")

        distances = m.get("distances") or []  # meters
        times = m.get("times") or []  # seconds

        # Convert to km and minutes
        distances_km = [[(d or 0) / 1000.0 for d in row] for row in distances]
        durations_min = [[(t or 0) / 60.0 for t in row] for row in times]
        return DistanceMatrix(distances_km=distances_km, durations_min=durations_min)