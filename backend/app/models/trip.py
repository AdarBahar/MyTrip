"""
Trip and TripMember models
"""
from sqlalchemy import (
    Column, String, Date, Boolean, Enum, ForeignKey,
    UniqueConstraint, DateTime
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class TripStatus(str, enum.Enum):
    """
    Trip planning and execution status

    Represents the current state of a trip throughout its lifecycle,
    from initial planning to completion and archival.
    """
    DRAFT = "draft"        # 📝 Trip is being planned - editable, not confirmed
    ACTIVE = "active"      # ✈️ Trip is currently happening or confirmed for travel
    COMPLETED = "completed"  # ✅ Trip has been completed successfully
    ARCHIVED = "archived"  # 📦 Trip has been archived for reference only


class TripMemberRole(str, enum.Enum):
    """
    Trip collaboration roles and permissions

    Defines the level of access and permissions for trip members
    in collaborative trip planning scenarios.
    """
    OWNER = "owner"      # 👑 Full control - can edit, delete, and manage members
    EDITOR = "editor"    # ✏️ Can edit trip content but not manage members
    VIEWER = "viewer"    # 👀 Read-only access to trip information


class TripMemberStatus(str, enum.Enum):
    """
    Trip member invitation and participation status

    Tracks the current state of a user's membership in a trip,
    from invitation through active participation.
    """
    ACTIVE = "active"      # ✅ Member is actively participating in trip planning
    PENDING = "pending"    # ⏳ Invitation sent but not yet accepted
    REMOVED = "removed"    # ❌ Member has been removed or left the trip


class Trip(BaseModel, SoftDeleteMixin):
    """Trip model"""

    __tablename__ = "trips"

    slug = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    destination = Column(String(255))
    start_date = Column(Date)
    timezone = Column(String(50))
    status = Column(Enum(TripStatus, values_callable=lambda obj: [e.value for e in obj]), default=TripStatus.ACTIVE, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    created_by = Column(String(26), ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by_user = relationship("User", back_populates="created_trips")
    members = relationship("TripMember", back_populates="trip")
    days = relationship("Day", back_populates="trip")
    pins = relationship("Pin", back_populates="trip")

    __table_args__ = (
        UniqueConstraint("slug", "created_by", name="uq_trip_slug_creator"),
    )

    def __repr__(self):
        return f"<Trip(id={self.id}, title={self.title})>"


class TripMember(BaseModel):
    """Trip member model"""

    __tablename__ = "trip_members"

    trip_id = Column(String(26), ForeignKey("trips.id"), nullable=False)
    user_id = Column(String(26), ForeignKey("users.id"), nullable=True)
    invited_email = Column(String(255), nullable=True)
    role = Column(Enum(TripMemberRole), nullable=False)
    status = Column(Enum(TripMemberStatus), default=TripMemberStatus.PENDING, nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="members")
    user = relationship("User", back_populates="trip_memberships")

    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", name="uq_trip_member_user"),
        UniqueConstraint("trip_id", "invited_email", name="uq_trip_member_email"),
    )

    def __repr__(self):
        return f"<TripMember(trip_id={self.trip_id}, user_id={self.user_id}, role={self.role})>"