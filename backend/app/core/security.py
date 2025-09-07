"""
Standardized Security Dependencies and Patterns for Phase 2

Provides consistent authentication and authorization patterns across all API endpoints
"""
from typing import Optional, List, Callable, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_current_user_optional
from app.core.database import get_db
from app.models.user import User
from app.schemas.errors import APIErrorResponse

# Security dependency functions

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for admin-only endpoints
    
    Ensures the current user has admin privileges
    
    Raises:
        HTTPException: 403 if user is not an admin
    
    Returns:
        User: The authenticated admin user
    """
    if not getattr(current_user, 'is_admin', False):
        from app.core.exception_handlers import PermissionDeniedError
        raise PermissionDeniedError(
            message="Admin access required",
            resource="admin_endpoint"
        )
    return current_user

async def get_user_or_admin(
    user_id: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency for endpoints that allow access by the user themselves or admins
    
    Used for user-specific endpoints where users can access their own data
    or admins can access any user's data
    
    Args:
        user_id: The user ID being accessed
        current_user: The authenticated user
    
    Raises:
        HTTPException: 403 if user is not the owner or an admin
    
    Returns:
        User: The authenticated user (either the owner or an admin)
    """
    is_admin = getattr(current_user, 'is_admin', False)
    is_owner = current_user.id == user_id
    
    if not (is_admin or is_owner):
        from app.core.exception_handlers import PermissionDeniedError
        raise PermissionDeniedError(
            message="Access denied. You can only access your own data or must be an admin.",
            resource=f"user_data:{user_id}"
        )
    
    return current_user

def require_resource_owner(
    get_resource_func: Callable[[str, Session], Any],
    resource_id_param: str = "resource_id"
):
    """
    Factory function to create dependencies that verify resource ownership
    
    Args:
        get_resource_func: Function to get the resource (trip, day, etc.)
        resource_id_param: Name of the parameter containing the resource ID
    
    Returns:
        Dependency function that verifies ownership
    """
    async def verify_ownership(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        **kwargs
    ):
        resource_id = kwargs.get(resource_id_param)
        if not resource_id:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameter: {resource_id_param}"
            )
        
        resource = get_resource_func(resource_id, db)
        
        if not resource:
            from app.core.exception_handlers import ResourceNotFoundError
            raise ResourceNotFoundError(
                resource_type=get_resource_func.__name__.replace('get_', '').replace('_by_id', ''),
                resource_id=resource_id
            )
        
        # Check ownership (assumes resource has created_by field)
        if hasattr(resource, 'created_by') and resource.created_by != current_user.id:
            from app.core.exception_handlers import PermissionDeniedError
            raise PermissionDeniedError(
                message="You can only access your own resources",
                resource=f"{resource.__class__.__name__}:{resource_id}"
            )
        
        return resource
    
    return verify_ownership

# Standard response schemas for security

SECURITY_RESPONSES = {
    "401": {
        "description": "Authentication required",
        "model": APIErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "error_code": "AUTHENTICATION_REQUIRED",
                        "message": "Authentication required",
                        "suggestions": [
                            "Include a valid Bearer token in the Authorization header",
                            "Ensure your token has not expired",
                            "Contact support if you continue to have authentication issues"
                        ]
                    },
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "req_123e4567-e89b-12d3-a456-426614174000",
                    "path": "/api/endpoint"
                }
            }
        }
    },
    "403": {
        "description": "Permission denied",
        "model": APIErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "error_code": "PERMISSION_DENIED",
                        "message": "Permission denied",
                        "suggestions": [
                            "Ensure you have the required permissions for this resource",
                            "Contact the resource owner to request access",
                            "Verify you are accessing your own resources"
                        ]
                    },
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "req_123e4567-e89b-12d3-a456-426614174001",
                    "path": "/api/endpoint"
                }
            }
        }
    }
}

