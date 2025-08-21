"""
Route models
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, Numeric, ForeignKey,
    UniqueConstraint, Index, JSON, Text
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RouteVersion(BaseModel):
    """Route version model"""

    __tablename__ = "route_versions"

    day_id = Column(String(26), ForeignKey("days.id"), nullable=False)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    name = Column(String(255))
    profile_used = Column(String(50))
    total_km = Column(Numeric(precision=10, scale=3))
    total_min = Column(Numeric(precision=10, scale=2))
    geometry_wkt = Column(Text)  # Store geometry as WKT text
    geojson = Column(JSON)
    totals = Column(JSON)
    stop_snapshot = Column(JSON)
    created_by = Column(String(26), ForeignKey("users.id"), nullable=False)

    # Relationships
    day = relationship("Day", back_populates="route_versions")
    created_by_user = relationship("User", back_populates="route_versions")
    legs = relationship("RouteLeg", back_populates="route_version")

    __table_args__ = (
        UniqueConstraint("day_id", "version", name="uq_route_version_day_version"),
        Index("ix_route_version_active", "day_id", "is_active"),
    )

    def __repr__(self):
        return f"<RouteVersion(id={self.id}, day_id={self.day_id}, version={self.version})>"


class RouteLeg(BaseModel):
    """Route leg model"""

    __tablename__ = "route_legs"

    route_version_id = Column(String(26), ForeignKey("route_versions.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    distance_km = Column(Numeric(precision=10, scale=3))
    duration_min = Column(Numeric(precision=10, scale=2))
    geometry_wkt = Column(Text)  # Store geometry as WKT text
    geojson = Column(JSON)
    meta = Column(JSON)

    # Relationships
    route_version = relationship("RouteVersion", back_populates="legs")

    __table_args__ = (
        UniqueConstraint("route_version_id", "seq", name="uq_route_leg_version_seq"),
    )

    def __repr__(self):
        return f"<RouteLeg(id={self.id}, route_version_id={self.route_version_id}, seq={self.seq})>"