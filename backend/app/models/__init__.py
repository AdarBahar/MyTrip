"""
Database models
"""
from app.core.database import Base
from app.models.base import BaseModel, SoftDeleteMixin, TimestampMixin, ULIDMixin
from app.models.day import Day
from app.models.pin import Pin
from app.models.place import Place
from app.models.route import RouteLeg, RouteVersion
from app.models.stop import Stop
from app.models.trip import Trip, TripMember

# Import all models here to ensure they are registered with SQLAlchemy
from app.models.user import User

# Note: Location model is in separate database - see app.models.location

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
    # Location is in separate database
]
