"""
Base model classes and utilities with ISO-8601 datetime standardization
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from ulid import ULID

from app.core.database import Base
from app.core.datetime_utils import DateTimeStandards


class TimestampMixin:
    """
    Mixin for created_at and updated_at timestamps with ISO-8601 standardization

    All timestamps are stored in UTC and serialized to ISO-8601 format
    for consistent datetime handling across the API.
    """

    created_at = Column(
        DateTime(timezone=True),
        default=DateTimeStandards.now_utc,
        nullable=False,
        doc="Creation timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=DateTimeStandards.now_utc,
        onupdate=DateTimeStandards.now_utc,
        nullable=False,
        doc="Last update timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)"
    )


class ULIDMixin:
    """Mixin for ULID primary key"""

    @declared_attr
    def id(cls):
        return Column(String(26), primary_key=True, default=lambda: str(ULID()))


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality with ISO-8601 standardization

    Soft delete timestamps are stored in UTC and serialized to ISO-8601 format.
    """

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Soft delete timestamp in UTC (ISO-8601: YYYY-MM-DDTHH:MM:SSZ)"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the record is soft deleted"""
        return self.deleted_at is not None

    def soft_delete(self):
        """Mark the record as soft deleted with current UTC timestamp"""
        self.deleted_at = DateTimeStandards.now_utc()


class BaseModel(Base, ULIDMixin, TimestampMixin):
    """Base model class with ULID and timestamps"""

    __abstract__ = True