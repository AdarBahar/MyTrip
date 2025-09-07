"""
Unified error schemas for consistent API error responses
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from app.core.datetime_utils import DateTimeStandards

class ErrorCode(str, Enum):
    """
    Standardized error codes for comprehensive API error handling

    Provides consistent, machine-readable error codes that enable
    clients to handle specific error conditions programmatically.
    """

    # Validation Errors (422) - Input validation failures
    VALIDATION_ERROR = "VALIDATION_ERROR"          # 📝 General validation failure with field details
    INVALID_INPUT = "INVALID_INPUT"                # ❌ Input doesn't meet format requirements
    MISSING_FIELD = "MISSING_FIELD"                # 📋 Required field is missing from request
    INVALID_FORMAT = "INVALID_FORMAT"              # 🔤 Field format is incorrect (email, date, etc.)

    # Authentication & Authorization (401, 403) - Access control
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"  # 🔐 Valid authentication token required
    INVALID_TOKEN = "INVALID_TOKEN"                      # 🚫 Authentication token is malformed or invalid
    TOKEN_EXPIRED = "TOKEN_EXPIRED"                      # ⏰ Authentication token has expired
    PERMISSION_DENIED = "PERMISSION_DENIED"              # 🛡️ User lacks required permissions for resource

    # Resource Errors (404, 409) - Resource state issues
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"      # 🔍 Requested resource doesn't exist
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"        # ⚡ Resource state conflict (concurrent modification)
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"      # 🔄 Resource already exists (unique constraint)

    # Business Logic Errors (422) - Domain rule violations
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"  # 📏 Operation violates business rules
    INVALID_OPERATION = "INVALID_OPERATION"              # 🚧 Operation not allowed in current state
    SEQUENCE_CONFLICT = "SEQUENCE_CONFLICT"              # 🔢 Sequence number conflicts with existing data
    
    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    
    # Routing Specific Errors
    ROUTING_ERROR = "ROUTING_ERROR"
    COORDINATES_OUT_OF_BOUNDS = "COORDINATES_OUT_OF_BOUNDS"
    ROUTING_SERVICE_UNAVAILABLE = "ROUTING_SERVICE_UNAVAILABLE"

class APIError(BaseModel):
    """Standardized error information"""
    error_code: ErrorCode = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context and debugging information")
    field_errors: Optional[Dict[str, List[str]]] = Field(None, description="Field-level validation errors")
    suggestions: Optional[List[str]] = Field(None, description="Actionable suggestions to resolve the error")

class APIErrorResponse(BaseModel):
    """Complete error response wrapper"""
    error: APIError = Field(..., description="Error information")
    timestamp: str = Field(
        default_factory=lambda: DateTimeStandards.format_datetime(DateTimeStandards.now_utc()),
        description="When the error occurred (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)"
    )
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")
    path: Optional[str] = Field(None, description="API endpoint path where error occurred")

# Utility functions for creating standardized errors

def create_validation_error(
    message: str,
    field_errors: Optional[Dict[str, List[str]]] = None,
    details: Optional[Dict[str, Any]] = None
) -> APIError:
    """Create a standardized validation error"""
    return APIError(
        error_code=ErrorCode.VALIDATION_ERROR,
        message=message,
        field_errors=field_errors,
        details=details,
        suggestions=[
            "Check the request format and required fields",
            "Ensure all field values meet the specified constraints"
        ]
    )

def create_authentication_error(
    message: str = "Authentication required",
    details: Optional[Dict[str, Any]] = None
) -> APIError:
    """Create a standardized authentication error"""
    return APIError(
        error_code=ErrorCode.AUTHENTICATION_REQUIRED,
        message=message,
        details=details,
        suggestions=[
            "Include a valid Bearer token in the Authorization header",
            "Ensure your token has not expired",
            "Contact support if you continue to have authentication issues"
        ]
    )

def create_permission_error(
    message: str = "Permission denied",
    resource: Optional[str] = None
) -> APIError:
    """Create a standardized permission error"""
    details = {"resource": resource} if resource else None
    return APIError(
        error_code=ErrorCode.PERMISSION_DENIED,
        message=message,
        details=details,
        suggestions=[
            "Ensure you have the required permissions for this resource",
            "Contact the resource owner to request access",
            "Verify you are accessing your own resources"
        ]
    )

def create_not_found_error(
    resource_type: str,
    resource_id: Optional[str] = None
) -> APIError:
    """Create a standardized not found error"""
    message = f"{resource_type} not found"
    if resource_id:
        message += f" with ID: {resource_id}"
    
    return APIError(
        error_code=ErrorCode.RESOURCE_NOT_FOUND,
        message=message,
        details={"resource_type": resource_type, "resource_id": resource_id},
        suggestions=[
            "Verify the resource ID is correct",
            "Ensure the resource exists and you have access to it",
            "Check if the resource may have been deleted"
        ]
    )

def create_conflict_error(
    message: str,
    conflicting_field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> APIError:
    """Create a standardized conflict error"""
    error_details = details or {}
    if conflicting_field:
        error_details["conflicting_field"] = conflicting_field
    
    return APIError(
        error_code=ErrorCode.RESOURCE_CONFLICT,
        message=message,
        details=error_details,
        suggestions=[
            "Use a different value for the conflicting field",
            "Check if a similar resource already exists",
            "Consider updating the existing resource instead"
        ]
    )

def create_business_rule_error(
    message: str,
    rule: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> APIError:
    """Create a standardized business rule violation error"""
    error_details = details or {}
    if rule:
        error_details["violated_rule"] = rule
    
    return APIError(
        error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
        message=message,
        details=error_details,
        suggestions=[
            "Review the business rules for this operation",
            "Ensure all prerequisites are met",
            "Contact support if you believe this is an error"
        ]
    )

def create_rate_limit_error(
    message: str = "Rate limit exceeded",
    retry_after: Optional[int] = None,
    limit_type: Optional[str] = None
) -> APIError:
    """Create a standardized rate limit error"""
    details = {}
    if retry_after:
        details["retry_after_seconds"] = retry_after
    if limit_type:
        details["limit_type"] = limit_type
    
    suggestions = ["Wait before making additional requests"]
    if retry_after:
        suggestions.append(f"Retry after {retry_after} seconds")
    suggestions.extend([
        "Consider reducing the frequency of requests",
        "Use bulk operations when available"
    ])
    
    return APIError(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=message,
        details=details,
        suggestions=suggestions
    )

def create_routing_error(
    message: str,
    error_type: Optional[str] = None,
    suggestions: Optional[List[str]] = None
) -> APIError:
    """Create a standardized routing error"""
    error_code = ErrorCode.ROUTING_ERROR
    if error_type == "out_of_bounds":
        error_code = ErrorCode.COORDINATES_OUT_OF_BOUNDS
    elif error_type == "service_unavailable":
        error_code = ErrorCode.ROUTING_SERVICE_UNAVAILABLE
    
    default_suggestions = [
        "Verify all coordinates are valid",
        "Ensure locations are within supported regions",
        "Try again in a few moments"
    ]
    
    return APIError(
        error_code=error_code,
        message=message,
        details={"error_type": error_type} if error_type else None,
        suggestions=suggestions or default_suggestions
    )

def create_internal_error(
    message: str = "An internal error occurred",
    details: Optional[Dict[str, Any]] = None
) -> APIError:
    """Create a standardized internal server error"""
    return APIError(
        error_code=ErrorCode.INTERNAL_ERROR,
        message=message,
        details=details,
        suggestions=[
            "Try the request again in a few moments",
            "Contact support if the problem persists",
            "Include the request ID when reporting issues"
        ]
    )

def format_pydantic_errors(errors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Format Pydantic validation errors into field-level errors"""
    field_errors = {}
    
    for error in errors:
        field_path = ".".join(str(loc) for loc in error["loc"])
        error_msg = error["msg"]
        
        if field_path not in field_errors:
            field_errors[field_path] = []
        field_errors[field_path].append(error_msg)
    
    return field_errors
