"""
Location SQLAlchemy models

Database models for location-related functionality.
Uses separate location database with different credentials.
These models will be customized based on your PHP database schema.
"""

from sqlalchemy import DECIMAL, JSON, Boolean, Column, Index, String, Text

from app.models.location_base import LocationBaseModel, LocationSoftDeleteMixin


class Location(LocationBaseModel, LocationSoftDeleteMixin):
    """
    Location model for separate location database

    This model will be customized based on your PHP database schema.
    Common location fields are included as examples.
    """

    __tablename__ = "locations"

    # Basic location information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    country = Column(String(100), nullable=True, index=True)

    # Geographic coordinates
    latitude = Column(DECIMAL(10, 8), nullable=True, index=True)
    longitude = Column(DECIMAL(11, 8), nullable=True, index=True)

    # Categorization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # Store as JSON array

    # Additional data
    extra_data = Column(
        JSON, nullable=True
    )  # Flexible metadata storage (renamed from 'metadata' to avoid SQLAlchemy conflict)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # User reference (no foreign key since users table is in different database)
    created_by = Column(
        String(26), nullable=False, index=True
    )  # ULID of user from main database

    # Add more relationships based on your PHP schema:
    # favorites = relationship("LocationFavorite", back_populates="location")
    # reviews = relationship("LocationReview", back_populates="location")
    # visits = relationship("LocationVisit", back_populates="location")

    # Database indexes for performance
    __table_args__ = (
        # Composite index for geographic searches
        Index("idx_location_coordinates", "latitude", "longitude"),
        # Composite index for user's locations
        Index("idx_location_user_active", "created_by", "is_active"),
        # Full-text search index (if supported by your MySQL version)
        Index("idx_location_search", "name", "description", mysql_prefix="FULLTEXT"),
    )

    def __repr__(self):
        return f"<Location(id={self.id}, name={self.name})>"

    @property
    def has_coordinates(self) -> bool:
        """Check if location has valid coordinates"""
        return self.latitude is not None and self.longitude is not None

    def distance_to(self, other_lat: float, other_lng: float) -> float:
        """
        Calculate distance to another point using Haversine formula
        Returns distance in kilometers
        """
        if not self.has_coordinates:
            return float("inf")

        import math

        # Convert to radians
        lat1, lng1 = math.radians(float(self.latitude)), math.radians(
            float(self.longitude)
        )
        lat2, lng2 = math.radians(other_lat), math.radians(other_lng)

        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # Earth's radius in kilometers
        r = 6371

        return c * r


# Example additional models based on common location features
# Uncomment and customize based on your PHP schema:

# class LocationFavorite(BaseModel):
#     """User's favorite locations"""
#
#     __tablename__ = "location_favorites"
#
#     user_id = Column(String(26), ForeignKey("users.id"), nullable=False)
#     location_id = Column(String(26), ForeignKey("locations.id"), nullable=False)
#
#     # Relationships
#     user = relationship("User", back_populates="favorite_locations")
#     location = relationship("Location", back_populates="favorites")
#
#     __table_args__ = (
#         Index('idx_favorite_user_location', 'user_id', 'location_id', unique=True),
#     )


# class LocationReview(BaseModel, SoftDeleteMixin):
#     """User reviews for locations"""
#
#     __tablename__ = "location_reviews"
#
#     location_id = Column(String(26), ForeignKey("locations.id"), nullable=False)
#     user_id = Column(String(26), ForeignKey("users.id"), nullable=False)
#     rating = Column(Integer, nullable=False)  # 1-5 stars
#     review_text = Column(Text, nullable=True)
#
#     # Relationships
#     location = relationship("Location", back_populates="reviews")
#     user = relationship("User", back_populates="location_reviews")
#
#     __table_args__ = (
#         Index('idx_review_location', 'location_id'),
#         Index('idx_review_user', 'user_id'),
#         CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating'),
#     )


# class LocationVisit(BaseModel):
#     """Track user visits to locations"""
#
#     __tablename__ = "location_visits"
#
#     location_id = Column(String(26), ForeignKey("locations.id"), nullable=False)
#     user_id = Column(String(26), ForeignKey("users.id"), nullable=False)
#     visit_date = Column(DateTime(timezone=True), nullable=False)
#     notes = Column(Text, nullable=True)
#
#     # Relationships
#     location = relationship("Location", back_populates="visits")
#     user = relationship("User", back_populates="location_visits")
#
#     __table_args__ = (
#         Index('idx_visit_location_date', 'location_id', 'visit_date'),
#         Index('idx_visit_user_date', 'user_id', 'visit_date'),
#     )
