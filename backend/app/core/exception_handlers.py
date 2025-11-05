"""
Global exception handlers for consistent error responses
"""
import logging
import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.datetime_utils import DateTimeStandards
from app.schemas.errors import (
    APIErrorResponse,
    ErrorCode,
    create_authentication_error,
    create_conflict_error,
    create_internal_error,
    create_not_found_error,
    create_permission_error,
    create_validation_error,
    format_pydantic_errors,
)
from app.services.error_analytics import get_error_analytics

logger = logging.getLogger(__name__)

# Ensure all error payloads are JSON-serializable (e.g., bytes -> str)
def _sanitize_for_json(obj):
    """Recursively convert non‑JSON‑serializable values to safe types."""
    try:
        from collections.abc import Mapping
    except Exception:
        Mapping = dict  # Fallback

    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8", errors="replace")
        except Exception:
            return repr(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, Mapping):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    # Fallback to string representation
    return str(obj)



def generate_request_id() -> str:
    """Generate a unique request ID for tracking"""
    return str(uuid.uuid4())


def log_error_to_analytics(request: Request, api_error: any, request_id: str):
    """Log error to analytics system"""
    try:
        from app.core.database import get_db

        db = next(get_db())
        analytics = get_error_analytics(db)

        # Extract user ID if available
        user_id = None
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)

        analytics.log_error(
            error=api_error,
            endpoint=str(request.url.path),
            user_id=user_id,
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"Failed to log error to analytics: {e}")


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    request_id = generate_request_id()

    # Format field-level errors
    field_errors = format_pydantic_errors(exc.errors())

    # Create standardized error (sanitize errors to avoid bytes in JSON)
    sanitized_errors = _sanitize_for_json(exc.errors())
    api_error = create_validation_error(
        message="Request validation failed",
        field_errors=field_errors,
        details={"validation_errors": sanitized_errors, "error_count": len(exc.errors())},
    )

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.warning(f"Validation error [{request_id}]: {exc.errors()}")

    # Log to analytics
    log_error_to_analytics(request, api_error, request_id)

    return JSONResponse(status_code=422, content=error_response.dict())


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    request_id = generate_request_id()

    # Check if detail is already a structured response (dict)
    # This happens when services raise HTTPException with structured error responses
    # like RouteOptimizationErrorResponse.dict()
    if isinstance(exc.detail, dict):
        # Add request metadata to structured response
        if "timestamp" not in exc.detail:
            exc.detail["timestamp"] = DateTimeStandards.format_datetime(
                DateTimeStandards.now_utc()
            )
        if "request_id" not in exc.detail:
            exc.detail["request_id"] = request_id
        if "path" not in exc.detail:
            exc.detail["path"] = str(request.url.path)

        logger.warning(
            f"HTTP exception [{request_id}]: {exc.status_code} - structured response"
        )

        return JSONResponse(status_code=exc.status_code, content=_sanitize_for_json(exc.detail))

    # Handle string-based detail messages with standard APIError wrapping
    # Map HTTP status codes to error types
    if exc.status_code == 401:
        api_error = create_authentication_error(
            message=exc.detail or "Authentication required"
        )
    elif exc.status_code == 403:
        api_error = create_permission_error(message=exc.detail or "Permission denied")
    elif exc.status_code == 404:
        # Try to extract resource type from detail
        detail = exc.detail or "Resource not found"
        api_error = create_not_found_error(resource_type="Resource", resource_id=None)
        api_error.message = detail
    elif exc.status_code == 409:
        api_error = create_conflict_error(message=exc.detail or "Resource conflict")
    elif exc.status_code == 422:
        api_error = create_validation_error(message=exc.detail or "Validation error")
    elif exc.status_code == 429:
        from app.schemas.errors import create_rate_limit_error

        api_error = create_rate_limit_error(message=exc.detail or "Rate limit exceeded")
    else:
        # Generic error for other status codes
        api_error = create_internal_error(
            message=exc.detail or f"HTTP {exc.status_code} error"
        )
        api_error.error_code = ErrorCode.INTERNAL_ERROR

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.warning(f"HTTP exception [{request_id}]: {exc.status_code} - {exc.detail}")

    return JSONResponse(status_code=exc.status_code, content=error_response.dict())


