"""
Enhanced Enum Documentation API

Provides comprehensive documentation for all API enums with user-friendly descriptions,
usage examples, and validation rules.
"""
from typing import Dict, List, Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.models.trip import TripStatus, TripMemberRole, TripMemberStatus
from app.models.stop import StopType, StopKind
from app.schemas.errors import ErrorCode
from app.core.datetime_utils import get_timezone_documentation
from app.schemas.base import get_datetime_schema_documentation

router = APIRouter()

class EnumValue(BaseModel):
    """Enhanced enum value with documentation"""
    value: str
    label: str
    description: str
    icon: str
    usage_notes: List[str]
    examples: List[str]

class EnumDocumentation(BaseModel):
    """Complete enum documentation"""
    name: str
    description: str
    values: List[EnumValue]
    usage_examples: List[str]
    validation_rules: List[str]
    related_endpoints: List[str]

@router.get("/trip-status", 
    response_model=EnumDocumentation,
    summary="🌐 Trip status enum documentation",
    description="""
    **Trip Status Enum Documentation**
    
    Complete documentation for the TripStatus enum including descriptions,
    usage examples, and validation rules.
    
    **Public Endpoint:** No authentication required.
    """)
async def get_trip_status_enum():
    """Get comprehensive TripStatus enum documentation"""
    return EnumDocumentation(
        name="TripStatus",
        description="Represents the current state of a trip throughout its lifecycle, from initial planning to completion and archival.",
        values=[
            EnumValue(
                value="draft",
                label="Draft",
                description="Trip is being planned - editable, not confirmed",
                icon="📝",
                usage_notes=[
                    "Default status for new trips",
                    "Allows full editing of all trip details",
                    "Not visible to invited members until activated"
                ],
                examples=[
                    "New trip just created",
                    "Trip being planned for future travel",
                    "Incomplete trip missing key details"
                ]
            ),
            EnumValue(
                value="active",
                label="Active",
                description="Trip is currently happening or confirmed for travel",
                icon="✈️",
                usage_notes=[
                    "Trip is confirmed and ready for travel",
                    "Visible to all invited members",
                    "Can still be edited but with some restrictions"
                ],
                examples=[
                    "Trip starting next week",
                    "Currently traveling",
                    "Confirmed trip with bookings made"
                ]
            ),
            EnumValue(
                value="completed",
                label="Completed",
                description="Trip has been completed successfully",
                icon="✅",
                usage_notes=[
                    "Trip has finished",
                    "Read-only for most operations",
                    "Can add photos and memories"
                ],
                examples=[
                    "Just returned from vacation",
                    "Trip finished last month",
                    "Successful business trip completed"
                ]
            ),
            EnumValue(
                value="archived",
                label="Archived",
                description="Trip has been archived for reference only",
                icon="📦",
                usage_notes=[
                    "Trip is stored for historical reference",
                    "Minimal editing allowed",
                    "Hidden from active trip lists"
                ],
                examples=[
                    "Old trip from several years ago",
                    "Cancelled trip kept for reference",
                    "Template trip for future planning"
                ]
            )
        ],
        usage_examples=[
            "POST /trips/ with status: 'draft'",
            "PATCH /trips/{id} to change status to 'active'",
            "GET /trips?status=active to filter active trips"
        ],
        validation_rules=[
            "Status transitions must follow logical order",
            "Cannot change from 'completed' back to 'active'",
            "Only owners can change trip status"
        ],
        related_endpoints=[
            "POST /trips/",
            "PATCH /trips/{trip_id}",
            "GET /trips/"
        ]
    )

@router.get("/stop-types", 
    response_model=EnumDocumentation,
    summary="🌐 Stop types enum documentation",
    description="""
    **Stop Types Enum Documentation**
    
    Complete documentation for the StopType enum including categories,
    descriptions, and usage examples for trip planning.
    
    **Public Endpoint:** No authentication required.
    """)
async def get_stop_types_enum():
    """Get comprehensive StopType enum documentation"""
    return EnumDocumentation(
        name="StopType",
        description="Categorizes stops by their purpose and type to help with trip planning, filtering, and organization.",
        values=[
            EnumValue(
                value="ACCOMMODATION",
                label="Accommodation",
                description="Hotels, hostels, vacation rentals, camping",
                icon="🏨",
                usage_notes=[
                    "Use for overnight stays",
                    "Typically has longer duration",
                    "Often fixed stops in route planning"
                ],
                examples=[
                    "Hotel booking for 2 nights",
                    "Airbnb rental",
                    "Camping site reservation"
                ]
            ),
            EnumValue(
                value="FOOD",
                label="Food & Dining",
                description="Restaurants, cafes, food markets, bars",
                icon="🍽️",
                usage_notes=[
                    "Plan meal stops during travel",
                    "Consider local cuisine specialties",
                    "Factor in meal timing"
                ],
                examples=[
                    "Famous local restaurant",
                    "Quick lunch stop",
                    "Food market visit"
                ]
            ),
            EnumValue(
                value="ATTRACTION",
                label="Attractions",
                description="Museums, landmarks, tourist sites, monuments",
                icon="🎭",
                usage_notes=[
                    "Main sightseeing destinations",
                    "Often require advance booking",
                    "Check opening hours and seasons"
                ],
                examples=[
                    "Eiffel Tower visit",
                    "Museum tour",
                    "Historical landmark"
                ]
            ),
            EnumValue(
                value="ACTIVITY",
                label="Activities",
                description="Tours, experiences, entertainment, sports",
                icon="🎯",
                usage_notes=[
                    "Interactive experiences",
                    "May require reservations",
                    "Weather dependent activities"
                ],
                examples=[
                    "Guided city tour",
                    "Hiking excursion",
                    "Concert or show"
                ]
            ),
            EnumValue(
                value="TRANSPORT",
                label="Transportation",
                description="Airports, train stations, bus stops, ports",
                icon="🚌",
                usage_notes=[
                    "Transit connection points",
                    "Usually fixed timing",
                    "Allow buffer time for connections"
                ],
                examples=[
                    "Airport departure",
                    "Train station transfer",
                    "Ferry terminal"
                ]
            ),
            EnumValue(
                value="OTHER",
                label="Other",
                description="Miscellaneous stops not fitting other categories",
                icon="📌",
                usage_notes=[
                    "Catch-all category",
                    "Use when no other type fits",
                    "Consider if a new category is needed"
                ],
                examples=[
                    "Meeting point",
                    "Unique local experience",
                    "Personal appointment"
                ]
            )
        ],
        usage_examples=[
            "POST /stops/ with stop_type: 'FOOD'",
            "GET /stops?stop_type=ATTRACTION",
            "Filter stops by type in trip planning"
        ],
        validation_rules=[
            "Must be one of the predefined values",
            "Case sensitive (use uppercase)",
            "Cannot be null for new stops"
        ],
        related_endpoints=[
            "GET /stops/types",
            "POST /trips/{trip_id}/days/{day_id}/stops",
            "PATCH /trips/{trip_id}/days/{day_id}/stops/{stop_id}"
        ]
    )

