"""
Best Insertion API endpoints for fast route optimization.

Provides endpoints for interactive route editing with instant feedback
when adding stops to existing routes.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
import logging

from app.schemas.route import RoutePoint as RoutePointSchema
from app.services.routing.base import RoutePoint
from app.services.routing.optimization import RouteOptimizer
from app.services.routing import get_routing_provider
from app.exceptions.routing import RouteCalculationError, RouteOptimizationError
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class BestInsertionRequest:
    """Request model for best insertion optimization."""
    
    def __init__(
        self,
        current_route: List[RoutePointSchema],
        new_stop: RoutePointSchema,
        profile: str = "car",
        optimize_for: str = "time",
        options: Optional[Dict[str, Any]] = None
    ):
        self.current_route = current_route
        self.new_stop = new_stop
        self.profile = profile
        self.optimize_for = optimize_for
        self.options = options or {}


class BestInsertionResponse:
    """Response model for best insertion optimization."""
    
    def __init__(
        self,
        optimized_route: List[RoutePointSchema],
        insertion_metrics: Dict[str, Any],
        success: bool = True,
        message: Optional[str] = None
    ):
        self.optimized_route = optimized_route
        self.insertion_metrics = insertion_metrics
        self.success = success
        self.message = message


@router.post("/best-insertion", response_model=Dict[str, Any])
async def optimize_route_with_best_insertion(
    request_data: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """
    Insert a new stop at the optimal position using best insertion algorithm.
    
    This endpoint provides O(n) route optimization for interactive UI,
    giving instant feedback when users add stops to existing routes.
    
    Args:
        request_data: Best insertion request data
        current_user: Current authenticated user
        
    Returns:
        Optimized route with insertion metrics
        
    Raises:
        HTTPException: If optimization fails
    """
    try:
        # Parse request
        current_route_data = request_data.get("current_route", [])
        new_stop_data = request_data.get("new_stop")
        profile = request_data.get("profile", "car")
        optimize_for = request_data.get("optimize_for", "time")
        options = request_data.get("options", {})
        
        if not current_route_data:
            raise HTTPException(
                status_code=400,
                detail="Current route must contain at least start and end points"
            )
        
        if not new_stop_data:
            raise HTTPException(
                status_code=400,
                detail="New stop data is required"
            )
        
        # Convert to RoutePoint objects
        current_route = [
            RoutePoint(
                lat=point["lat"],
                lon=point["lon"],
                name=point.get("name", f"Point {i}")
            )
            for i, point in enumerate(current_route_data)
        ]
        
        new_stop = RoutePoint(
            lat=new_stop_data["lat"],
            lon=new_stop_data["lon"],
            name=new_stop_data.get("name", "New Stop")
        )
        
        # Validate coordinates
        for point in current_route + [new_stop]:
            if not (-90 <= point.lat <= 90) or not (-180 <= point.lon <= 180):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid coordinates: lat={point.lat}, lon={point.lon}"
                )
        
        # Validate optimize_for parameter
        if optimize_for not in ["time", "distance"]:
            raise HTTPException(
                status_code=400,
                detail="optimize_for must be 'time' or 'distance'"
            )
        
        # Initialize optimizer
        routing_provider = get_routing_provider()
        optimizer = RouteOptimizer(routing_provider)
        
        # Perform best insertion optimization
        logger.info(
            f"Performing best insertion for user {current_user}: "
            f"{len(current_route)} points + 1 new stop, optimize_for={optimize_for}"
        )
        
        optimized_route, insertion_metrics = await optimizer.insert_stop_optimally(
            current_route=current_route,
            new_stop=new_stop,
            profile=profile,
            optimize_for=optimize_for,
            options=options
        )
        
        # Convert back to response format
        optimized_route_data = [
            {
                "lat": point.lat,
                "lon": point.lon,
                "name": point.name
            }
            for point in optimized_route
        ]
        
        logger.info(
            f"Best insertion completed: inserted at position {insertion_metrics['insertion_position']}, "
            f"cost increase: +{insertion_metrics['insertion_cost']:.2f} {optimize_for}"
        )
        
        return {
            "success": True,
            "optimized_route": optimized_route_data,
            "insertion_metrics": insertion_metrics,
            "message": f"Stop inserted at optimal position {insertion_metrics['insertion_position']}"
        }
        
    except RouteCalculationError as e:
        logger.error(f"Route calculation error in best insertion: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Route calculation failed: {e.user_message}"
        )
    except RouteOptimizationError as e:
        logger.error(f"Route optimization error in best insertion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {e.user_message}"
        )
    except ValueError as e:
        logger.error(f"Validation error in best insertion: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in best insertion: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during route optimization"
        )


@router.get("/insertion-preview")
async def preview_best_insertion_positions(
    current_route: str,  # JSON string of route points
    new_stop: str,       # JSON string of new stop
    profile: str = "car",
    optimize_for: str = "time",
    current_user: str = Depends(get_current_user)
):
    """
    Preview insertion costs for all possible positions.
    
    This endpoint calculates the cost of inserting a new stop at each
    possible position in the route, useful for UI visualization.
    
    Args:
        current_route: JSON string of current route points
        new_stop: JSON string of new stop data
        profile: Routing profile
        optimize_for: "time" or "distance"
        current_user: Current authenticated user
        
    Returns:
        List of insertion costs for each position
    """
    try:
        import json
        
        # Parse JSON parameters
        current_route_data = json.loads(current_route)
        new_stop_data = json.loads(new_stop)
        
        # Convert to RoutePoint objects
        current_route_points = [
            RoutePoint(
                lat=point["lat"],
                lon=point["lon"],
                name=point.get("name", f"Point {i}")
            )
            for i, point in enumerate(current_route_data)
        ]
        
        new_stop_point = RoutePoint(
            lat=new_stop_data["lat"],
            lon=new_stop_data["lon"],
            name=new_stop_data.get("name", "New Stop")
        )
        
        # Initialize optimizer
        routing_provider = get_routing_provider()
        optimizer = RouteOptimizer(routing_provider)
        
        # Get best insertion optimizer
        from app.services.routing.best_insertion import BestInsertionOptimizer
        insertion_optimizer = BestInsertionOptimizer(routing_provider)
        
        # Calculate insertion costs for all positions
        insertion_result = await insertion_optimizer.find_best_insertion_position(
            current_route_points, new_stop_point, profile, optimize_for
        )
        
        # Calculate costs for all positions (for visualization)
        all_points = current_route_points + [new_stop_point]
        matrix = await insertion_optimizer._get_or_compute_matrix(
            all_points, profile, optimize_for
        )
        
        position_costs = []
        new_stop_idx = len(current_route_points)
        
        for i in range(len(current_route_points) - 1):
            j = i + 1
            cost_i_to_new = matrix.get((i, new_stop_idx), 0.0)
            cost_new_to_j = matrix.get((new_stop_idx, j), 0.0)
            cost_i_to_j = matrix.get((i, j), 0.0)
            insertion_cost = cost_i_to_new + cost_new_to_j - cost_i_to_j
            
            position_costs.append({
                "position": j,
                "insertion_cost": insertion_cost,
                "is_best": j == insertion_result.best_position
            })
        
        return {
            "success": True,
            "best_position": insertion_result.best_position,
            "best_cost": insertion_result.insertion_cost,
            "position_costs": position_costs,
            "cost_type": optimize_for
        }
        
    except Exception as e:
        logger.error(f"Error in insertion preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate insertion preview"
        )
