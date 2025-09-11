"""
Enhanced type definitions for routing services.

This module provides strict type definitions and validation for routing
operations, improving type safety and API contracts.
"""
from typing import TypedDict, Literal, Optional, Union
from dataclasses import dataclass


# Routing profile types
RoutingProfile = Literal["car", "motorcycle", "bike", "walking"]

# Travel context types
TravelContext = Literal["urban", "highway", "rural", "mixed"]

# Optimization strategy types
OptimizationStrategy = Literal["nearest_neighbor", "matrix_based", "tsp_solver"]


class RouteOptionsDict(TypedDict, total=False):
    """Typed dictionary for route options with strict validation."""
    avoid_highways: bool
    avoid_tolls: bool
    avoid_ferries: bool
    avoid_unpaved: bool
    optimization_strategy: OptimizationStrategy
    travel_context: TravelContext
    max_detour_factor: float
    time_preference: Literal["fastest", "shortest", "balanced"]


class OptimizationOptionsDict(TypedDict, total=False):
    """Typed dictionary for optimization-specific options."""
    strategy: OptimizationStrategy
    max_iterations: int
    improvement_threshold: float
    use_cache: bool
    parallel_segments: bool
    tsp_solver_timeout: int


class RoutePointDict(TypedDict):
    """Typed dictionary for route point data."""
    lat: float
    lon: float
    name: str


class OptimizationSavingsDict(TypedDict):
    """Typed dictionary for optimization savings data."""
    distance_km_saved: float
    duration_min_saved: float
    distance_improvement_percent: float
    duration_improvement_percent: float


class RouteSegmentDict(TypedDict):
    """Typed dictionary for route segment data."""
    from_point: RoutePointDict
    to_point: RoutePointDict
    distance_km: float
    duration_min: float
    segment_type: Literal["start_to_stop", "stop_to_stop", "stop_to_end"]
    segment_index: int


@dataclass(frozen=True)
class ValidationError:
    """Immutable validation error with context."""
    field: str
    message: str
    value: Optional[Union[str, int, float]] = None
    
    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.field}: {self.message} (got: {self.value})"
        return f"{self.field}: {self.message}"


@dataclass(frozen=True)
class RouteValidationResult:
    """Result of route validation with errors and warnings."""
    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0
    
    def get_error_messages(self) -> list[str]:
        """Get list of error messages."""
        return [str(error) for error in self.errors]
    
    def get_warning_messages(self) -> list[str]:
        """Get list of warning messages."""
        return [str(warning) for warning in self.warnings]


class RouteValidator:
    """Validator for route data with comprehensive checks."""
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> list[ValidationError]:
        """Validate latitude and longitude coordinates."""
        errors = []
        
        if not isinstance(lat, (int, float)):
            errors.append(ValidationError("lat", "Must be a number", lat))
        elif not -90 <= lat <= 90:
            errors.append(ValidationError("lat", "Must be between -90 and 90", lat))
        
        if not isinstance(lon, (int, float)):
            errors.append(ValidationError("lon", "Must be a number", lon))
        elif not -180 <= lon <= 180:
            errors.append(ValidationError("lon", "Must be between -180 and 180", lon))
        
        return errors
    
    @staticmethod
    def validate_route_point(point_data: dict, field_name: str = "point") -> list[ValidationError]:
        """Validate a route point dictionary."""
        errors = []
        
        # Check required fields
        required_fields = ["lat", "lon", "name"]
        for field in required_fields:
            if field not in point_data:
                errors.append(ValidationError(
                    f"{field_name}.{field}", 
                    "Required field missing"
                ))
        
        # Validate coordinates if present
        if "lat" in point_data and "lon" in point_data:
            coord_errors = RouteValidator.validate_coordinates(
                point_data["lat"], point_data["lon"]
            )
            for error in coord_errors:
                errors.append(ValidationError(
                    f"{field_name}.{error.field}",
                    error.message,
                    error.value
                ))
        
        # Validate name
        if "name" in point_data:
            name = point_data["name"]
            if not isinstance(name, str):
                errors.append(ValidationError(
                    f"{field_name}.name", 
                    "Must be a string", 
                    name
                ))
            elif len(name.strip()) == 0:
                errors.append(ValidationError(
                    f"{field_name}.name", 
                    "Cannot be empty"
                ))
        
        return errors
    
    @staticmethod
    def validate_route_options(options: dict) -> RouteValidationResult:
        """Validate route options dictionary."""
        errors = []
        warnings = []
        
        # Validate boolean options
        bool_options = ["avoid_highways", "avoid_tolls", "avoid_ferries", "avoid_unpaved", "use_cache", "parallel_segments"]
        for option in bool_options:
            if option in options and not isinstance(options[option], bool):
                errors.append(ValidationError(
                    option, 
                    "Must be a boolean", 
                    options[option]
                ))
        
        # Validate numeric options
        if "max_detour_factor" in options:
            factor = options["max_detour_factor"]
            if not isinstance(factor, (int, float)) or factor < 1.0:
                errors.append(ValidationError(
                    "max_detour_factor", 
                    "Must be a number >= 1.0", 
                    factor
                ))
        
        # Validate enum options
        if "optimization_strategy" in options:
            strategy = options["optimization_strategy"]
            valid_strategies = ["nearest_neighbor", "matrix_based", "tsp_solver"]
            if strategy not in valid_strategies:
                errors.append(ValidationError(
                    "optimization_strategy", 
                    f"Must be one of {valid_strategies}", 
                    strategy
                ))
        
        return RouteValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
