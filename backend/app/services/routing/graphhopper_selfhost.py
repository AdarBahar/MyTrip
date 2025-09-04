"""
GraphHopper Self-hosted routing provider
"""
import httpx
from typing import List, Dict, Any, Optional
from shapely.geometry import LineString
import logging
import asyncio

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
        # We support matrix either via Cloud (hybrid) or local approximation.
        return True

    async def compute_matrix(
        self,
        points: List[RoutePoint],
        profile: str = "car",
        options: Optional[Dict[str, Any]] = None,
    ):
        """Compute a distance/time matrix.
        If USE_CLOUD_MATRIX is True, delegate to Cloud Matrix (hybrid).
        Otherwise, approximate locally using pairwise /route calls to the self-hosted server.
        """
        from app.services.routing.base import DistanceMatrix

        n = len(points)
        if n < 2:
            raise ValueError("At least 2 points are required for a matrix")

        if settings.USE_CLOUD_MATRIX:
            from app.services.routing.graphhopper_cloud import GraphHopperCloudProvider
            provider = GraphHopperCloudProvider()
            return await provider.compute_matrix(points, profile=profile, options=options)

        # Local approximation: pairwise routing for all i!=j with limited concurrency
        distances_km = [[0.0 for _ in range(n)] for _ in range(n)]
        durations_min = [[0.0 for _ in range(n)] for _ in range(n)]

        sem = asyncio.Semaphore(4)

        async def compute_pair(i: int, j: int):
            if i == j:
                return
            payload = {
                "profile": profile,
                "points": [
                    [points[i].lat, points[i].lon],
                    [points[j].lat, points[j].lon],
                ],
                "points_encoded": False,
                "instructions": False,
                "calc_points": False,
                "debug": False,
                "elevation": False,
                "turn_costs": True if profile in ["car", "motorcycle"] else False,
            }
            async with sem:
                async with httpx.AsyncClient() as client:  # type: ignore[name-defined]
                    try:
                        resp = await client.post(
                            f"{self.base_url}/route",
                            json=payload,
                            timeout=20.0,
                        )
                        resp.raise_for_status()
                        d = resp.json()
                        paths = d.get("paths") or []
                        if not paths:
                            return
                        p0 = paths[0]
                        distances_km[i][j] = (p0.get("distance") or 0) / 1000.0
                        durations_min[i][j] = (p0.get("time") or 0) / 60000.0
                    except Exception as e:
                        logger.warning(f"Local matrix pair ({i},{j}) failed: {e}")
                        # leave zeros
                        return

        tasks = [compute_pair(i, j) for i in range(n) for j in range(n) if i != j]
        await asyncio.gather(*tasks)

        return DistanceMatrix(distances_km=distances_km, durations_min=durations_min)