async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """Handle SQLAlchemy integrity constraint violations"""
    request_id = generate_request_id()

    # Parse common integrity errors
    error_msg = str(exc.orig) if exc.orig else str(exc)

    if "unique constraint" in error_msg.lower():
        api_error = create_conflict_error(
            message="A resource with this value already exists",
            details={"constraint_violation": "unique_constraint"},
        )
        status_code = 409
    elif "foreign key constraint" in error_msg.lower():
        api_error = create_validation_error(
            message="Referenced resource does not exist",
            details={"constraint_violation": "foreign_key_constraint"},
        )
        status_code = 422
    elif "not null constraint" in error_msg.lower():
        api_error = create_validation_error(
            message="Required field is missing",
            details={"constraint_violation": "not_null_constraint"},
        )
        status_code = 422
    else:
        api_error = create_conflict_error(
            message="Database constraint violation",
            details={"constraint_violation": "unknown"},
        )
        status_code = 409

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.error(f"Integrity error [{request_id}]: {error_msg}")

    return JSONResponse(status_code=status_code, content=error_response.dict())


async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle general SQLAlchemy errors"""
    request_id = generate_request_id()

    api_error = create_internal_error(
        message="Database operation failed",
        details={"error_type": "database_error", "database_error": str(exc)},
    )
    api_error.error_code = ErrorCode.DATABASE_ERROR

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.error(f"Database error [{request_id}]: {exc}")

    return JSONResponse(status_code=500, content=error_response.dict())


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    request_id = generate_request_id()

    api_error = create_internal_error(
        message="An unexpected error occurred",
        details={"error_type": type(exc).__name__, "error_message": str(exc)},
    )

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.error(
        f"Unexpected error [{request_id}]: {type(exc).__name__}: {exc}", exc_info=True
    )

    return JSONResponse(status_code=500, content=error_response.dict())


# Custom exception classes for business logic


class BusinessRuleViolation(Exception):
    """Exception for business rule violations"""

    def __init__(self, message: str, rule: str = None, details: dict = None):
        self.message = message
        self.rule = rule
        self.details = details or {}
        super().__init__(self.message)


class ResourceNotFoundError(Exception):
    """Exception for resource not found errors"""

    def __init__(self, resource_type: str, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = f"{resource_type} not found"
        if resource_id:
            message += f" with ID: {resource_id}"
        super().__init__(message)


class PermissionDeniedError(Exception):
    """Exception for permission denied errors"""

    def __init__(self, message: str = "Permission denied", resource: str = None):
        self.message = message
        self.resource = resource
        super().__init__(self.message)


async def business_rule_violation_handler(
    request: Request, exc: BusinessRuleViolation
) -> JSONResponse:
    """Handle business rule violation exceptions"""
    request_id = generate_request_id()

    api_error = create_business_rule_error(
        message=exc.message, rule=exc.rule, details=exc.details
    )

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.warning(f"Business rule violation [{request_id}]: {exc.message}")

    return JSONResponse(status_code=422, content=error_response.dict())


async def resource_not_found_handler(
    request: Request, exc: ResourceNotFoundError
) -> JSONResponse:
    """Handle resource not found exceptions"""
    request_id = generate_request_id()

    api_error = create_not_found_error(
        resource_type=exc.resource_type, resource_id=exc.resource_id
    )

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.info(f"Resource not found [{request_id}]: {exc}")

    return JSONResponse(status_code=404, content=error_response.dict())


async def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    """Handle permission denied exceptions"""
    request_id = generate_request_id()

    api_error = create_permission_error(message=exc.message, resource=exc.resource)

    error_response = APIErrorResponse(
        error=api_error, request_id=request_id, path=str(request.url.path)
    )

    logger.warning(f"Permission denied [{request_id}]: {exc.message}")

    return JSONResponse(status_code=403, content=error_response.dict())
