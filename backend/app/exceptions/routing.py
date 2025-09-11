"""
Enhanced exception handling for routing services.

This module provides specific exception types for different routing
error scenarios, enabling better error handling and user feedback.
"""
from typing import Optional, Any, Dict
from dataclasses import dataclass


class RoutingBaseException(Exception):
    """Base exception for all routing-related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
    
    def _get_default_user_message(self) -> str:
        """Get default user-friendly message."""
        return "A routing error occurred. Please try again."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.user_message,
            "details": self.details,
            "technical_message": self.message
        }


class RouteValidationError(RoutingBaseException):
    """Raised when route input validation fails."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = value
        
        super().__init__(
            message=message,
            error_code="ROUTE_VALIDATION_ERROR",
            details=details,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        return "Invalid route data provided. Please check your input and try again."


class RouteProviderError(RoutingBaseException):
    """Raised when routing provider fails."""
    
    def __init__(
        self, 
        message: str, 
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        is_recoverable: bool = True,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if provider:
            details["provider"] = provider
        if status_code:
            details["status_code"] = status_code
        details["is_recoverable"] = is_recoverable
        
        super().__init__(
            message=message,
            error_code="ROUTE_PROVIDER_ERROR",
            details=details,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        if self.details.get("is_recoverable", True):
            return "Routing service temporarily unavailable. Please try again in a moment."
        return "Routing service is currently unavailable. Please try again later."


class RouteRateLimitError(RouteProviderError):
    """Raised when routing provider rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str, 
        retry_after: Optional[int] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if retry_after:
            details["retry_after_seconds"] = retry_after
        
        super().__init__(
            message=message,
            error_code="ROUTE_RATE_LIMIT_ERROR",
            details=details,
            is_recoverable=True,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        retry_after = self.details.get("retry_after_seconds")
        if retry_after:
            return f"Rate limit exceeded. Please try again in {retry_after} seconds."
        return "Rate limit exceeded. Please try again in a few moments."


class RouteOptimizationError(RoutingBaseException):
    """Raised when route optimization fails."""
    
    def __init__(
        self, 
        message: str, 
        strategy: Optional[str] = None,
        fallback_available: bool = True,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if strategy:
            details["optimization_strategy"] = strategy
        details["fallback_available"] = fallback_available
        
        super().__init__(
            message=message,
            error_code="ROUTE_OPTIMIZATION_ERROR",
            details=details,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        if self.details.get("fallback_available", True):
            return "Route optimization failed, using original order."
        return "Route optimization is currently unavailable."


class RouteCalculationError(RoutingBaseException):
    """Raised when route calculation fails."""
    
    def __init__(
        self, 
        message: str, 
        segment: Optional[str] = None,
        fallback_used: bool = False,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if segment:
            details["failed_segment"] = segment
        details["fallback_used"] = fallback_used
        
        super().__init__(
            message=message,
            error_code="ROUTE_CALCULATION_ERROR",
            details=details,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        if self.details.get("fallback_used", False):
            return "Route calculated using estimated distances. Results may be approximate."
        return "Unable to calculate route. Please check your locations and try again."


class RouteConfigurationError(RoutingBaseException):
    """Raised when routing configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(
            message=message,
            error_code="ROUTE_CONFIGURATION_ERROR",
            details=details,
            **kwargs
        )
    
    def _get_default_user_message(self) -> str:
        return "Routing service configuration error. Please contact support."


@dataclass
class ErrorContext:
    """Context information for error handling and logging."""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    trip_id: Optional[str] = None
    day_id: Optional[str] = None
    operation: Optional[str] = None
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class RoutingErrorHandler:
    """Centralized error handling for routing operations."""
    
    @staticmethod
    def handle_provider_error(
        error: Exception, 
        provider: str,
        context: Optional[ErrorContext] = None
    ) -> RouteProviderError:
        """Convert generic provider errors to specific routing errors."""
        error_str = str(error)
        
        # Check for rate limiting
        if "429" in error_str or "rate limit" in error_str.lower():
            return RouteRateLimitError(
                f"Rate limit exceeded for {provider}: {error_str}",
                provider=provider,
                details={"original_error": error_str}
            )
        
        # Check for authentication errors
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str.lower():
            return RouteProviderError(
                f"Authentication failed for {provider}: {error_str}",
                provider=provider,
                is_recoverable=False,
                details={"original_error": error_str}
            )
        
        # Check for network errors
        if any(term in error_str.lower() for term in ["timeout", "connection", "network"]):
            return RouteProviderError(
                f"Network error with {provider}: {error_str}",
                provider=provider,
                is_recoverable=True,
                details={"original_error": error_str}
            )
        
        # Generic provider error
        return RouteProviderError(
            f"Provider error from {provider}: {error_str}",
            provider=provider,
            details={"original_error": error_str}
        )
    
    @staticmethod
    def create_user_friendly_error(
        error: Exception,
        operation: str = "routing",
        context: Optional[ErrorContext] = None
    ) -> Dict[str, Any]:
        """Create user-friendly error response."""
        if isinstance(error, RoutingBaseException):
            return error.to_dict()
        
        # Handle unexpected errors
        return {
            "error_code": "UNEXPECTED_ERROR",
            "message": f"An unexpected error occurred during {operation}. Please try again.",
            "details": {
                "operation": operation,
                "technical_message": str(error)
            }
        }
