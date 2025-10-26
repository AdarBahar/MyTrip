"""
Bulk operations service for efficient batch processing
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Type, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.schemas.bulk import (
    BulkOperationResult, BulkOperationResultItem, BulkOperationStatus,
    BulkOperationType, create_bulk_result, BulkOperationLimits
)

logger = logging.getLogger(__name__)

class BulkOperationService:
    """Service for handling bulk operations across different resources"""
    
    def __init__(self, db: Session):
        self.db = db
        self.limits = BulkOperationLimits()
    
    async def bulk_delete(
        self,
        model_class: Type,
        ids: List[str],
        user_id: str,
        force: bool = False,
        pre_delete_hook: Optional[Callable] = None,
        post_delete_hook: Optional[Callable] = None
    ) -> BulkOperationResult:
        """
        Perform bulk deletion of resources
        
        Args:
            model_class: SQLAlchemy model class
            ids: List of resource IDs to delete
            user_id: ID of user performing the operation
            force: Whether to force deletion despite dependencies
            pre_delete_hook: Optional function to call before each deletion
            post_delete_hook: Optional function to call after each deletion
        """
        results = []
        errors = []
        
        # Validate limits
        if len(ids) > self.limits.MAX_ITEMS_PER_REQUEST:
            errors.append(f"Too many items: {len(ids)}. Maximum allowed: {self.limits.MAX_ITEMS_PER_REQUEST}")
            return create_bulk_result([], errors)
        
        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(ids))
        
        for resource_id in unique_ids:
            try:
                # Find the resource
                resource = self.db.query(model_class).filter(model_class.id == resource_id).first()
                
                if not resource:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Resource not found",
                        operation=BulkOperationType.DELETE
                    ))
                    continue
                
                # Check ownership/permissions (if model has created_by or similar)
                if hasattr(resource, 'created_by') and resource.created_by != user_id:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Permission denied",
                        operation=BulkOperationType.DELETE
                    ))
                    continue
                
                # Pre-delete hook
                if pre_delete_hook:
                    try:
                        await pre_delete_hook(resource)
                    except Exception as e:
                        results.append(BulkOperationResultItem(
                            id=resource_id,
                            status=BulkOperationStatus.FAILED,
                            error=f"Pre-delete hook failed: {str(e)}",
                            operation=BulkOperationType.DELETE
                        ))
                        continue
                
                # Perform deletion (soft delete if supported, hard delete otherwise)
                if hasattr(resource, 'soft_delete'):
                    resource.soft_delete()
                else:
                    self.db.delete(resource)
                
                # Post-delete hook
                if post_delete_hook:
                    try:
                        await post_delete_hook(resource)
                    except Exception as e:
                        logger.warning(f"Post-delete hook failed for {resource_id}: {e}")
                
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.SUCCESS,
                    operation=BulkOperationType.DELETE
                ))
                
            except IntegrityError as e:
                self.db.rollback()
                error_msg = "Cannot delete: resource has dependencies" if not force else f"Integrity error: {str(e)}"
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.FAILED,
                    error=error_msg,
                    operation=BulkOperationType.DELETE
                ))
            except Exception as e:
                self.db.rollback()
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.FAILED,
                    error=str(e),
                    operation=BulkOperationType.DELETE
                ))
        
        # Commit all successful deletions
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            errors.append(f"Failed to commit bulk deletion: {str(e)}")
            # Mark all as failed
            for result in results:
                if result.status == BulkOperationStatus.SUCCESS:
                    result.status = BulkOperationStatus.FAILED
                    result.error = "Transaction commit failed"
        
        return create_bulk_result(results, errors)
    
    async def bulk_update(
        self,
        model_class: Type,
        updates: List[Dict[str, Any]],
        user_id: str,
        allowed_fields: Optional[List[str]] = None,
        pre_update_hook: Optional[Callable] = None,
        post_update_hook: Optional[Callable] = None
    ) -> BulkOperationResult:
        """
        Perform bulk updates of resources
        
        Args:
            model_class: SQLAlchemy model class
            updates: List of update operations with 'id' and 'data' keys
            user_id: ID of user performing the operation
            allowed_fields: List of fields that can be updated
            pre_update_hook: Optional function to call before each update
            post_update_hook: Optional function to call after each update
        """
        results = []
        errors = []
        
        # Validate limits
        if len(updates) > self.limits.MAX_ITEMS_PER_REQUEST:
            errors.append(f"Too many items: {len(updates)}. Maximum allowed: {self.limits.MAX_ITEMS_PER_REQUEST}")
            return create_bulk_result([], errors)
        
        for update_item in updates:
            resource_id = update_item.get('id')
            update_data = update_item.get('data', {})
            
            if not resource_id:
                results.append(BulkOperationResultItem(
                    id=None,
                    status=BulkOperationStatus.FAILED,
                    error="Missing resource ID",
                    operation=BulkOperationType.UPDATE
                ))
                continue
            
            try:
                # Find the resource
                resource = self.db.query(model_class).filter(model_class.id == resource_id).first()
                
                if not resource:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Resource not found",
                        operation=BulkOperationType.UPDATE
                    ))
                    continue
                
                # Check ownership/permissions
                if hasattr(resource, 'created_by') and resource.created_by != user_id:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Permission denied",
                        operation=BulkOperationType.UPDATE
                    ))
                    continue
                
                # Filter allowed fields
                if allowed_fields:
                    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
                    if len(filtered_data) != len(update_data):
                        logger.warning(f"Some fields filtered out for update {resource_id}")
                    update_data = filtered_data
                
                # Pre-update hook
                if pre_update_hook:
                    try:
                        update_data = await pre_update_hook(resource, update_data) or update_data
                    except Exception as e:
                        results.append(BulkOperationResultItem(
                            id=resource_id,
                            status=BulkOperationStatus.FAILED,
                            error=f"Pre-update hook failed: {str(e)}",
                            operation=BulkOperationType.UPDATE
                        ))
                        continue
                
                # Apply updates
                for field, value in update_data.items():
                    if hasattr(resource, field):
                        setattr(resource, field, value)
                
                # Update timestamp if available
                if hasattr(resource, 'updated_at'):
                    from datetime import datetime
                    resource.updated_at = datetime.utcnow()
                
                # Post-update hook
                if post_update_hook:
                    try:
                        await post_update_hook(resource, update_data)
                    except Exception as e:
                        logger.warning(f"Post-update hook failed for {resource_id}: {e}")
                
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.SUCCESS,
                    operation=BulkOperationType.UPDATE,
                    data={"updated_fields": list(update_data.keys())}
                ))
                
            except Exception as e:
                self.db.rollback()
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.FAILED,
                    error=str(e),
                    operation=BulkOperationType.UPDATE
                ))
        
        # Commit all successful updates
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            errors.append(f"Failed to commit bulk update: {str(e)}")
            # Mark all as failed
            for result in results:
                if result.status == BulkOperationStatus.SUCCESS:
                    result.status = BulkOperationStatus.FAILED
                    result.error = "Transaction commit failed"
        
        return create_bulk_result(results, errors)
    
    async def bulk_reorder(
        self,
        model_class: Type,
        reorder_items: List[Dict[str, Any]],
        user_id: str,
        sequence_field: str = 'seq',
        scope_field: Optional[str] = None,
        scope_value: Optional[str] = None
    ) -> BulkOperationResult:
        """
        Perform bulk reordering of resources
        
        Args:
            model_class: SQLAlchemy model class
            reorder_items: List with 'id' and 'seq' for new positions
            user_id: ID of user performing the operation
            sequence_field: Name of the sequence field (default: 'seq')
            scope_field: Optional field to scope reordering (e.g., 'day_id')
            scope_value: Value for the scope field
        """
        results = []
        errors = []
        
        try:
            # Build base query
            query = self.db.query(model_class)
            if scope_field and scope_value:
                query = query.filter(getattr(model_class, scope_field) == scope_value)
            
            # Get all resources in scope
            resources = {r.id: r for r in query.all()}
            
            # Validate all IDs exist and user has permission
            for item in reorder_items:
                resource_id = item.get('id')
                new_seq = item.get('seq')
                
                if not resource_id or new_seq is None:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Missing ID or sequence number",
                        operation=BulkOperationType.REORDER
                    ))
                    continue
                
                resource = resources.get(resource_id)
                if not resource:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Resource not found",
                        operation=BulkOperationType.REORDER
                    ))
                    continue
                
                # Check permissions
                if hasattr(resource, 'created_by') and resource.created_by != user_id:
                    results.append(BulkOperationResultItem(
                        id=resource_id,
                        status=BulkOperationStatus.FAILED,
                        error="Permission denied",
                        operation=BulkOperationType.REORDER
                    ))
                    continue
                
                # Update sequence
                setattr(resource, sequence_field, new_seq)
                results.append(BulkOperationResultItem(
                    id=resource_id,
                    status=BulkOperationStatus.SUCCESS,
                    operation=BulkOperationType.REORDER,
                    data={"new_sequence": new_seq}
                ))
            
            # Commit all changes
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            errors.append(f"Failed to reorder resources: {str(e)}")
            # Mark all as failed
            for result in results:
                if result.status == BulkOperationStatus.SUCCESS:
                    result.status = BulkOperationStatus.FAILED
                    result.error = "Reorder transaction failed"
        
        return create_bulk_result(results, errors)