@router.get("/error-codes", 
    response_model=EnumDocumentation,
    summary="🌐 Error codes enum documentation",
    description="""
    **Error Codes Enum Documentation**
    
    Complete documentation for API error codes including descriptions,
    HTTP status mappings, and resolution guidance.
    
    **Public Endpoint:** No authentication required.
    """)
async def get_error_codes_enum():
    """Get comprehensive ErrorCode enum documentation"""
    return EnumDocumentation(
        name="ErrorCode",
        description="Provides consistent, machine-readable error codes that enable clients to handle specific error conditions programmatically.",
        values=[
            EnumValue(
                value="VALIDATION_ERROR",
                label="Validation Error",
                description="General validation failure with field details",
                icon="📝",
                usage_notes=[
                    "HTTP 422 status code",
                    "Includes field-level error details",
                    "Client should fix input and retry"
                ],
                examples=[
                    "Missing required field",
                    "Invalid email format",
                    "Date in the past when future required"
                ]
            ),
            EnumValue(
                value="AUTHENTICATION_REQUIRED",
                label="Authentication Required",
                description="Valid authentication token required",
                icon="🔐",
                usage_notes=[
                    "HTTP 401 status code",
                    "Include Bearer token in Authorization header",
                    "Redirect to login if in browser"
                ],
                examples=[
                    "Missing Authorization header",
                    "Invalid token format",
                    "Accessing protected endpoint without auth"
                ]
            ),
            EnumValue(
                value="PERMISSION_DENIED",
                label="Permission Denied",
                description="User lacks required permissions for resource",
                icon="🛡️",
                usage_notes=[
                    "HTTP 403 status code",
                    "User is authenticated but lacks permission",
                    "Contact admin or resource owner"
                ],
                examples=[
                    "Accessing another user's trip",
                    "Admin-only endpoint access",
                    "Editing read-only resource"
                ]
            ),
            EnumValue(
                value="RESOURCE_NOT_FOUND",
                label="Resource Not Found",
                description="Requested resource doesn't exist",
                icon="🔍",
                usage_notes=[
                    "HTTP 404 status code",
                    "Check resource ID is correct",
                    "Resource may have been deleted"
                ],
                examples=[
                    "Trip ID doesn't exist",
                    "Stop not found in day",
                    "User ID is invalid"
                ]
            )
        ],
        usage_examples=[
            "Check error.error_code in API responses",
            "Handle specific errors programmatically",
            "Display user-friendly error messages"
        ],
        validation_rules=[
            "Always included in error responses",
            "Machine-readable string format",
            "Consistent across all API endpoints"
        ],
        related_endpoints=[
            "All API endpoints (in error responses)",
            "Error handling documentation",
            "Client SDK error handling"
        ]
    )

@router.get("/datetime-standards",
    response_model=Dict[str, Any],
    summary="🌐 Date/DateTime standards documentation",
    description="""
    **Date/DateTime Standards Documentation**

    Complete documentation for ISO-8601 date/datetime handling standards
    used throughout the API for consistent timezone-aware data management.

    **Public Endpoint:** No authentication required.
    """)
async def get_datetime_standards():
    """Get comprehensive date/datetime standards documentation"""
    return {
        **get_datetime_schema_documentation(),
        **get_timezone_documentation()
    }

@router.get("/",
    response_model=Dict[str, str],
    summary="🌐 Available enum documentation",
    description="""
    **Available Enum Documentation**

    List all available enum documentation endpoints with descriptions.

    **Public Endpoint:** No authentication required.
    """)
async def list_enum_documentation():
    """List all available enum documentation endpoints"""
    return {
        "trip_status": "Trip lifecycle status documentation",
        "stop_types": "Stop categorization and types documentation",
        "error_codes": "API error codes and handling documentation",
        "member_roles": "Trip collaboration roles documentation",
        "member_status": "Trip member invitation status documentation",
        "datetime_standards": "ISO-8601 date/datetime standards and timezone handling"
    }
