"""
Route optimization service
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from app.services.routing import get_routing_provider
from app.services.routing.tsp_optimizer import TSPOptimizer
from app.services.routing.geometry_builder import GeometryBuilder
from app.schemas.route_optimization import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteOptimizationErrorResponse,
    LocationRequest,
    LocationResponse,
    LocationType,
    OptimizationSummary,
    OptimizationDiagnostics,
    OptimizationError,
    Objective,
    Units
)

logger = logging.getLogger(__name__)


class RouteOptimizationService:
    """Service for route optimization"""
    
    def __init__(self):
        self.routing_provider = get_routing_provider()
        self.tsp_optimizer = TSPOptimizer(self.routing_provider)
        self.geometry_builder = GeometryBuilder(self.routing_provider)
    
    async def optimize_route(self, request: RouteOptimizationRequest) -> RouteOptimizationResponse:
        """
        Optimize route based on request
        
        Args:
            request: Route optimization request
            
        Returns:
            RouteOptimizationResponse with optimized route
            
        Raises:
            HTTPException: For validation or processing errors
        """
        try:
            # Validate request
            validation_errors = self._validate_request(request)
            if validation_errors:
                raise HTTPException(
                    status_code=400,
                    detail=RouteOptimizationErrorResponse(
                        errors=validation_errors
                    ).dict()
                )
            
            # Check if graph is routable
            routability_errors = await self._check_routability(request)
            if routability_errors:
                raise HTTPException(
                    status_code=422,
                    detail=RouteOptimizationErrorResponse(
                        errors=routability_errors
                    ).dict()
                )
            
            # Perform optimization
            optimization_result = await self.tsp_optimizer.optimize_route(
                request.data.locations,
                request.meta.objective,
                request.meta.vehicle_profile.value,
                self._build_routing_options(request)
            )
            
            # Build geometry
            geometry, geometry_warnings = await self.geometry_builder.build_route_geometry(
                optimization_result.ordered_locations,
                request.meta.vehicle_profile.value,
                self._build_routing_options(request)
            )
            
            # Build response
            response = self._build_response(
                request, optimization_result, geometry, geometry_warnings
            )
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Route optimization failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=RouteOptimizationErrorResponse(
                    errors=[OptimizationError(
                        code="INTERNAL_ERROR",
                        message="Internal server error during optimization"
                    )]
                ).dict()
            )
    
    def _validate_request(self, request: RouteOptimizationRequest) -> List[OptimizationError]:
        """Validate optimization request"""
        errors = []
        
        try:
            # Basic validation is handled by Pydantic, but we can add custom checks
            locations = request.data.locations
            
            # Check for multiple START locations
            start_locations = [loc for loc in locations if loc.type == LocationType.START]
            if len(start_locations) > 1:
                errors.append(OptimizationError(
                    code="MULTIPLE_START",
                    message="More than one START provided"
                ))
            elif len(start_locations) == 0:
                errors.append(OptimizationError(
                    code="MISSING_START",
                    message="No START provided"
                ))
            
            # Check for missing END
            end_locations = [loc for loc in locations if loc.type == LocationType.END]
            if len(end_locations) == 0:
                errors.append(OptimizationError(
                    code="MISSING_END",
                    message="No END provided"
                ))
            elif len(end_locations) > 1:
                errors.append(OptimizationError(
                    code="MULTIPLE_END",
                    message="More than one END provided"
                ))
            
            # Check fixed sequence conflicts
            fixed_seqs = []
            for loc in locations:
                if loc.fixed_seq and loc.seq is not None:
                    if loc.seq in fixed_seqs:
                        errors.append(OptimizationError(
                            code="FIXED_CONFLICT",
                            message="Fixed stop sequences conflict or are out of range"
                        ))
                        break
                    fixed_seqs.append(loc.seq)
            
            # Check coordinate validity
            for loc in locations:
                if not (-90 <= loc.lat <= 90) or not (-180 <= loc.lng <= 180):
                    errors.append(OptimizationError(
                        code="INVALID_COORDS",
                        message="One or more coordinates are invalid"
                    ))
                    break
            
        except Exception as e:
            errors.append(OptimizationError(
                code="SCHEMA_VALIDATION",
                message="Payload failed JSON schema validation"
            ))
        
        return errors
    
    async def _check_routability(self, request: RouteOptimizationRequest) -> List[OptimizationError]:
        """Check if locations are routable"""
        errors = []
        
        try:
            # Simple connectivity check - try to route between start and end
            locations = request.data.locations
            start_loc = next(loc for loc in locations if loc.type == LocationType.START)
            end_loc = next(loc for loc in locations if loc.type == LocationType.END)
            
            from app.services.routing.base import RoutePoint
            
            route_points = [
                RoutePoint(lat=start_loc.lat, lon=start_loc.lng, name=start_loc.name),
                RoutePoint(lat=end_loc.lat, lon=end_loc.lng, name=end_loc.name)
            ]
            
            # Try a simple route to check connectivity
            await self.routing_provider.compute_route(
                route_points,
                request.meta.vehicle_profile.value,
                self._build_routing_options(request)
            )
            
        except Exception as e:
            logger.warning(f"Routability check failed: {e}")
            errors.append(OptimizationError(
                code="DISCONNECTED_GRAPH",
                message="Locations are not routable with current profile/avoidances"
            ))
        
        return errors
    
    def _build_routing_options(self, request: RouteOptimizationRequest) -> Dict[str, Any]:
        """Build routing options from request"""
        options = {}
        
        for avoid_option in request.meta.avoid:
            if avoid_option.value == "tolls":
                options["avoid_tolls"] = True
            elif avoid_option.value == "highways":
                options["avoid_highways"] = True
            elif avoid_option.value == "ferries":
                options["avoid_ferries"] = True
        
        return options
    
    def _build_response(
        self,
        request: RouteOptimizationRequest,
        optimization_result,
        geometry,
        geometry_warnings: List[str]
    ) -> RouteOptimizationResponse:
        """Build optimization response"""
        
        # Build ordered locations with ETAs and leg metrics
        ordered_responses = []
        cumulative_time = 0.0
        
        for i, location in enumerate(optimization_result.ordered_locations):
            # Calculate leg metrics
            leg_distance = optimization_result.leg_distances_km[i] if i < len(optimization_result.leg_distances_km) else 0.0
            leg_duration = optimization_result.leg_durations_min[i] if i < len(optimization_result.leg_durations_min) else 0.0
            
            ordered_responses.append(LocationResponse(
                seq=i + 1,
                id=location.id,
                type=location.type,
                name=location.name,
                lat=location.lat,
                lng=location.lng,
                fixed_seq=location.fixed_seq,
                eta_min=cumulative_time,
                leg_distance_km=leg_distance,
                leg_duration_min=leg_duration
            ))
            
            cumulative_time += leg_duration
        
        # Build summary
        stop_count = len([loc for loc in optimization_result.ordered_locations if loc.type == LocationType.STOP])
        summary = OptimizationSummary(
            stop_count=stop_count,
            total_distance_km=optimization_result.total_distance_km,
            total_duration_min=optimization_result.total_duration_min
        )
        
        # Build diagnostics
        diagnostics = OptimizationDiagnostics(
            warnings=geometry_warnings,
            assumptions=[],
            computation_notes=optimization_result.computation_notes
        )
        
        # Add assumptions based on request
        if request.meta.avoid:
            diagnostics.assumptions.append(f"Avoiding: {', '.join([a.value for a in request.meta.avoid])}")
        
        if request.meta.objective == Objective.TIME:
            diagnostics.assumptions.append("Optimized for minimum travel time")
        else:
            diagnostics.assumptions.append("Optimized for minimum distance")
        
        return RouteOptimizationResponse(
            version="1.0",
            objective=request.meta.objective,
            units=request.meta.units,
            ordered=ordered_responses,
            summary=summary,
            geometry=geometry,
            diagnostics=diagnostics,
            errors=[]
        )
