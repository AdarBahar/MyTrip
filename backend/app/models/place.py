"""
Place model
"""
from sqlalchemy import Column, String, Numeric, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class OwnerType(str, enum.Enum):
    USER = "user"
    TRIP = "trip"
    SYSTEM = "system"


class Place(BaseModel):
    """Place model"""

    __tablename__ = "places"

    owner_type = Column(Enum(OwnerType), nullable=False)
    owner_id = Column(String(26), nullable=False)
    provider_place_id = Column(String(255))
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    lat = Column(Numeric(precision=10, scale=7), nullable=False)
    lon = Column(Numeric(precision=10, scale=7), nullable=False)
    meta = Column(JSON)

    # Relationships
    stops = relationship("Stop", back_populates="place")
    pins = relationship("Pin", back_populates="place")

    def __repr__(self):
        return f"<Place(id={self.id}, name={self.name})>"