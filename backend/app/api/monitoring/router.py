"""
Error Monitoring and Analytics API Endpoints

Provides insights into API error patterns and system health
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.security import get_admin_user, get_user_or_admin, ADMIN_RESPONSES, PUBLIC_RESPONSES
from app.models.user import User
from app.services.error_analytics import get_error_analytics, ErrorAnalytics
from app.schemas.errors import APIErrorResponse

router = APIRouter()

@router.get("/errors/patterns",
    summary="Get error patterns analysis",
    description="""
    **Error Pattern Analysis**

    Analyze error patterns over a specified time period to identify:
    - Most common error types
    - Problematic endpoints
    - Error frequency trends
    - Common error messages

    **Use Cases:**
    - System health monitoring
    - API reliability assessment
    - Error reduction planning
    - User experience optimization

    **Admin Access Required:** This endpoint is restricted to administrators only.
    """,
    responses={
        200: {"description": "Error patterns analysis"},
        **ADMIN_RESPONSES
    }
)
async def get_error_patterns(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours (1-168)"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get error patterns analysis for the specified time period"""
    
    analytics = get_error_analytics(db)
    patterns = analytics.get_error_patterns(hours)
    
    return {
        "time_period": f"Last {hours} hours",
        "patterns": [
            {
                "error_code": p.error_code,
                "count": p.count,
                "endpoints": p.endpoints,
                "common_messages": p.common_messages,
                "time_range": p.time_range
            } for p in patterns
        ],
        "total_patterns": len(patterns)
    }

