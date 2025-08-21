"""
Day model
"""
from sqlalchemy import (
    Column, String, Integer, Date, Boolean, Enum, ForeignKey,
    UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class DayStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Day(BaseModel, SoftDeleteMixin):
    """Day model"""

    __tablename__ = "days"

    trip_id = Column(String(26), ForeignKey("trips.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    date = Column(Date)
    status = Column(Enum(DayStatus), default=DayStatus.ACTIVE, nullable=False)
    rest_day = Column(Boolean, default=False, nullable=False)
    notes = Column(JSON)

    # Relationships
    trip = relationship("Trip", back_populates="days")
    stops = relationship("Stop", back_populates="day")
    route_versions = relationship("RouteVersion", back_populates="day")

    __table_args__ = (
        UniqueConstraint("trip_id", "seq", name="uq_day_trip_seq"),
        CheckConstraint("seq > 0", name="ck_day_seq_positive"),
    )

    def __repr__(self):
        return f"<Day(id={self.id}, trip_id={self.trip_id}, seq={self.seq})>"