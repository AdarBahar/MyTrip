"""
Base model classes and utilities
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declared_attr
from ulid import ULID

from app.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class ULIDMixin:
    """Mixin for ULID primary key"""

    @declared_attr
    def id(cls):
        return Column(String(26), primary_key=True, default=lambda: str(ULID()))


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()


class BaseModel(Base, ULIDMixin, TimestampMixin):
    """Base model class with ULID and timestamps"""

    __abstract__ = True