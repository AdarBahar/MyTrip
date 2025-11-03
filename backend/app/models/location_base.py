"""
Base models for location database
Separate from main database models
"""
import ulid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.core.location_database import LocationBase


class LocationTimestampMixin:
    """Mixin for timestamp fields in location database"""

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class LocationULIDMixin:
    """Mixin for ULID primary key in location database"""

    id = Column(
        String(26), primary_key=True, default=lambda: str(ulid.new()), nullable=False
    )


class LocationSoftDeleteMixin:
    """Mixin for soft delete functionality in location database"""

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted"""
        return self.deleted_at is not None


class LocationBaseModel(LocationBase, LocationTimestampMixin, LocationULIDMixin):
    """
    Base model for location database tables
    Includes ULID primary key and timestamp fields
    """

    __abstract__ = True

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
