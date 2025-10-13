"""
User model
"""
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(BaseModel):
    """User model"""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Optional for backward compatibility
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

    # Relationships
    created_trips = relationship("Trip", back_populates="created_by_user")
    trip_memberships = relationship("TripMember", back_populates="user")
    route_versions = relationship("RouteVersion", back_populates="created_by_user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"