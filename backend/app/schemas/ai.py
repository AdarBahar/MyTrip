"""
AI-related Pydantic schemas
"""
from typing import Any, Optional, Union

from pydantic import BaseModel, Field


class RouteOptimizeRequest(BaseModel):
    """Request schema for AI route optimization"""

    prompt: str = Field(
        ...,
        description="Instructions for the AI on how to process the route data",
        min_length=1,
        max_length=2000,
    )
    data: Union[str, dict[str, Any]] = Field(
        ...,
        description="The route data to analyze (stops with coordinates and addresses)",
    )
    response_structure: str = Field(
        ...,
        description="Template/example showing the desired output format",
        min_length=1,
        max_length=1000,
    )


class RouteOptimizeResponse(BaseModel):
    """Response schema for AI route optimization"""

    result: str = Field(..., description="The AI-generated optimized route order")
    raw_response: Optional[dict[str, Any]] = Field(
        None, description="Full OpenAI API response for debugging"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata (tokens used, model used, etc.)"
    )


class AIError(BaseModel):
    """Error response for AI operations"""

    error_code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None, description="Additional error details"
    )