ADMIN_RESPONSES = {
    **SECURITY_RESPONSES,
    "403": {
        "description": "Admin access required",
        "model": APIErrorResponse,
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "error_code": "PERMISSION_DENIED",
                        "message": "Admin access required",
                        "suggestions": [
                            "Contact an administrator to request admin privileges",
                            "Verify you are using the correct account",
                            "This endpoint is restricted to administrators only"
                        ]
                    },
                    "timestamp": "2024-01-15T10:30:00Z",
                    "request_id": "req_123e4567-e89b-12d3-a456-426614174002",
                    "path": "/api/admin-endpoint"
                }
            }
        }
    }
}

PUBLIC_RESPONSES = {
    # No authentication responses for public endpoints
}

# Helper functions for creating standardized endpoint decorators

def authenticated_endpoint(
    method: str,
    path: str,
    response_model: Any,
    summary: str,
    description: str,
    status_code: int = 200,
    additional_responses: dict = None
):
    """
    Decorator factory for authenticated endpoints with standardized security
    
    Args:
        method: HTTP method (get, post, put, patch, delete)
        path: Endpoint path
        response_model: Pydantic model for successful response
        summary: Short description for OpenAPI
        description: Detailed description for OpenAPI
        status_code: HTTP status code for success
        additional_responses: Additional response schemas
    
    Returns:
        FastAPI route decorator with standardized security
    """
    responses = {
        status_code: {"description": "Success", "model": response_model},
        **SECURITY_RESPONSES
    }
    
    if additional_responses:
        responses.update(additional_responses)
    
    def decorator(router):
        return getattr(router, method)(
            path,
            response_model=response_model,
            status_code=status_code,
            summary=summary,
            description=f"""
{description}

**Authentication Required:** You must be logged in to access this endpoint.

**Security:**
- Requires valid Bearer token in Authorization header
- Returns 401 if authentication is missing or invalid
- Returns 403 if you don't have permission to access this resource
            """.strip(),
            responses=responses
        )
    
    return decorator

def admin_endpoint(
    method: str,
    path: str,
    response_model: Any,
    summary: str,
    description: str,
    status_code: int = 200,
    additional_responses: dict = None
):
    """
    Decorator factory for admin-only endpoints with standardized security
    
    Args:
        method: HTTP method (get, post, put, patch, delete)
        path: Endpoint path
        response_model: Pydantic model for successful response
        summary: Short description for OpenAPI
        description: Detailed description for OpenAPI
        status_code: HTTP status code for success
        additional_responses: Additional response schemas
    
    Returns:
        FastAPI route decorator with admin security
    """
    responses = {
        status_code: {"description": "Success", "model": response_model},
        **ADMIN_RESPONSES
    }
    
    if additional_responses:
        responses.update(additional_responses)
    
    def decorator(router):
        return getattr(router, method)(
            path,
            response_model=response_model,
            status_code=status_code,
            summary=summary,
            description=f"""
{description}

**Admin Access Required:** This endpoint is restricted to administrators only.

**Security:**
- Requires valid Bearer token in Authorization header
- Requires admin privileges on the authenticated user account
- Returns 401 if authentication is missing or invalid
- Returns 403 if you don't have admin privileges
            """.strip(),
            responses=responses
        )
    
    return decorator

def public_endpoint(
    method: str,
    path: str,
    response_model: Any,
    summary: str,
    description: str,
    status_code: int = 200,
    additional_responses: dict = None
):
    """
    Decorator factory for public endpoints with clear documentation
    
    Args:
        method: HTTP method (get, post, put, patch, delete)
        path: Endpoint path
        response_model: Pydantic model for successful response
        summary: Short description for OpenAPI
        description: Detailed description for OpenAPI
        status_code: HTTP status code for success
        additional_responses: Additional response schemas
    
    Returns:
        FastAPI route decorator for public endpoints
    """
    responses = {
        status_code: {"description": "Success", "model": response_model},
        **PUBLIC_RESPONSES
    }
    
    if additional_responses:
        responses.update(additional_responses)
    
    def decorator(router):
        return getattr(router, method)(
            path,
            response_model=response_model,
            status_code=status_code,
            summary=f"🌐 {summary}",  # Public indicator
            description=f"""
{description}

**Public Endpoint:** No authentication required.

**Security:**
- This endpoint is publicly accessible
- No Bearer token required
- Rate limiting may apply
            """.strip(),
            responses=responses
        )
    
    return decorator
