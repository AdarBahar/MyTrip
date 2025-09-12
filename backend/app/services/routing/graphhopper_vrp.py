"""
GraphHopper VRP (Vehicle Routing Problem) provider for professional route optimization.

This module implements the GraphHopper Route Optimization API for advanced
TSP/VRP solving with support for vehicles, services, relations, and constraints.
"""
import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, List
import httpx

from app.services.routing.base import RoutePoint
from app.services.routing.optimization import OptimizationResult
from app.core.config import settings
from app.exceptions.routing import RouteProviderError, RouteOptimizationError

logger = logging.getLogger(__name__)


class GraphHopperVRPProvider:
    """
    GraphHopper VRP API provider for professional route optimization.
    
    Uses GraphHopper's Route Optimization API which implements advanced
    TSP/VRP algorithms with support for:
    - Multiple vehicles and profiles
    - Service constraints and time windows
    - Relations for partial ordering (in_sequence, in_direct_sequence)
    - Priorities and capacities
    - Async job processing for large problems
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize VRP provider.
        
        Args:
            api_key: GraphHopper API key (defaults to settings)
            base_url: GraphHopper base URL (defaults to cloud API)
        """
        self.api_key = api_key or settings.GRAPHHOPPER_API_KEY
        self.base_url = base_url or "https://graphhopper.com/api/1"
        
        if not self.api_key:
            raise ValueError("GraphHopper API key is required for VRP optimization")
    
    async def optimize_route_vrp(
        self,
        start: RoutePoint,
        stops: List[RoutePoint],
        end: RoutePoint,
        profile: str = "car",
        fixed_indices: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Optimize route using GraphHopper VRP API.
        
        Args:
            start: Starting point (fixed)
            stops: List of stops to optimize
            end: Ending point (fixed)
            profile: Routing profile (car, bike, etc.)
            fixed_indices: Indices of stops that cannot be moved
            options: Additional optimization options
            
        Returns:
            OptimizationResult with optimized order and metrics
            
        Raises:
            RouteOptimizationError: If VRP optimization fails
            RouteProviderError: If API communication fails
        """
        if not stops:
            # No stops to optimize
            original_points = [start, end]
            return OptimizationResult(
                optimized_points=original_points,
                original_distance_km=0.0,
                optimized_distance_km=0.0,
                original_duration_min=0.0,
                optimized_duration_min=0.0
            )
        
        try:
            # Build VRP request
            vrp_request = self._build_vrp_request(
                start, stops, end, profile, fixed_indices, options
            )
            
            # Submit VRP job
            job_id = await self._submit_vrp_job(vrp_request)
            
            # Poll for completion
            vrp_solution = await self._poll_vrp_solution(job_id)
            
            # Parse solution and calculate metrics
            return await self._parse_vrp_solution(
                vrp_solution, start, stops, end, profile, options
            )
            
        except Exception as e:
            logger.error(f"VRP optimization failed: {e}")
            if isinstance(e, (RouteOptimizationError, RouteProviderError)):
                raise
            raise RouteOptimizationError(
                f"VRP optimization failed: {str(e)}",
                strategy="graphhopper_vrp",
                fallback_available=True
            )
    
    def _build_vrp_request(
        self,
        start: RoutePoint,
        stops: List[RoutePoint],
        end: RoutePoint,
        profile: str,
        fixed_indices: Optional[List[int]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build GraphHopper VRP request payload.
        
        Creates a VRP request with:
        - One vehicle with start/end addresses
        - Each stop as a service
        - Relations for fixed ordering constraints
        - Optimization objective (minimize completion time)
        """
        vehicle_id = f"vehicle_{uuid.uuid4().hex[:8]}"
        
        # Build vehicle definition
        vehicle = {
            "vehicle_id": vehicle_id,
            "profile": profile,
            "start_address": {
                "lat": start.lat,
                "lon": start.lon
            },
            "end_address": {
                "lat": end.lat,
                "lon": end.lon
            }
        }
        
        # Add vehicle constraints from options
        if options:
            if "max_distance" in options:
                vehicle["max_distance"] = options["max_distance"]
            if "max_driving_time" in options:
                vehicle["max_driving_time"] = options["max_driving_time"]
        
        # Build services (stops)
        services = []
        for i, stop in enumerate(stops):
            service = {
                "id": f"stop_{i}",
                "name": stop.name,
                "address": {
                    "lat": stop.lat,
                    "lon": stop.lon
                },
                "duration": 300,  # 5 minutes default stop duration
                "priority": 1
            }
            
            # Add service-specific options
            if options and "stop_durations" in options:
                if i < len(options["stop_durations"]):
                    service["duration"] = options["stop_durations"][i]
            
            services.append(service)
        
        # Build relations for fixed ordering
        relations = []
        if fixed_indices:
            # Create in_sequence relation for fixed stops
            fixed_service_ids = [f"stop_{i}" for i in fixed_indices]
            if len(fixed_service_ids) > 1:
                relations.append({
                    "type": "in_sequence",
                    "ids": fixed_service_ids
                })
        
        # Build configuration
        configuration = {
            "routing": {
                "profile": profile
            },
            "objectives": [
                {
                    "type": "min",
                    "value": "completion_time"
                }
            ]
        }
        
        # Add optimization options
        if options:
            if "optimization_timeout" in options:
                configuration["solver"] = {
                    "max_runtime": options["optimization_timeout"]
                }
        
        return {
            "vehicles": [vehicle],
            "services": services,
            "relations": relations,
            "configuration": configuration
        }
    
    async def _submit_vrp_job(self, vrp_request: Dict[str, Any]) -> str:
        """
        Submit VRP optimization job to GraphHopper.
        
        Returns:
            Job ID for polling solution
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/vrp",
                    params={"key": self.api_key},
                    json=vrp_request,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                job_id = data.get("job_id")
                if not job_id:
                    raise RouteProviderError(
                        "No job_id returned from VRP API",
                        provider="graphhopper_vrp"
                    )
                
                logger.info(f"VRP job submitted: {job_id}")
                return job_id
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RouteProviderError(
                        "VRP API rate limit exceeded",
                        provider="graphhopper_vrp",
                        status_code=429,
                        is_recoverable=True
                    )
                elif e.response.status_code >= 400:
                    error_data = e.response.json() if e.response.content else {}
                    raise RouteProviderError(
                        f"VRP API error: {error_data.get('message', str(e))}",
                        provider="graphhopper_vrp",
                        status_code=e.response.status_code
                    )
                raise
            except Exception as e:
                raise RouteProviderError(
                    f"Failed to submit VRP job: {str(e)}",
                    provider="graphhopper_vrp"
                )
    
    async def _poll_vrp_solution(
        self, 
        job_id: str, 
        max_wait_seconds: int = 60,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """
        Poll VRP job until completion.
        
        Args:
            job_id: VRP job ID
            max_wait_seconds: Maximum time to wait for completion
            poll_interval: Seconds between polling attempts
            
        Returns:
            VRP solution data
        """
        start_time = asyncio.get_event_loop().time()
        
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.base_url}/vrp/solution/{job_id}",
                        params={"key": self.api_key},
                        timeout=10.0
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    status = data.get("status")
                    
                    if status == "finished":
                        logger.info(f"VRP job {job_id} completed successfully")
                        return data
                    elif status == "failed":
                        error_msg = data.get("message", "VRP optimization failed")
                        raise RouteOptimizationError(
                            f"VRP job failed: {error_msg}",
                            strategy="graphhopper_vrp"
                        )
                    elif status in ["waiting", "processing"]:
                        # Job still running, continue polling
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > max_wait_seconds:
                            raise RouteOptimizationError(
                                f"VRP job {job_id} timed out after {max_wait_seconds}s",
                                strategy="graphhopper_vrp"
                            )
                        
                        logger.debug(f"VRP job {job_id} status: {status}, waiting...")
                        await asyncio.sleep(poll_interval)
                    else:
                        raise RouteOptimizationError(
                            f"Unknown VRP job status: {status}",
                            strategy="graphhopper_vrp"
                        )
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        raise RouteOptimizationError(
                            f"VRP job {job_id} not found",
                            strategy="graphhopper_vrp"
                        )
                    raise RouteProviderError(
                        f"Error polling VRP job: {e}",
                        provider="graphhopper_vrp",
                        status_code=e.response.status_code
                    )
                except Exception as e:
                    raise RouteProviderError(
                        f"Failed to poll VRP solution: {str(e)}",
                        provider="graphhopper_vrp"
                    )

    async def _parse_vrp_solution(
        self,
        vrp_solution: Dict[str, Any],
        start: RoutePoint,
        stops: List[RoutePoint],
        end: RoutePoint,
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Parse VRP solution and calculate optimization metrics.

        Args:
            vrp_solution: VRP solution from GraphHopper
            start: Original start point
            stops: Original stops list
            end: Original end point
            profile: Routing profile
            options: Additional options

        Returns:
            OptimizationResult with optimized order and metrics
        """
        try:
            solution = vrp_solution.get("solution", {})
            routes = solution.get("routes", [])

            if not routes:
                raise RouteOptimizationError(
                    "No routes found in VRP solution",
                    strategy="graphhopper_vrp"
                )

            # Get the first (and should be only) route
            route = routes[0]
            activities = route.get("activities", [])

            # Parse optimized order from activities
            optimized_points = [start]  # Always start with start point

            # Extract service activities (excluding start/end)
            service_activities = [
                act for act in activities
                if act.get("type") == "service"
            ]

            # Map service IDs back to original stops
            for activity in service_activities:
                service_id = activity.get("id", "")
                if service_id.startswith("stop_"):
                    try:
                        stop_index = int(service_id.split("_")[1])
                        if 0 <= stop_index < len(stops):
                            optimized_points.append(stops[stop_index])
                    except (ValueError, IndexError):
                        logger.warning(f"Invalid service ID in VRP solution: {service_id}")

            optimized_points.append(end)  # Always end with end point

            # Calculate original route metrics
            original_points = [start] + stops + [end]
            original_distance, original_duration = await self._calculate_route_metrics(
                original_points, profile, options
            )

            # Calculate optimized route metrics
            optimized_distance, optimized_duration = await self._calculate_route_metrics(
                optimized_points, profile, options
            )

            # Extract VRP solution metrics if available
            solution_stats = solution.get("costs", {})
            if solution_stats:
                # Use VRP solution metrics if available (more accurate)
                optimized_distance = solution_stats.get("distance", optimized_distance) / 1000.0  # Convert to km
                optimized_duration = solution_stats.get("time", optimized_duration) / 60.0  # Convert to minutes

            logger.info(
                f"VRP optimization completed: {len(stops)} stops, "
                f"distance: {original_distance:.2f}km -> {optimized_distance:.2f}km "
                f"({((original_distance - optimized_distance) / original_distance * 100):.1f}% improvement)"
            )

            return OptimizationResult(
                optimized_points=optimized_points,
                original_distance_km=original_distance,
                optimized_distance_km=optimized_distance,
                original_duration_min=original_duration,
                optimized_duration_min=optimized_duration
            )

        except Exception as e:
            if isinstance(e, RouteOptimizationError):
                raise
            raise RouteOptimizationError(
                f"Failed to parse VRP solution: {str(e)}",
                strategy="graphhopper_vrp"
            )

    async def _calculate_route_metrics(
        self,
        points: List[RoutePoint],
        profile: str,
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[float, float]:
        """
        Calculate total distance and duration for a route.

        Uses GraphHopper routing API to get accurate metrics.
        Falls back to haversine distance if routing fails.

        Returns:
            Tuple of (total_distance_km, total_duration_min)
        """
        if len(points) < 2:
            return 0.0, 0.0

        try:
            # Use GraphHopper routing API for accurate calculation
            from app.services.routing import get_routing_provider
            provider = get_routing_provider()

            route_result = await provider.compute_route(
                points, profile=profile, options=options
            )

            return route_result.total_distance_km, route_result.total_duration_min

        except Exception as e:
            logger.warning(f"Route calculation failed, using fallback: {e}")

            # Fallback to haversine + estimated time
            from app.utils.geometry import haversine_km, estimate_travel_time_minutes

            total_distance = 0.0
            for i in range(len(points) - 1):
                distance = haversine_km(
                    points[i].lat, points[i].lon,
                    points[i + 1].lat, points[i + 1].lon
                )
                total_distance += distance

            total_duration = estimate_travel_time_minutes(total_distance, profile)
            return total_distance, total_duration
