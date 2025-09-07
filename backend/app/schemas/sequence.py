"""
Schemas for sequence management operations
"""
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.services.sequence_manager import SequenceOperation

class SequenceOperationRequest(BaseModel):
    """Request for sequence operation"""
    operation: SequenceOperation = Field(..., description="Type of sequence operation")
    target_id: Optional[str] = Field(None, description="Target item ID (for insert_after/insert_before)")
    target_position: Optional[int] = Field(None, ge=1, description="Target position (for move_to_position)")
    
    @validator('target_id')
    def validate_target_id(cls, v, values):
        """Validate target_id requirements"""
        operation = values.get('operation')
        if operation in [SequenceOperation.INSERT_AFTER, SequenceOperation.INSERT_BEFORE] and not v:
            raise ValueError(f"target_id is required for {operation} operation")
        return v
    
    @validator('target_position')
    def validate_target_position(cls, v, values):
        """Validate target_position requirements"""
        operation = values.get('operation')
        if operation == SequenceOperation.MOVE_TO_POSITION and v is None:
            raise ValueError("target_position is required for move_to_position operation")
        return v

class SequenceOperationResult(BaseModel):
    """Result of sequence operation"""
    success: bool = Field(..., description="Whether the operation succeeded")
    item_id: str = Field(..., description="ID of the item that was moved")
    old_sequence: Optional[int] = Field(None, description="Original sequence number")
    new_sequence: Optional[int] = Field(None, description="New sequence number")
    operation: str = Field(..., description="Operation that was performed")
    affected_items: Optional[int] = Field(None, description="Number of other items affected")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class SequenceNormalizeRequest(BaseModel):
    """Request to normalize sequences in a scope"""
    scope_filters: Optional[dict] = Field(default_factory=dict, description="Filters to define the scope")

class SequenceNormalizeResult(BaseModel):
    """Result of sequence normalization"""
    success: bool = Field(..., description="Whether the normalization succeeded")
    items_resequenced: int = Field(..., description="Number of items that were resequenced")
    error: Optional[str] = Field(None, description="Error message if normalization failed")

# Enhanced filtering schemas
class FilterConditionSchema(BaseModel):
    """Schema for a single filter condition"""
    field: str = Field(..., description="Field name to filter on")
    operator: str = Field(..., description="Filter operator (eq, ne, gt, gte, lt, lte, contains, etc.)")
    value: Optional[str] = Field(None, description="Filter value")
    values: Optional[List[str]] = Field(None, description="Multiple values for IN/NOT_IN operators")

class SortConditionSchema(BaseModel):
    """Schema for a single sort condition"""
    field: str = Field(..., description="Field name to sort by")
    direction: str = Field("asc", pattern="^(asc|desc)$", description="Sort direction: asc or desc")

class FilterSortRequest(BaseModel):
    """Request with filtering and sorting parameters"""
    filters: Optional[List[FilterConditionSchema]] = Field(default_factory=list, description="List of filter conditions")
    sorts: Optional[List[SortConditionSchema]] = Field(default_factory=list, description="List of sort conditions")
    
    # Alternative: string-based filters and sorts for URL parameters
    filter_string: Optional[str] = Field(None, description="Filter string: field:operator:value,field2:operator2:value2")
    sort_string: Optional[str] = Field(None, description="Sort string: field:direction,field2:direction2")

# Resource-specific schemas with allowed fields

class StopFilterSort(FilterSortRequest):
    """Filtering and sorting for stops"""
    
    @validator('filters')
    def validate_stop_filters(cls, v):
        """Validate that only allowed fields are used for filtering"""
        allowed_fields = [
            'stop_type', 'seq', 'duration_min', 'notes', 'created_at', 'updated_at',
            'day_id', 'place_id'
        ]
        for filter_cond in v:
            if filter_cond.field not in allowed_fields:
                raise ValueError(f"Filtering not allowed on field: {filter_cond.field}")
        return v
    
    @validator('sorts')
    def validate_stop_sorts(cls, v):
        """Validate that only allowed fields are used for sorting"""
        allowed_fields = [
            'seq', 'stop_type', 'duration_min', 'created_at', 'updated_at'
        ]
        for sort_cond in v:
            if sort_cond.field not in allowed_fields:
                raise ValueError(f"Sorting not allowed on field: {sort_cond.field}")
        return v

