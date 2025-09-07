"""
Standardized bulk operation schemas
"""
from typing import List, Optional, Dict, Any, Generic, TypeVar, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

T = TypeVar('T')

class BulkOperationType(str, Enum):
    """Types of bulk operations"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    REORDER = "reorder"

class BulkOperationStatus(str, Enum):
    """Status of individual bulk operation items"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class BulkOperationItem(BaseModel, Generic[T]):
    """Individual item in a bulk operation"""
    id: Optional[str] = Field(None, description="Resource ID (required for update/delete)")
    data: Optional[T] = Field(None, description="Resource data (required for create/update)")
    operation: BulkOperationType = Field(..., description="Operation type")
    
    @validator('id')
    def validate_id_for_operation(cls, v, values):
        """Validate ID requirements based on operation type"""
        operation = values.get('operation')
        if operation in [BulkOperationType.UPDATE, BulkOperationType.DELETE] and not v:
            raise ValueError(f"ID is required for {operation} operations")
        return v
    
    @validator('data')
    def validate_data_for_operation(cls, v, values):
        """Validate data requirements based on operation type"""
        operation = values.get('operation')
        if operation in [BulkOperationType.CREATE, BulkOperationType.UPDATE] and not v:
            raise ValueError(f"Data is required for {operation} operations")
        return v

class BulkOperationRequest(BaseModel, Generic[T]):
    """Request for bulk operations"""
    items: List[BulkOperationItem[T]] = Field(..., min_items=1, max_items=100, description="List of operations to perform")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional options for the bulk operation")
    
    @validator('items')
    def validate_items_limit(cls, v):
        """Ensure reasonable limits on bulk operations"""
        if len(v) > 100:
            raise ValueError("Maximum 100 items allowed per bulk operation")
        return v

class BulkOperationResultItem(BaseModel):
    """Result of an individual bulk operation item"""
    id: Optional[str] = Field(None, description="Resource ID")
    status: BulkOperationStatus = Field(..., description="Operation status")
    error: Optional[str] = Field(None, description="Error message if operation failed")
    data: Optional[Dict[str, Any]] = Field(None, description="Resulting resource data")
    operation: BulkOperationType = Field(..., description="Operation that was performed")

class BulkOperationResult(BaseModel):
    """Result of a bulk operation"""
    total_items: int = Field(..., description="Total number of items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    skipped: int = Field(..., description="Number of skipped operations")
    items: List[BulkOperationResultItem] = Field(..., description="Results for each item")
    errors: List[str] = Field(default_factory=list, description="General errors not tied to specific items")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.successful / self.total_items) * 100

# Specialized bulk operation schemas for different resources

class BulkDeleteRequest(BaseModel):
    """Request for bulk deletion"""
    ids: List[str] = Field(..., min_items=1, max_items=100, description="List of resource IDs to delete")
    force: bool = Field(False, description="Force deletion even if there are dependencies")
    
    @validator('ids')
    def validate_ids_limit(cls, v):
        """Ensure reasonable limits on bulk deletions"""
        if len(v) > 100:
            raise ValueError("Maximum 100 items allowed per bulk deletion")
        return v

class BulkUpdateRequest(BaseModel, Generic[T]):
    """Request for bulk updates"""
    updates: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100, description="List of update operations")
    
    class UpdateItem(BaseModel):
        id: str = Field(..., description="Resource ID to update")
        data: Dict[str, Any] = Field(..., description="Fields to update")
    
    @validator('updates')
    def validate_updates_limit(cls, v):
        """Ensure reasonable limits on bulk updates"""
        if len(v) > 100:
            raise ValueError("Maximum 100 items allowed per bulk update")
        return v

class BulkReorderRequest(BaseModel):
    """Request for bulk reordering"""
    items: List[Dict[str, Union[str, int]]] = Field(..., min_items=1, description="List of items with new positions")
    
    class ReorderItem(BaseModel):
        id: str = Field(..., description="Resource ID")
        seq: int = Field(..., ge=1, description="New sequence number")
    
    @validator('items')
    def validate_reorder_items(cls, v):
        """Validate reorder items"""
        if len(v) > 100:
            raise ValueError("Maximum 100 items allowed per bulk reorder")
        
        # Check for duplicate IDs
        ids = [item.get('id') for item in v if item.get('id')]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate IDs found in reorder request")
        
        # Check for duplicate sequence numbers
        seqs = [item.get('seq') for item in v if item.get('seq')]
        if len(seqs) != len(set(seqs)):
            raise ValueError("Duplicate sequence numbers found in reorder request")
        
        return v

# Utility functions for bulk operations

def create_bulk_result(
    items: List[BulkOperationResultItem],
    errors: Optional[List[str]] = None
) -> BulkOperationResult:
    """Create a bulk operation result from individual item results"""
    if errors is None:
        errors = []
    
    total_items = len(items)
    successful = len([item for item in items if item.status == BulkOperationStatus.SUCCESS])
    failed = len([item for item in items if item.status == BulkOperationStatus.FAILED])
    skipped = len([item for item in items if item.status == BulkOperationStatus.SKIPPED])
    
    return BulkOperationResult(
        total_items=total_items,
        successful=successful,
        failed=failed,
        skipped=skipped,
        items=items,
        errors=errors
    )

def validate_bulk_permissions(user_id: str, resource_ids: List[str], resource_type: str) -> List[str]:
    """
    Validate that user has permissions for bulk operations on resources.
    Returns list of resource IDs that user doesn't have permission for.
    """
    # This would be implemented based on your authorization logic
    # For now, return empty list (assuming all permissions are valid)
    return []

class BulkOperationLimits:
    """Configuration for bulk operation limits"""
    MAX_ITEMS_PER_REQUEST = 100
    MAX_CONCURRENT_OPERATIONS = 10
    TIMEOUT_SECONDS = 300  # 5 minutes
    
    # Resource-specific limits
    STOPS_MAX_BULK = 50
    DAYS_MAX_BULK = 20
    TRIPS_MAX_BULK = 10
