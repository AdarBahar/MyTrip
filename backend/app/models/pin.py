"""
Pin model
"""
from sqlalchemy import Column, String, Numeric, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Pin(BaseModel):
    """Pin model"""

    __tablename__ = "pins"

    trip_id = Column(String(26), ForeignKey("trips.id"), nullable=False)
    place_id = Column(String(26), ForeignKey("places.id"), nullable=True)
    name = Column(String(255), nullable=False)
    lat = Column(Numeric(precision=10, scale=7), nullable=False)
    lon = Column(Numeric(precision=10, scale=7), nullable=False)
    order_index = Column(Integer)
    meta = Column(JSON)

    # Relationships
    trip = relationship("Trip", back_populates="pins")
    place = relationship("Place", back_populates="pins")

    def __repr__(self):
        return f"<Pin(id={self.id}, name={self.name}, trip_id={self.trip_id})>"