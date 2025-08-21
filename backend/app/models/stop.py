"""
Stop model
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, Enum, ForeignKey,
    UniqueConstraint, CheckConstraint, Text
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class StopKind(str, enum.Enum):
    START = "start"
    VIA = "via"
    END = "end"


class Stop(BaseModel):
    """Stop model"""

    __tablename__ = "stops"

    day_id = Column(String(26), ForeignKey("days.id"), nullable=False)
    trip_id = Column(String(26), ForeignKey("trips.id"), nullable=False)
    place_id = Column(String(26), ForeignKey("places.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    kind = Column(Enum(StopKind), nullable=False)
    fixed = Column(Boolean, default=False, nullable=False)
    notes = Column(Text)

    # Relationships
    day = relationship("Day", back_populates="stops")
    trip = relationship("Trip")
    place = relationship("Place", back_populates="stops")

    __table_args__ = (
        UniqueConstraint("day_id", "seq", name="uq_stop_day_seq"),
        CheckConstraint("seq > 0", name="ck_stop_seq_positive"),
        # Constraint: exactly one start at seq=1 with fixed=true
        CheckConstraint(
            "(kind != 'start') OR (seq = 1 AND fixed = true)",
            name="ck_stop_start_constraints"
        ),
        # Constraint: end stops must be fixed
        CheckConstraint(
            "(kind != 'end') OR (fixed = true)",
            name="ck_stop_end_fixed"
        ),
    )

    def __repr__(self):
        return f"<Stop(id={self.id}, day_id={self.day_id}, seq={self.seq}, kind={self.kind})>"