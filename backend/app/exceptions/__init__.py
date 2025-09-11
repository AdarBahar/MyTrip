"""
Enhanced exception handling for the application.

This package provides specific exception types for different error scenarios,
enabling better error handling, user feedback, and debugging.
"""

from .routing import (
    RoutingBaseException,
    RouteValidationError,
    RouteProviderError,
    RouteRateLimitError,
    RouteOptimizationError,
    RouteCalculationError,
    RouteConfigurationError,
    ErrorContext,
    RoutingErrorHandler
)

__all__ = [
    "RoutingBaseException",
    "RouteValidationError", 
    "RouteProviderError",
    "RouteRateLimitError",
    "RouteOptimizationError",
    "RouteCalculationError",
    "RouteConfigurationError",
    "ErrorContext",
    "RoutingErrorHandler"
]