@router.get("/errors/trends",
    summary="Get error trends over time",
    description="""
    **Error Trends Analysis**

    Track error trends over time to identify:
    - Daily error counts
    - Error rate changes
    - Trending error types
    - System stability metrics

    **Metrics Included:**
    - Total errors in period
    - Unique error codes
    - Daily breakdown
    - Top error codes
    - Error rate trend (increasing/decreasing/stable)

    **Admin Access Required:** This endpoint is restricted to administrators only.
    """,
    responses={
        200: {"description": "Error trends analysis"},
        **ADMIN_RESPONSES
    }
)
async def get_error_trends(
    days: int = Query(7, ge=1, le=30, description="Time period in days (1-30)"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get error trends over the specified time period"""
    
    analytics = get_error_analytics(db)
    trends = analytics.get_error_trends(days)
    
    return {
        "time_period": f"Last {days} days",
        **trends
    }

@router.get("/errors/endpoints",
    summary="Get error analysis by endpoint",
    description="""
    **Endpoint Error Analysis**
    
    Analyze errors grouped by API endpoint to identify:
    - Endpoints with highest error rates
    - Common error types per endpoint
    - Recent error activity
    - Endpoint reliability metrics
    
    **Use Cases:**
    - Identify problematic endpoints
    - Prioritize bug fixes
    - Monitor endpoint health
    - API quality assessment
    
    **Authentication Required:** Admin users only
    """,
    responses={
        200: {"description": "Endpoint error analysis"},
        **ADMIN_RESPONSES
    }
)
async def get_endpoint_error_analysis(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get error analysis grouped by endpoint"""
    
    analytics = get_error_analytics(db)
    analysis = analytics.get_endpoint_error_analysis()
    
    return {
        "endpoint_analysis": analysis,
        "total_endpoints_with_errors": len(analysis)
    }

@router.get("/errors/validation",
    summary="Get validation error insights",
    description="""
    **Validation Error Analysis**
    
    Deep dive into validation errors to identify:
    - Most problematic form fields
    - Endpoints with validation issues
    - Common validation failures
    - Improvement suggestions
    
    **Insights Provided:**
    - Field-level error frequency
    - Validation error trends
    - Suggested improvements
    - User experience impact
    
    **Authentication Required:** Admin users only
    """,
    responses={
        200: {"description": "Validation error insights"},
        **ADMIN_RESPONSES
    }
)
async def get_validation_error_insights(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed analysis of validation errors"""
    
    analytics = get_error_analytics(db)
    insights = analytics.get_validation_error_insights()
    
    return insights

@router.get("/errors/user/{user_id}",
    summary="Get error patterns for specific user",
    description="""
    **User-Specific Error Analysis**

    Analyze error patterns for a specific user to:
    - Identify user-specific issues
    - Provide targeted support
    - Track user experience problems
    - Monitor user behavior patterns

    **Privacy Note:** Only accessible by admins or the user themselves

    **Authentication Required:** Admin users or the user themselves
    """,
    responses={
        200: {"description": "User error analysis"},
        **ADMIN_RESPONSES,
        404: {"description": "User not found", "model": APIErrorResponse}
    }
)
async def get_user_error_patterns(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get error patterns for a specific user"""

    # Use our standardized user/admin check
    await get_user_or_admin(user_id, current_user)
    
    analytics = get_error_analytics(db)
    patterns = analytics.get_user_error_patterns(user_id)
    
    return {
        "user_id": user_id,
        **patterns
    }

@router.get("/errors/resolution-metrics",
    summary="Get error resolution metrics",
    description="""
    **Error Resolution Metrics**
    
    Analyze error resolution effectiveness:
    - Suggestion coverage percentage
    - Error type breakdown
    - Resolution recommendations
    - User experience metrics
    
    **Metrics Include:**
    - Total errors tracked
    - Errors with actionable suggestions
    - Error type distribution
    - Improvement recommendations
    
    **Authentication Required:** Admin users only
    """,
    responses={
        200: {"description": "Error resolution metrics"},
        **ADMIN_RESPONSES
    }
)
async def get_error_resolution_metrics(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get metrics about error resolution and user experience"""
    
    analytics = get_error_analytics(db)
    metrics = analytics.get_error_resolution_metrics()
    
    return metrics

@router.get("/errors/report",
    summary="Generate comprehensive error report",
    description="""
    **Comprehensive Error Report**
    
    Generate a complete error analysis report including:
    - Error patterns and trends
    - Endpoint analysis
    - Validation insights
    - Resolution metrics
    - Actionable recommendations
    
    **Report Sections:**
    - Executive summary
    - Error patterns
    - Trend analysis
    - Endpoint breakdown
    - Validation insights
    - Resolution metrics
    
    **Use Cases:**
    - Weekly/monthly reporting
    - System health assessment
    - Planning error reduction initiatives
    - Stakeholder communication
    
    **Authentication Required:** Admin users only
    """,
    responses={
        200: {"description": "Comprehensive error report"},
        **ADMIN_RESPONSES
    }
)
async def generate_error_report(
    hours: int = Query(24, ge=1, le=168, description="Time period for report in hours"),
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Generate a comprehensive error analysis report"""
    
    analytics = get_error_analytics(db)
    report = analytics.generate_error_report(hours)
    
    return report

@router.get("/health",
    summary="🌐 System health check",
    description="""
    **System Health Check**

    Quick health check for the monitoring system:
    - Service availability
    - Recent error activity
    - System status

    **Public Endpoint:** No authentication required.

    **Security:**
    - This endpoint is publicly accessible
    - No Bearer token required
    - Rate limiting may apply
    """,
    responses={
        200: {"description": "System health status"},
        **PUBLIC_RESPONSES
    }
)
async def health_check(db: Session = Depends(get_db)):
    """Health check for the monitoring system"""
    
    try:
        analytics = get_error_analytics(db)
        recent_errors = len([e for e in analytics.error_log 
                           if (analytics.error_log and 
                               e['timestamp'] > analytics.error_log[-1]['timestamp'] if analytics.error_log else True)])
        
        return {
            "status": "healthy",
            "monitoring_active": True,
            "recent_errors_tracked": recent_errors,
            "timestamp": analytics.error_log[-1]['timestamp'].isoformat() if analytics.error_log else None
        }
    except Exception as e:
        return {
            "status": "degraded",
            "monitoring_active": False,
            "error": str(e)
        }
