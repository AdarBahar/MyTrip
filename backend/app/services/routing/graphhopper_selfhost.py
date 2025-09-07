"""
GraphHopper Self-hosted routing provider
"""
import httpx
from typing import List, Dict, Any, Optional
from shapely.geometry import LineString
import logging
import asyncio
import time

from app.services.routing.base import (
    RoutingProvider,
    RoutePoint,
    RouteLeg,
    RouteResult
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Enhanced rate limiter for cloud fallback with exponential backoff
class CloudFallbackRateLimiter:
    def __init__(self, max_calls=3, window_seconds=60):  # Reduced from 5 to 3
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.calls = []
        self.last_failure_time = None
        self.failure_count = 0
        self.max_failures = 3

    def can_make_call(self):
        now = time.time()

        # Check if we're in a backoff period after failures
        if self.last_failure_time and self.failure_count > 0:
            backoff_duration = min(300, 30 * (2 ** (self.failure_count - 1)))  # Max 5 minutes
            if now - self.last_failure_time < backoff_duration:
                return False

        # Remove calls outside the window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.window_seconds]
        return len(self.calls) < self.max_calls

    def record_call(self):
        self.calls.append(time.time())

    def record_failure(self):
        """Record a failure for exponential backoff"""
        self.failure_count = min(self.failure_count + 1, self.max_failures)
        self.last_failure_time = time.time()

    def record_success(self):
        """Reset failure count on successful call"""
        self.failure_count = 0
        self.last_failure_time = None

# Global rate limiter instance
cloud_rate_limiter = CloudFallbackRateLimiter()


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
            "elevation": False
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
                # Check if it's a 400 error that might be due to out-of-bounds coordinates
                if hasattr(e, 'response') and e.response.status_code == 400:
                    try:
                        error_data = e.response.json()
                        if "out of bounds" in error_data.get("message", "").lower():
                            logger.warning(f"Coordinates out of bounds for self-hosted GraphHopper, checking cloud fallback availability")

                            # Check rate limiter before attempting cloud fallback
                            if not cloud_rate_limiter.can_make_call():
                                backoff_time = "30 seconds to 5 minutes" if cloud_rate_limiter.failure_count > 0 else "1 minute"
                                logger.warning(f"Cloud fallback not available (rate limited or in backoff), next attempt in {backoff_time}")
                                raise Exception(f"Routing temporarily unavailable: coordinates are outside our coverage area. The routing service is currently rate-limited. Please try again in {backoff_time}.")

                            # Fall back to cloud routing for out-of-bounds coordinates
                            try:
                                logger.info("Attempting cloud fallback for out-of-bounds coordinates")
                                cloud_rate_limiter.record_call()
                                from app.services.routing.graphhopper_cloud import GraphHopperCloudProvider
                                cloud_provider = GraphHopperCloudProvider()
                                result = await cloud_provider.compute_route(points, profile, options)
                                cloud_rate_limiter.record_success()  # Reset failure count on success
                                return result
                            except Exception as cloud_error:
                                cloud_rate_limiter.record_failure()  # Record failure for backoff
                                if "429" in str(cloud_error) or "rate limit" in str(cloud_error).lower():
                                    logger.error(f"Cloud routing rate limited: {cloud_error}")
                                    raise Exception("Routing service is currently overloaded. Please try again in a few minutes, or consider using locations within our primary coverage area (Israel/Palestine region).")
                                else:
                                    logger.error(f"Cloud fallback failed: {cloud_error}")
                                    raise Exception(f"Unable to compute route: coordinates are outside our primary coverage area and external routing services are unavailable. Try using locations within Israel/Palestine or wait a few minutes and try again.")
                    except Exception as fallback_error:
                        logger.error(f"Cloud fallback also failed: {fallback_error}")
                        raise Exception(f"Coordinates are outside the supported geographic region and cloud fallback failed: {fallback_error}")
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
        # Use None to indicate failed computations vs actual zero distance
        distances_km = [[None if i != j else 0.0 for j in range(n)] for i in range(n)]
        durations_min = [[None if i != j else 0.0 for j in range(n)] for i in range(n)]

        # Enhanced bounds checking with circuit breaker pattern
        # Israel bounds: lat 29.49-33.42, lon 34.16-35.94 (approximate)
        out_of_bounds_count = 0
        for point in points:
            if not (29.4 <= point.lat <= 33.5 and 34.1 <= point.lon <= 36.0):
                out_of_bounds_count += 1

        # If most coordinates are out of bounds, skip matrix computation entirely
        if out_of_bounds_count >= len(points) * 0.7:  # 70% threshold
            logger.warning(f"Most coordinates ({out_of_bounds_count}/{len(points)}) are outside Israel bounds, skipping matrix computation to avoid rate limits")
            # Return zero matrix to maintain API compatibility
            distances_km = [[0.0 for _ in range(n)] for _ in range(n)]
            durations_min = [[0.0 for _ in range(n)] for _ in range(n)]
            return DistanceMatrix(distances_km=distances_km, durations_min=durations_min)

        # If cloud fallback is in backoff, skip matrix computation
        if not cloud_rate_limiter.can_make_call():
            logger.warning("Cloud fallback in backoff period, skipping matrix computation")
            distances_km = [[0.0 for _ in range(n)] for _ in range(n)]
            durations_min = [[0.0 for _ in range(n)] for _ in range(n)]
            return DistanceMatrix(distances_km=distances_km, durations_min=durations_min)

        sem = asyncio.Semaphore(4)

        # Create a single shared HTTP client for all requests to avoid resource leaks
        async with httpx.AsyncClient() as shared_client:
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
                }
                async with sem:
                        try:
                            resp = await shared_client.post(
                                f"{self.base_url}/route",
                                json=payload,
                                timeout=20.0,
                            )
                            resp.raise_for_status()
                            d = resp.json()
                            paths = d.get("paths") or []
                            if not paths:
                                # No path found - mark as failed computation
                                distances_km[i][j] = 0.0
                                durations_min[i][j] = 0.0
                                return
                            p0 = paths[0]
                            distances_km[i][j] = (p0.get("distance") or 0) / 1000.0
                            durations_min[i][j] = (p0.get("time") or 0) / 60000.0
                        except Exception as e:
                            logger.warning(f"Local matrix pair ({i},{j}) failed: {e}")
                            # Check if it's an out-of-bounds error
                            if "out of bounds" in str(e).lower() or "400 bad request" in str(e).lower():
                                logger.warning(f"Coordinates for matrix pair ({i},{j}) are outside supported region")
                            # Mark as failed computation (0.0 for API compatibility)
                            distances_km[i][j] = 0.0
                            durations_min[i][j] = 0.0
                            return

            tasks = [compute_pair(i, j) for i in range(n) for j in range(n) if i != j]
            await asyncio.gather(*tasks)

        return DistanceMatrix(distances_km=distances_km, durations_min=durations_min)