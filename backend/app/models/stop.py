"""
Stop model
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, Enum, ForeignKey,
    UniqueConstraint, CheckConstraint, Text, Time, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class StopKind(str, enum.Enum):
    """
    Route planning stop types for navigation

    Defines the role of a stop in route calculation and optimization.
    Used by routing algorithms to determine stop order and constraints.
    """
    START = "START"    # 🚀 Starting point of the route (fixed position)
    VIA = "VIA"        # 📍 Intermediate waypoint (can be optimized)
    END = "END"        # 🏁 Final destination (fixed position)


class StopType(str, enum.Enum):
    """
    User-friendly stop categories for trip organization

    Categorizes stops by their purpose and type to help with
    trip planning, filtering, and organization.
    """
    ACCOMMODATION = "ACCOMMODATION"  # 🏨 Hotels, hostels, vacation rentals, camping
    FOOD = "FOOD"                   # 🍽️ Restaurants, cafes, food markets, bars
    ATTRACTION = "ATTRACTION"       # 🎭 Museums, landmarks, tourist sites, monuments
    ACTIVITY = "ACTIVITY"          # 🎯 Tours, experiences, entertainment, sports
    SHOPPING = "SHOPPING"          # 🛍️ Stores, markets, shopping centers, outlets
    GAS = "GAS"                    # ⛽ Gas stations, EV charging stations, fuel stops
    TRANSPORT = "TRANSPORT"        # 🚌 Airports, train stations, bus stops, ports
    SERVICES = "SERVICES"          # 🏦 Banks, post offices, government offices, repair
    NATURE = "NATURE"              # 🌲 Parks, beaches, hiking trails, scenic viewpoints
    CULTURE = "CULTURE"            # 🎨 Museums, theaters, galleries, cultural sites
    NIGHTLIFE = "NIGHTLIFE"        # 🌙 Bars, clubs, entertainment venues, live music
    OTHER = "OTHER"                # 📌 Miscellaneous stops not fitting other categories


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

    # Enhanced stop management fields
    stop_type = Column(Enum(StopType), default=StopType.OTHER, nullable=False)
    arrival_time = Column(Time, nullable=True)
    departure_time = Column(Time, nullable=True)
    duration_minutes = Column(Integer, nullable=True)  # Planned duration at stop
    booking_info = Column(JSON, nullable=True)  # Reservation details, confirmation numbers
    contact_info = Column(JSON, nullable=True)  # Phone, website, email
    cost_info = Column(JSON, nullable=True)     # Estimated costs, actual costs
    priority = Column(Integer, default=3, nullable=False)  # 1=must-see, 2=important, 3=nice-to-have, 4=optional, 5=backup

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