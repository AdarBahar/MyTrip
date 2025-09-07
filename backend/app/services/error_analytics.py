"""
Error Analytics and Monitoring Service

Tracks error patterns, provides insights, and helps improve API reliability
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import json

from app.schemas.errors import ErrorCode, APIError

logger = logging.getLogger(__name__)

class ErrorPattern:
    """Represents a pattern of errors for analysis"""
    
    def __init__(self, error_code: str, count: int, endpoints: List[str], 
                 common_messages: List[str], time_range: str):
        self.error_code = error_code
        self.count = count
        self.endpoints = endpoints
        self.common_messages = common_messages
        self.time_range = time_range

class ErrorAnalytics:
    """Service for analyzing error patterns and providing insights"""
    
    def __init__(self, db: Session):
        self.db = db
        self.error_log = []  # In-memory storage for demo (use database in production)
    
    def log_error(self, error: APIError, endpoint: str, user_id: Optional[str] = None, 
                  request_id: Optional[str] = None):
        """Log an error for analytics"""
        error_entry = {
            'timestamp': datetime.utcnow(),
            'error_code': error.error_code,
            'message': error.message,
            'endpoint': endpoint,
            'user_id': user_id,
            'request_id': request_id,
            'details': error.details or {},
            'field_errors': error.field_errors or {},
            'suggestions_provided': len(error.suggestions or [])
        }
        
        self.error_log.append(error_entry)
        
        # Log to standard logging as well
        logger.warning(f"API Error [{request_id}]: {error.error_code} on {endpoint} - {error.message}")
    
    def get_error_patterns(self, hours: int = 24) -> List[ErrorPattern]:
        """Analyze error patterns over the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_log if e['timestamp'] > cutoff_time]
        
        if not recent_errors:
            return []
        
        # Group by error code
        error_groups = defaultdict(list)
        for error in recent_errors:
            error_groups[error['error_code']].append(error)
        
        patterns = []
        for error_code, errors in error_groups.items():
            endpoints = list(set(e['endpoint'] for e in errors))
            messages = [e['message'] for e in errors]
            common_messages = [msg for msg, count in Counter(messages).most_common(3)]
            
            pattern = ErrorPattern(
                error_code=error_code,
                count=len(errors),
                endpoints=endpoints,
                common_messages=common_messages,
                time_range=f"Last {hours} hours"
            )
            patterns.append(pattern)
        
        # Sort by frequency
        patterns.sort(key=lambda p: p.count, reverse=True)
        return patterns
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over time"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        recent_errors = [e for e in self.error_log if e['timestamp'] > cutoff_time]
        
        # Group by day and error code
        daily_errors = defaultdict(lambda: defaultdict(int))
        for error in recent_errors:
            day = error['timestamp'].date()
            daily_errors[day][error['error_code']] += 1
        
        # Calculate trends
        trends = {
            'total_errors': len(recent_errors),
            'unique_error_codes': len(set(e['error_code'] for e in recent_errors)),
            'daily_breakdown': dict(daily_errors),
            'top_error_codes': [code for code, count in 
                              Counter(e['error_code'] for e in recent_errors).most_common(5)],
            'error_rate_trend': self._calculate_error_rate_trend(recent_errors, days)
        }
        
        return trends
    
    def get_endpoint_error_analysis(self) -> Dict[str, Any]:
        """Analyze errors by endpoint"""
        endpoint_errors = defaultdict(list)
        for error in self.error_log:
            endpoint_errors[error['endpoint']].append(error)
        
        analysis = {}
        for endpoint, errors in endpoint_errors.items():
            error_codes = Counter(e['error_code'] for e in errors)
            analysis[endpoint] = {
                'total_errors': len(errors),
                'error_codes': dict(error_codes),
                'most_common_error': error_codes.most_common(1)[0] if error_codes else None,
                'recent_errors': len([e for e in errors 
                                    if e['timestamp'] > datetime.utcnow() - timedelta(hours=24)])
            }
        
        return analysis
    
    def get_user_error_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze error patterns for a specific user"""
        user_errors = [e for e in self.error_log if e.get('user_id') == user_id]
        
        if not user_errors:
            return {'message': 'No errors found for this user'}
        
        error_codes = Counter(e['error_code'] for e in user_errors)
        endpoints = Counter(e['endpoint'] for e in user_errors)
        
        return {
            'total_errors': len(user_errors),
            'error_codes': dict(error_codes),
            'endpoints': dict(endpoints),
            'recent_errors': len([e for e in user_errors 
                                if e['timestamp'] > datetime.utcnow() - timedelta(hours=24)]),
            'first_error': min(e['timestamp'] for e in user_errors),
            'last_error': max(e['timestamp'] for e in user_errors)
        }
    
    def get_validation_error_insights(self) -> Dict[str, Any]:
        """Analyze validation errors to identify common issues"""
        validation_errors = [e for e in self.error_log 
                           if e['error_code'] == ErrorCode.VALIDATION_ERROR]
        
        if not validation_errors:
            return {'message': 'No validation errors found'}
        
        # Analyze field errors
        field_error_counts = defaultdict(int)
        for error in validation_errors:
            for field in error.get('field_errors', {}):
                field_error_counts[field] += 1
        
        # Analyze endpoints with validation issues
        endpoint_validation_errors = Counter(e['endpoint'] for e in validation_errors)
        
        return {
            'total_validation_errors': len(validation_errors),
            'problematic_fields': dict(field_error_counts.most_common(10)),
            'endpoints_with_validation_issues': dict(endpoint_validation_errors),
            'suggestions': self._generate_validation_suggestions(field_error_counts)
        }
    
    def get_error_resolution_metrics(self) -> Dict[str, Any]:
        """Calculate metrics about error resolution and user experience"""
        total_errors = len(self.error_log)
        if total_errors == 0:
            return {'message': 'No errors to analyze'}
        
        # Calculate suggestion effectiveness (mock data for demo)
        errors_with_suggestions = len([e for e in self.error_log if e['suggestions_provided'] > 0])
        
        # Group errors by type for resolution analysis
        error_type_analysis = {
            'validation_errors': len([e for e in self.error_log 
                                    if e['error_code'] == ErrorCode.VALIDATION_ERROR]),
            'authentication_errors': len([e for e in self.error_log 
                                        if e['error_code'] == ErrorCode.AUTHENTICATION_REQUIRED]),
            'not_found_errors': len([e for e in self.error_log 
                                   if e['error_code'] == ErrorCode.RESOURCE_NOT_FOUND]),
            'permission_errors': len([e for e in self.error_log 
                                    if e['error_code'] == ErrorCode.PERMISSION_DENIED])
        }
        
        return {
            'total_errors': total_errors,
            'errors_with_suggestions': errors_with_suggestions,
            'suggestion_coverage': (errors_with_suggestions / total_errors) * 100,
            'error_type_breakdown': error_type_analysis,
            'resolution_recommendations': self._generate_resolution_recommendations(error_type_analysis)
        }
    
    def _calculate_error_rate_trend(self, errors: List[Dict], days: int) -> str:
        """Calculate if error rate is increasing, decreasing, or stable"""
        if len(errors) < 2:
            return "insufficient_data"
        
        # Split into two halves and compare
        mid_point = len(errors) // 2
        first_half = errors[:mid_point]
        second_half = errors[mid_point:]
        
        first_half_rate = len(first_half) / (days / 2)
        second_half_rate = len(second_half) / (days / 2)
        
        if second_half_rate > first_half_rate * 1.2:
            return "increasing"
        elif second_half_rate < first_half_rate * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_validation_suggestions(self, field_errors: Dict[str, int]) -> List[str]:
        """Generate suggestions based on common validation errors"""
        suggestions = []
        
        if 'title' in field_errors:
            suggestions.append("Consider adding client-side validation for trip titles")
        
        if 'start_date' in field_errors:
            suggestions.append("Add date picker with validation to prevent past dates")
        
        if 'email' in field_errors:
            suggestions.append("Implement email format validation on the frontend")
        
        if len(field_errors) > 5:
            suggestions.append("Consider implementing comprehensive form validation")
        
        return suggestions
    
    def _generate_resolution_recommendations(self, error_analysis: Dict[str, int]) -> List[str]:
        """Generate recommendations for reducing errors"""
        recommendations = []
        
        if error_analysis['validation_errors'] > 10:
            recommendations.append("Implement better client-side validation to reduce validation errors")
        
        if error_analysis['authentication_errors'] > 5:
            recommendations.append("Improve authentication flow and token refresh mechanisms")
        
        if error_analysis['not_found_errors'] > 5:
            recommendations.append("Add better error handling for missing resources")
        
        if error_analysis['permission_errors'] > 3:
            recommendations.append("Review and clarify permission requirements in documentation")
        
        return recommendations
    
    def generate_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a comprehensive error report"""
        patterns = self.get_error_patterns(hours)
        trends = self.get_error_trends(7)
        endpoint_analysis = self.get_endpoint_error_analysis()
        validation_insights = self.get_validation_error_insights()
        resolution_metrics = self.get_error_resolution_metrics()
        
        return {
            'report_generated': datetime.utcnow().isoformat(),
            'time_period': f"Last {hours} hours",
            'summary': {
                'total_errors': len([e for e in self.error_log 
                                   if e['timestamp'] > datetime.utcnow() - timedelta(hours=hours)]),
                'unique_error_codes': len(set(e['error_code'] for e in self.error_log 
                                            if e['timestamp'] > datetime.utcnow() - timedelta(hours=hours))),
                'most_common_error': patterns[0].error_code if patterns else None
            },
            'error_patterns': [
                {
                    'error_code': p.error_code,
                    'count': p.count,
                    'endpoints': p.endpoints,
                    'common_messages': p.common_messages
                } for p in patterns[:5]  # Top 5 patterns
            ],
            'trends': trends,
            'endpoint_analysis': endpoint_analysis,
            'validation_insights': validation_insights,
            'resolution_metrics': resolution_metrics
        }

# Global error analytics instance (in production, use dependency injection)
error_analytics = None

def get_error_analytics(db: Session) -> ErrorAnalytics:
    """Get error analytics instance"""
    global error_analytics
    if error_analytics is None:
        error_analytics = ErrorAnalytics(db)
    return error_analytics
