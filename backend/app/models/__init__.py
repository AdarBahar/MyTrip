"""
Database models
"""
from app.core.database import Base
from app.models.base import BaseModel, TimestampMixin, ULIDMixin, SoftDeleteMixin

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.trip import Trip, TripMember
from app.models.day import Day
from app.models.place import Place
from app.models.stop import Stop
from app.models.route import RouteVersion, RouteLeg
from app.models.pin import Pin
from app.models.user_setting import UserSetting

__all__ = [
    "Base",
    "BaseModel",
    "TimestampMixin",
    "ULIDMixin",
    "SoftDeleteMixin",
    "User",
    "Trip",
    "TripMember",
    "Day",
    "Place",
    "Stop",
    "RouteVersion",
    "RouteLeg",
    "Pin",
]