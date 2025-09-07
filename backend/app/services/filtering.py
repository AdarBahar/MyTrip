"""
Enhanced filtering and sorting service for flexible query building
"""
import logging
from typing import List, Optional, Dict, Any, Type, Union
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, desc, asc, func, text
from datetime import datetime, date
from enum import Enum
import re

logger = logging.getLogger(__name__)

class FilterOperator(str, Enum):
    """Supported filter operators"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    REGEX = "regex"

class SortDirection(str, Enum):
    """Sort directions"""
    ASC = "asc"
    DESC = "desc"

class FilterCondition:
    """Represents a single filter condition"""
    
    def __init__(
        self,
        field: str,
        operator: FilterOperator,
        value: Any = None,
        values: Optional[List[Any]] = None
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.values = values or []
    
    def validate(self) -> bool:
        """Validate the filter condition"""
        if self.operator in [FilterOperator.IN, FilterOperator.NOT_IN, FilterOperator.BETWEEN]:
            return bool(self.values)
        elif self.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return True
        else:
            return self.value is not None

class SortCondition:
    """Represents a single sort condition"""
    
    def __init__(self, field: str, direction: SortDirection = SortDirection.ASC):
        self.field = field
        self.direction = direction

class FilteringService:
    """Service for building complex queries with filtering and sorting"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def apply_filters(
        self,
        query: Query,
        model_class: Type,
        filters: List[FilterCondition],
        allowed_fields: Optional[List[str]] = None
    ) -> Query:
        """
        Apply filter conditions to a query
        
        Args:
            query: SQLAlchemy query object
            model_class: SQLAlchemy model class
            filters: List of filter conditions
            allowed_fields: List of fields that can be filtered (security)
            
        Returns:
            Modified query with filters applied
        """
        for filter_condition in filters:
            if not filter_condition.validate():
                self.logger.warning(f"Invalid filter condition: {filter_condition.field} {filter_condition.operator}")
                continue
            
            # Security check: only allow filtering on permitted fields
            if allowed_fields and filter_condition.field not in allowed_fields:
                self.logger.warning(f"Filtering not allowed on field: {filter_condition.field}")
                continue
            
            # Check if field exists on model
            if not hasattr(model_class, filter_condition.field):
                self.logger.warning(f"Field {filter_condition.field} not found on model {model_class.__name__}")
                continue
            
            field_attr = getattr(model_class, filter_condition.field)
            query = self._apply_single_filter(query, field_attr, filter_condition)
        
        return query
    
    def _apply_single_filter(self, query: Query, field_attr: Any, condition: FilterCondition) -> Query:
        """Apply a single filter condition to the query"""
        
        try:
            if condition.operator == FilterOperator.EQUALS:
                return query.filter(field_attr == condition.value)
            
            elif condition.operator == FilterOperator.NOT_EQUALS:
                return query.filter(field_attr != condition.value)
            
            elif condition.operator == FilterOperator.GREATER_THAN:
                return query.filter(field_attr > condition.value)
            
            elif condition.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                return query.filter(field_attr >= condition.value)
            
            elif condition.operator == FilterOperator.LESS_THAN:
                return query.filter(field_attr < condition.value)
            
            elif condition.operator == FilterOperator.LESS_THAN_OR_EQUAL:
                return query.filter(field_attr <= condition.value)
            
            elif condition.operator == FilterOperator.CONTAINS:
                return query.filter(field_attr.ilike(f"%{condition.value}%"))
            
            elif condition.operator == FilterOperator.STARTS_WITH:
                return query.filter(field_attr.ilike(f"{condition.value}%"))
            
            elif condition.operator == FilterOperator.ENDS_WITH:
                return query.filter(field_attr.ilike(f"%{condition.value}"))
            
            elif condition.operator == FilterOperator.IN:
                return query.filter(field_attr.in_(condition.values))
            
            elif condition.operator == FilterOperator.NOT_IN:
                return query.filter(~field_attr.in_(condition.values))
            
            elif condition.operator == FilterOperator.IS_NULL:
                return query.filter(field_attr.is_(None))
            
            elif condition.operator == FilterOperator.IS_NOT_NULL:
                return query.filter(field_attr.isnot(None))
            
            elif condition.operator == FilterOperator.BETWEEN:
                if len(condition.values) >= 2:
                    return query.filter(field_attr.between(condition.values[0], condition.values[1]))
            
            elif condition.operator == FilterOperator.REGEX:
                # PostgreSQL regex operator
                return query.filter(field_attr.op('~')(condition.value))
            
            else:
                self.logger.warning(f"Unsupported filter operator: {condition.operator}")
                return query
                
        except Exception as e:
            self.logger.error(f"Error applying filter {condition.field} {condition.operator}: {e}")
            return query
    
    def apply_sorting(
        self,
        query: Query,
        model_class: Type,
        sorts: List[SortCondition],
        allowed_fields: Optional[List[str]] = None,
        default_sort: Optional[SortCondition] = None
    ) -> Query:
        """
        Apply sort conditions to a query
        
        Args:
            query: SQLAlchemy query object
            model_class: SQLAlchemy model class
            sorts: List of sort conditions
            allowed_fields: List of fields that can be sorted (security)
            default_sort: Default sort if no sorts provided
            
        Returns:
            Modified query with sorting applied
        """
        applied_sorts = []
        
        for sort_condition in sorts:
            # Security check: only allow sorting on permitted fields
            if allowed_fields and sort_condition.field not in allowed_fields:
                self.logger.warning(f"Sorting not allowed on field: {sort_condition.field}")
                continue
            
            # Check if field exists on model
            if not hasattr(model_class, sort_condition.field):
                self.logger.warning(f"Field {sort_condition.field} not found on model {model_class.__name__}")
                continue
            
            field_attr = getattr(model_class, sort_condition.field)
            
            if sort_condition.direction == SortDirection.DESC:
                applied_sorts.append(desc(field_attr))
            else:
                applied_sorts.append(asc(field_attr))
        
        # Apply default sort if no valid sorts were applied
        if not applied_sorts and default_sort:
            if hasattr(model_class, default_sort.field):
                field_attr = getattr(model_class, default_sort.field)
                if default_sort.direction == SortDirection.DESC:
                    applied_sorts.append(desc(field_attr))
                else:
                    applied_sorts.append(asc(field_attr))
        
        if applied_sorts:
            query = query.order_by(*applied_sorts)
        
        return query
    
    def parse_filter_string(self, filter_str: str) -> List[FilterCondition]:
        """
        Parse filter string into FilterCondition objects
        
        Format: field:operator:value,field2:operator2:value2
        Example: "status:eq:active,created_at:gte:2024-01-01,title:contains:trip"
        """
        conditions = []
        
        if not filter_str:
            return conditions
        
        try:
            for condition_str in filter_str.split(','):
                parts = condition_str.strip().split(':', 2)
                if len(parts) < 2:
                    continue
                
                field = parts[0].strip()
                operator_str = parts[1].strip()
                value_str = parts[2].strip() if len(parts) > 2 else None
                
                try:
                    operator = FilterOperator(operator_str)
                except ValueError:
                    self.logger.warning(f"Invalid filter operator: {operator_str}")
                    continue
                
                # Parse value based on operator
                if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
                    conditions.append(FilterCondition(field, operator))
                elif operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
                    values = [v.strip() for v in value_str.split('|')] if value_str else []
                    conditions.append(FilterCondition(field, operator, values=values))
                elif operator == FilterOperator.BETWEEN:
                    values = [v.strip() for v in value_str.split('|')] if value_str else []
                    if len(values) >= 2:
                        conditions.append(FilterCondition(field, operator, values=values[:2]))
                else:
                    # Convert value to appropriate type
                    parsed_value = self._parse_value(value_str)
                    conditions.append(FilterCondition(field, operator, parsed_value))
                    
        except Exception as e:
            self.logger.error(f"Error parsing filter string '{filter_str}': {e}")
        
        return conditions
    
    def parse_sort_string(self, sort_str: str) -> List[SortCondition]:
        """
        Parse sort string into SortCondition objects
        
        Format: field:direction,field2:direction2
        Example: "created_at:desc,title:asc"
        """
        conditions = []
        
        if not sort_str:
            return conditions
        
        try:
            for condition_str in sort_str.split(','):
                parts = condition_str.strip().split(':')
                if len(parts) < 1:
                    continue
                
                field = parts[0].strip()
                direction_str = parts[1].strip() if len(parts) > 1 else 'asc'
                
                try:
                    direction = SortDirection(direction_str)
                except ValueError:
                    direction = SortDirection.ASC
                
                conditions.append(SortCondition(field, direction))
                
        except Exception as e:
            self.logger.error(f"Error parsing sort string '{sort_str}': {e}")
        
        return conditions
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse string value to appropriate Python type"""
        if not value_str:
            return None
        
        # Boolean values
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
        
        # Numeric values
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Date values (ISO format)
        try:
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value_str):
                return datetime.strptime(value_str, '%Y-%m-%d').date()
            elif re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value_str):
                return datetime.fromisoformat(value_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # String value (default)
        return value_str