class DayFilterSort(FilterSortRequest):
    """Filtering and sorting for days"""
    
    @validator('filters')
    def validate_day_filters(cls, v):
        """Validate that only allowed fields are used for filtering"""
        allowed_fields = [
            'date', 'title', 'status', 'seq', 'created_at', 'updated_at',
            'trip_id'
        ]
        for filter_cond in v:
            if filter_cond.field not in allowed_fields:
                raise ValueError(f"Filtering not allowed on field: {filter_cond.field}")
        return v
    
    @validator('sorts')
    def validate_day_sorts(cls, v):
        """Validate that only allowed fields are used for sorting"""
        allowed_fields = [
            'date', 'seq', 'title', 'status', 'created_at', 'updated_at'
        ]
        for sort_cond in v:
            if sort_cond.field not in allowed_fields:
                raise ValueError(f"Sorting not allowed on field: {sort_cond.field}")
        return v

class TripFilterSort(FilterSortRequest):
    """Filtering and sorting for trips"""
    
    @validator('filters')
    def validate_trip_filters(cls, v):
        """Validate that only allowed fields are used for filtering"""
        allowed_fields = [
            'status', 'title', 'destination', 'start_date', 'is_published',
            'created_at', 'updated_at'
        ]
        for filter_cond in v:
            if filter_cond.field not in allowed_fields:
                raise ValueError(f"Filtering not allowed on field: {filter_cond.field}")
        return v
    
    @validator('sorts')
    def validate_trip_sorts(cls, v):
        """Validate that only allowed fields are used for sorting"""
        allowed_fields = [
            'title', 'destination', 'start_date', 'status', 'is_published',
            'created_at', 'updated_at'
        ]
        for sort_cond in v:
            if sort_cond.field not in allowed_fields:
                raise ValueError(f"Sorting not allowed on field: {sort_cond.field}")
        return v

class PlaceFilterSort(FilterSortRequest):
    """Filtering and sorting for places"""
    
    @validator('filters')
    def validate_place_filters(cls, v):
        """Validate that only allowed fields are used for filtering"""
        allowed_fields = [
            'name', 'place_type', 'country', 'region', 'created_at', 'updated_at'
        ]
        for filter_cond in v:
            if filter_cond.field not in allowed_fields:
                raise ValueError(f"Filtering not allowed on field: {filter_cond.field}")
        return v
    
    @validator('sorts')
    def validate_place_sorts(cls, v):
        """Validate that only allowed fields are used for sorting"""
        allowed_fields = [
            'name', 'place_type', 'country', 'region', 'created_at', 'updated_at'
        ]
        for sort_cond in v:
            if sort_cond.field not in allowed_fields:
                raise ValueError(f"Sorting not allowed on field: {sort_cond.field}")
        return v

# Utility schemas for common operations

class MultiAttributeFilter(BaseModel):
    """Multi-attribute filter for complex queries"""
    search_term: Optional[str] = Field(None, description="Global search term across multiple fields")
    date_range: Optional[dict] = Field(None, description="Date range filter with 'start' and 'end' keys")
    status_filter: Optional[List[str]] = Field(None, description="Multiple status values")
    type_filter: Optional[List[str]] = Field(None, description="Multiple type values")
    
    class Config:
        schema_extra = {
            "example": {
                "search_term": "jerusalem",
                "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
                "status_filter": ["active", "completed"],
                "type_filter": ["food", "attraction"]
            }
        }

class AdvancedQueryRequest(BaseModel):
    """Advanced query request combining multiple filter types"""
    basic_filters: Optional[FilterSortRequest] = Field(None, description="Basic field-level filters")
    multi_attribute: Optional[MultiAttributeFilter] = Field(None, description="Multi-attribute search")
    pagination: Optional[dict] = Field(None, description="Pagination parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "basic_filters": {
                    "filter_string": "status:eq:active,created_at:gte:2024-01-01",
                    "sort_string": "created_at:desc,title:asc"
                },
                "multi_attribute": {
                    "search_term": "jerusalem",
                    "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
                },
                "pagination": {"page": 1, "size": 20}
            }
        }
