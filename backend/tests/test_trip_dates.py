"""
Test trip date management functionality
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.user import User


@pytest.mark.trips
class TestTripDateUpdate:
    """Test trip date update functionality"""

    def test_set_start_date_for_trip_without_date(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test setting start date for a trip that doesn't have one"""
        # Ensure trip has no start date
        assert test_trip.start_date is None
        
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["start_date"] == new_date.isoformat()
        assert data["id"] == test_trip.id
        assert data["title"] == test_trip.title

    def test_update_existing_start_date(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session: Session):
        """Test updating an existing start date"""
        # Set initial date
        initial_date = date.today() + timedelta(days=5)
        test_trip.start_date = initial_date
        db_session.commit()
        
        # Update to new date
        new_date = date.today() + timedelta(days=10)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["start_date"] == new_date.isoformat()
        assert data["start_date"] != initial_date.isoformat()

    def test_clear_start_date(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session: Session):
        """Test clearing/removing a start date"""
        # Set initial date
        initial_date = date.today() + timedelta(days=5)
        test_trip.start_date = initial_date
        db_session.commit()
        
        # Clear the date
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": None},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["start_date"] is None

    def test_set_past_date_allowed(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test that past dates are allowed (for flexibility)"""
        past_date = date.today() - timedelta(days=5)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": past_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["start_date"] == past_date.isoformat()

    def test_invalid_date_format_rejected(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test that invalid date formats are rejected"""
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": "invalid-date"},
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_update_date_requires_authentication(self, client: TestClient, test_trip: Trip):
        """Test that updating trip date requires authentication"""
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_date.isoformat()}
            # No auth headers
        )
        
        assert response.status_code == 401

    def test_update_date_requires_ownership(self, client: TestClient, test_trip: Trip, db_session: Session):
        """Test that only trip owner can update dates"""
        # Create another user
        other_user = User(email="other@example.com", display_name="Other User")
        db_session.add(other_user)
        db_session.commit()
        
        # Create auth headers for other user
        other_headers = {"Authorization": f"Bearer test-token-{other_user.id}"}
        
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_date.isoformat()},
            headers=other_headers
        )
        
        assert response.status_code == 403

    def test_update_nonexistent_trip_returns_404(self, client: TestClient, auth_headers: dict):
        """Test updating date for non-existent trip returns 404"""
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            "/trips/nonexistent-trip-id",
            json={"start_date": new_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_update_multiple_fields_including_date(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test updating multiple trip fields including start date"""
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={
                "title": "Updated Trip Title",
                "start_date": new_date.isoformat(),
                "destination": "Updated Destination"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "Updated Trip Title"
        assert data["start_date"] == new_date.isoformat()
        assert data["destination"] == "Updated Destination"

    def test_date_only_update_preserves_other_fields(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test that updating only date preserves other trip fields"""
        original_title = test_trip.title
        original_destination = test_trip.destination
        new_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["start_date"] == new_date.isoformat()
        assert data["title"] == original_title
        assert data["destination"] == original_destination


@pytest.mark.trips
class TestTripDateValidation:
    """Test trip date validation"""

    def test_date_format_validation(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test various date format validations"""
        invalid_dates = [
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid day
            "24-01-01",    # Wrong year format
            "2024/01/01",  # Wrong separator
            "January 1, 2024",  # Text format
            "",            # Empty string
            "null",        # String null
        ]
        
        for invalid_date in invalid_dates:
            response = client.patch(
                f"/trips/{test_trip.id}",
                json={"start_date": invalid_date},
                headers=auth_headers
            )
            
            assert response.status_code == 422, f"Date '{invalid_date}' should be invalid"

    def test_valid_date_formats(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test valid date formats"""
        valid_dates = [
            "2024-01-01",
            "2024-12-31",
            "2025-02-28",
            "2024-02-29",  # Leap year
        ]
        
        for valid_date in valid_dates:
            response = client.patch(
                f"/trips/{test_trip.id}",
                json={"start_date": valid_date},
                headers=auth_headers
            )
            
            assert response.status_code == 200, f"Date '{valid_date}' should be valid"
            data = response.json()
            assert data["start_date"] == valid_date


@pytest.mark.trips
@pytest.mark.integration
class TestTripDateIntegration:
    """Test trip date integration with other features"""

    def test_trip_date_affects_day_calculations(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session: Session):
        """Test that changing trip date affects day date calculations"""
        # Set trip start date
        start_date = date.today() + timedelta(days=7)
        
        response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": start_date.isoformat()},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Create a day
        day_response = client.post(
            f"/trips/{test_trip.id}/days",
            json={"seq": 1, "status": "active"},
            headers=auth_headers
        )
        
        assert day_response.status_code == 200
        day_data = day_response.json()
        
        # Check that calculated_date matches trip start date
        assert day_data["calculated_date"] == start_date.isoformat()
        
        # Update trip start date
        new_start_date = start_date + timedelta(days=3)
        
        update_response = client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": new_start_date.isoformat()},
            headers=auth_headers
        )
        
        assert update_response.status_code == 200
        
        # Get day again to check updated calculated_date
        day_get_response = client.get(
            f"/trips/{test_trip.id}/days/{day_data['id']}",
            headers=auth_headers
        )
        
        assert day_get_response.status_code == 200
        updated_day_data = day_get_response.json()
        
        # Calculated date should be updated
        assert updated_day_data["calculated_date"] == new_start_date.isoformat()

    def test_clearing_trip_date_affects_day_calculations(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session: Session):
        """Test that clearing trip date affects day calculations"""
        # Set trip start date and create day
        start_date = date.today() + timedelta(days=7)
        
        client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": start_date.isoformat()},
            headers=auth_headers
        )
        
        day_response = client.post(
            f"/trips/{test_trip.id}/days",
            json={"seq": 1, "status": "active"},
            headers=auth_headers
        )
        
        day_data = day_response.json()
        
        # Clear trip start date
        client.patch(
            f"/trips/{test_trip.id}",
            json={"start_date": None},
            headers=auth_headers
        )
        
        # Get day to check calculated_date is None
        day_get_response = client.get(
            f"/trips/{test_trip.id}/days/{day_data['id']}",
            headers=auth_headers
        )
        
        updated_day_data = day_get_response.json()
        assert updated_day_data["calculated_date"] is None
