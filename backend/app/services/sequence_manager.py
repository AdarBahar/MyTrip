"""
Sequence management service for automatic ordering and conflict resolution
"""
import logging
from typing import List, Optional, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from enum import Enum

logger = logging.getLogger(__name__)

class SequenceOperation(str, Enum):
    """Types of sequence operations"""
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_TO_TOP = "move_to_top"
    MOVE_TO_BOTTOM = "move_to_bottom"
    INSERT_AFTER = "insert_after"
    INSERT_BEFORE = "insert_before"
    MOVE_TO_POSITION = "move_to_position"

class SequenceManager:
    """Service for managing sequence numbers and automatic reordering"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_next_sequence(
        self,
        model_class: Type,
        scope_filters: Optional[Dict[str, Any]] = None,
        sequence_field: str = 'seq'
    ) -> int:
        """
        Get the next available sequence number in a scope
        
        Args:
            model_class: SQLAlchemy model class
            scope_filters: Dictionary of field->value filters for scoping
            sequence_field: Name of the sequence field
            
        Returns:
            Next available sequence number
        """
        query = self.db.query(func.max(getattr(model_class, sequence_field)))
        
        if scope_filters:
            for field, value in scope_filters.items():
                query = query.filter(getattr(model_class, field) == value)
        
        max_seq = query.scalar()
        return (max_seq or 0) + 1
    
    def reorder_sequence(
        self,
        model_class: Type,
        item_id: str,
        operation: SequenceOperation,
        target_id: Optional[str] = None,
        target_position: Optional[int] = None,
        scope_filters: Optional[Dict[str, Any]] = None,
        sequence_field: str = 'seq'
    ) -> Dict[str, Any]:
        """
        Perform sequence reordering operation
        
        Args:
            model_class: SQLAlchemy model class
            item_id: ID of item to move
            operation: Type of sequence operation
            target_id: ID of target item (for insert_after/insert_before)
            target_position: Target position (for move_to_position)
            scope_filters: Dictionary of field->value filters for scoping
            sequence_field: Name of the sequence field
            
        Returns:
            Dictionary with operation results
        """
        try:
            # Get the item to move
            item = self.db.query(model_class).filter(model_class.id == item_id).first()
            if not item:
                raise ValueError(f"Item {item_id} not found")
            
            current_seq = getattr(item, sequence_field)
            
            # Build base query for items in same scope
            query = self.db.query(model_class)
            if scope_filters:
                for field, value in scope_filters.items():
                    query = query.filter(getattr(model_class, field) == value)
            
            # Get all items in scope ordered by sequence
            all_items = query.order_by(getattr(model_class, sequence_field)).all()
            
            # Perform the requested operation
            if operation == SequenceOperation.MOVE_UP:
                new_seq = self._move_up(item, all_items, sequence_field)
            elif operation == SequenceOperation.MOVE_DOWN:
                new_seq = self._move_down(item, all_items, sequence_field)
            elif operation == SequenceOperation.MOVE_TO_TOP:
                new_seq = self._move_to_top(item, all_items, sequence_field)
            elif operation == SequenceOperation.MOVE_TO_BOTTOM:
                new_seq = self._move_to_bottom(item, all_items, sequence_field)
            elif operation == SequenceOperation.INSERT_AFTER:
                new_seq = self._insert_after(item, target_id, all_items, sequence_field)
            elif operation == SequenceOperation.INSERT_BEFORE:
                new_seq = self._insert_before(item, target_id, all_items, sequence_field)
            elif operation == SequenceOperation.MOVE_TO_POSITION:
                new_seq = self._move_to_position(item, target_position, all_items, sequence_field)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
            
            # Commit the changes
            self.db.commit()
            
            return {
                "success": True,
                "item_id": item_id,
                "old_sequence": current_seq,
                "new_sequence": new_seq,
                "operation": operation.value,
                "affected_items": len([i for i in all_items if getattr(i, sequence_field) != getattr(i, sequence_field)])
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Sequence reorder failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "item_id": item_id,
                "operation": operation.value
            }
    
    def _move_up(self, item: Any, all_items: List[Any], sequence_field: str) -> int:
        """Move item up one position"""
        current_seq = getattr(item, sequence_field)
        
        # Find the item immediately before this one
        prev_item = None
        for i in all_items:
            if getattr(i, sequence_field) < current_seq:
                if prev_item is None or getattr(i, sequence_field) > getattr(prev_item, sequence_field):
                    prev_item = i
        
        if prev_item is None:
            # Already at top
            return current_seq
        
        # Swap sequences
        prev_seq = getattr(prev_item, sequence_field)
        setattr(item, sequence_field, prev_seq)
        setattr(prev_item, sequence_field, current_seq)
        
        return prev_seq
    
    def _move_down(self, item: Any, all_items: List[Any], sequence_field: str) -> int:
        """Move item down one position"""
        current_seq = getattr(item, sequence_field)
        
        # Find the item immediately after this one
        next_item = None
        for i in all_items:
            if getattr(i, sequence_field) > current_seq:
                if next_item is None or getattr(i, sequence_field) < getattr(next_item, sequence_field):
                    next_item = i
        
        if next_item is None:
            # Already at bottom
            return current_seq
        
        # Swap sequences
        next_seq = getattr(next_item, sequence_field)
        setattr(item, sequence_field, next_seq)
        setattr(next_item, sequence_field, current_seq)
        
        return next_seq
    
    def _move_to_top(self, item: Any, all_items: List[Any], sequence_field: str) -> int:
        """Move item to top position"""
        current_seq = getattr(item, sequence_field)
        
        # Shift all items with sequence < current_seq up by 1
        for i in all_items:
            item_seq = getattr(i, sequence_field)
            if item_seq < current_seq:
                setattr(i, sequence_field, item_seq + 1)
        
        # Set item to position 1
        setattr(item, sequence_field, 1)
        return 1
    
    def _move_to_bottom(self, item: Any, all_items: List[Any], sequence_field: str) -> int:
        """Move item to bottom position"""
        current_seq = getattr(item, sequence_field)
        max_seq = max(getattr(i, sequence_field) for i in all_items)
        
        # Shift all items with sequence > current_seq down by 1
        for i in all_items:
            item_seq = getattr(i, sequence_field)
            if item_seq > current_seq:
                setattr(i, sequence_field, item_seq - 1)
        
        # Set item to bottom position
        new_seq = max_seq
        setattr(item, sequence_field, new_seq)
        return new_seq
    
    def _insert_after(self, item: Any, target_id: str, all_items: List[Any], sequence_field: str) -> int:
        """Insert item after target item"""
        if not target_id:
            raise ValueError("target_id is required for insert_after operation")
        
        # Find target item
        target_item = next((i for i in all_items if i.id == target_id), None)
        if not target_item:
            raise ValueError(f"Target item {target_id} not found")
        
        target_seq = getattr(target_item, sequence_field)
        current_seq = getattr(item, sequence_field)
        new_seq = target_seq + 1
        
        # Shift items to make room
        for i in all_items:
            item_seq = getattr(i, sequence_field)
            if i.id != item.id:  # Don't move the item being repositioned
                if item_seq >= new_seq and current_seq > item_seq:
                    # Items between new position and old position move up
                    setattr(i, sequence_field, item_seq + 1)
                elif item_seq >= new_seq and current_seq < item_seq:
                    # Items after new position move down
                    setattr(i, sequence_field, item_seq + 1)
        
        setattr(item, sequence_field, new_seq)
        return new_seq
    
    def _insert_before(self, item: Any, target_id: str, all_items: List[Any], sequence_field: str) -> int:
        """Insert item before target item"""
        if not target_id:
            raise ValueError("target_id is required for insert_before operation")
        
        # Find target item
        target_item = next((i for i in all_items if i.id == target_id), None)
        if not target_item:
            raise ValueError(f"Target item {target_id} not found")
        
        target_seq = getattr(target_item, sequence_field)
        current_seq = getattr(item, sequence_field)
        new_seq = target_seq
        
        # Shift items to make room
        for i in all_items:
            item_seq = getattr(i, sequence_field)
            if i.id != item.id:  # Don't move the item being repositioned
                if item_seq >= new_seq:
                    setattr(i, sequence_field, item_seq + 1)
        
        setattr(item, sequence_field, new_seq)
        return new_seq
    
    def _move_to_position(self, item: Any, target_position: int, all_items: List[Any], sequence_field: str) -> int:
        """Move item to specific position"""
        if target_position is None or target_position < 1:
            raise ValueError("target_position must be a positive integer")
        
        current_seq = getattr(item, sequence_field)
        max_seq = max(getattr(i, sequence_field) for i in all_items)
        
        # Clamp target position to valid range
        target_position = min(target_position, max_seq)
        
        if current_seq == target_position:
            return current_seq
        
        # Shift other items
        for i in all_items:
            if i.id == item.id:
                continue
                
            item_seq = getattr(i, sequence_field)
            
            if current_seq < target_position:
                # Moving down: shift items between current and target up
                if current_seq < item_seq <= target_position:
                    setattr(i, sequence_field, item_seq - 1)
            else:
                # Moving up: shift items between target and current down
                if target_position <= item_seq < current_seq:
                    setattr(i, sequence_field, item_seq + 1)
        
        setattr(item, sequence_field, target_position)
        return target_position
    
    def normalize_sequences(
        self,
        model_class: Type,
        scope_filters: Optional[Dict[str, Any]] = None,
        sequence_field: str = 'seq'
    ) -> int:
        """
        Normalize sequence numbers to remove gaps and ensure consecutive numbering
        
        Returns:
            Number of items resequenced
        """
        query = self.db.query(model_class)
        
        if scope_filters:
            for field, value in scope_filters.items():
                query = query.filter(getattr(model_class, field) == value)
        
        items = query.order_by(getattr(model_class, sequence_field)).all()
        
        changes = 0
        for i, item in enumerate(items, 1):
            current_seq = getattr(item, sequence_field)
            if current_seq != i:
                setattr(item, sequence_field, i)
                changes += 1
        
        if changes > 0:
            self.db.commit()
            logger.info(f"Normalized {changes} sequence numbers")
        
        return changes
