"""
Location service layer

Business logic for location-related operations.
This service will be customized based on your PHP business logic.
"""

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.datetime_utils import DateTimeStandards
from app.models.location import Location
from app.schemas.location import LocationCreate, LocationSearchParams, LocationUpdate

logger = logging.getLogger(__name__)


class LocationService:
    """
    Service class for location operations

    This service encapsulates all business logic for location management
    and will be customized based on your PHP implementation.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_locations(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        search_params: Optional[LocationSearchParams] = None,
    ) -> list[Location]:
        """
        Get locations with optional filtering and pagination

        Args:
            user_id: ID of the requesting user
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Simple search term
            search_params: Advanced search parameters

        Returns:
            List of Location objects
        """
        query = self.db.query(Location).filter(Location.deleted_at.is_(None))

        # Apply user-specific filtering if needed
        # Uncomment if locations should be user-specific:
        # query = query.filter(Location.created_by == user_id)

        # Apply simple search
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Location.name.ilike(search_term),
                    Location.description.ilike(search_term),
                    Location.address.ilike(search_term),
                    Location.city.ilike(search_term),
                )
            )

        # Apply advanced search parameters
        if search_params:
            if search_params.category:
                query = query.filter(Location.category == search_params.category)

            if search_params.city:
                query = query.filter(Location.city.ilike(f"%{search_params.city}%"))

            if search_params.country:
                query = query.filter(
                    Location.country.ilike(f"%{search_params.country}%")
                )

            if search_params.is_active is not None:
                query = query.filter(Location.is_active == search_params.is_active)

            # Geographic proximity search
            if (
                search_params.near_lat
                and search_params.near_lng
                and search_params.radius_km
            ):
                # Use Haversine formula for distance calculation
                # This is a simplified version - you might want to use PostGIS for better performance
                lat_rad = func.radians(search_params.near_lat)
                lng_rad = func.radians(search_params.near_lng)
                loc_lat_rad = func.radians(Location.latitude)
                loc_lng_rad = func.radians(Location.longitude)

                distance = 6371 * func.acos(
                    func.cos(lat_rad)
                    * func.cos(loc_lat_rad)
                    * func.cos(loc_lng_rad - lng_rad)
                    + func.sin(lat_rad) * func.sin(loc_lat_rad)
                )

                query = query.filter(distance <= search_params.radius_km)

        # Apply pagination and return results
        return query.offset(skip).limit(limit).all()

    def get_location_by_id(self, location_id: str, user_id: str) -> Optional[Location]:
        """
        Get a location by ID

        Args:
            location_id: Location ID
            user_id: ID of the requesting user

        Returns:
            Location object or None if not found
        """
        query = self.db.query(Location).filter(
            and_(Location.id == location_id, Location.deleted_at.is_(None))
        )

        # Add user-specific filtering if needed
        # Uncomment if locations should be user-specific:
        # query = query.filter(Location.created_by == user_id)

        return query.first()

    def create_location(self, user_id: str, location_data: LocationCreate) -> Location:
        """
        Create a new location

        Args:
            user_id: ID of the user creating the location
            location_data: Location creation data

        Returns:
            Created Location object

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Create location instance
            location = Location(
                name=location_data.name,
                description=location_data.description,
                address=location_data.address,
                city=location_data.city,
                country=location_data.country,
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                category=location_data.category,
                tags=location_data.tags,
                extra_data=location_data.extra_data,
                is_active=location_data.is_active,
                created_by=user_id,
            )

            # Add to database
            self.db.add(location)
            self.db.commit()
            self.db.refresh(location)

            logger.info(f"Created location {location.id} by user {user_id}")
            return location

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create location: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create location",
            )

    def update_location(
        self, location_id: str, user_id: str, location_data: LocationUpdate
    ) -> Optional[Location]:
        """
        Update a location

        Args:
            location_id: Location ID
            user_id: ID of the user updating the location
            location_data: Location update data

        Returns:
            Updated Location object or None if not found

        Raises:
            HTTPException: If update fails
        """
        location = self.get_location_by_id(location_id, user_id)
        if not location:
            return None

        # Check if user has permission to update
        # Uncomment if only creators can update their locations:
        # if location.created_by != user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to update this location"
        #     )

        try:
            # Update fields that are provided
            update_data = location_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(location, field, value)

            # Update timestamp
            location.updated_at = DateTimeStandards.now_utc()

            self.db.commit()
            self.db.refresh(location)

            logger.info(f"Updated location {location_id} by user {user_id}")
            return location

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update location {location_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update location",
            )

    def delete_location(self, location_id: str, user_id: str) -> bool:
        """
        Soft delete a location

        Args:
            location_id: Location ID
            user_id: ID of the user deleting the location

        Returns:
            True if deleted, False if not found

        Raises:
            HTTPException: If deletion fails
        """
        location = self.get_location_by_id(location_id, user_id)
        if not location:
            return False

        # Check if user has permission to delete
        # Uncomment if only creators can delete their locations:
        # if location.created_by != user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to delete this location"
        #     )

        try:
            # Soft delete
            location.deleted_at = DateTimeStandards.now_utc()

            self.db.commit()

            logger.info(f"Deleted location {location_id} by user {user_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete location {location_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete location",
            )

    def get_location_count(
        self,
        user_id: str,
        search: Optional[str] = None,
        search_params: Optional[LocationSearchParams] = None,
    ) -> int:
        """
        Get total count of locations matching the criteria

        Args:
            user_id: ID of the requesting user
            search: Simple search term
            search_params: Advanced search parameters

        Returns:
            Total count of matching locations
        """
        # This should use the same filtering logic as get_locations
        # but return count instead of results
        query = self.db.query(func.count(Location.id)).filter(
            Location.deleted_at.is_(None)
        )

        # Apply the same filters as in get_locations method
        # ... (implement same filtering logic)

        return query.scalar()

    # Add more methods based on your PHP business logic:
    # def add_to_favorites(self, location_id: str, user_id: str) -> bool:
    # def remove_from_favorites(self, location_id: str, user_id: str) -> bool:
    # def get_nearby_locations(self, lat: float, lng: float, radius_km: float) -> List[Location]:
    # def bulk_import_locations(self, locations_data: List[LocationCreate], user_id: str) -> Dict[str, Any]:
    # etc.
