"""
Tests for Days API endpoints
"""
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient

from app.models.day import Day, DayStatus
from app.models.trip import Trip


class TestDaysCreate:
    """Test day creation endpoints"""

    def test_create_day_with_all_fields(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test creating a day with all fields specified"""
        day_data = {
            "seq": 1,
            "status": "active",
            "rest_day": False,
            "notes": {"description": "First day of the trip"}
        }

        response = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["seq"] == 1
        assert data["status"] == "active"
        assert data["rest_day"] is False
        assert data["notes"]["description"] == "First day of the trip"
        assert data["trip_id"] == test_trip.id
        assert "id" in data
        assert "created_at" in data

    def test_create_day_minimal_fields(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test creating a day with minimal fields (auto-generated seq)"""
        day_data = {}
        
        response = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["seq"] == 1  # Auto-generated as first day
        assert data["status"] == "active"  # Default
        assert data["rest_day"] is False  # Default
        assert data["notes"] is None
        assert data["trip_id"] == test_trip.id

    def test_create_multiple_days_auto_sequence(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test creating multiple days with auto-generated sequence numbers"""
        # Create first day
        response1 = client.post(
            f"/trips/{test_trip.id}/days",
            json={},
            headers=auth_headers
        )
        assert response1.status_code == 200
        assert response1.json()["seq"] == 1
        
        # Create second day
        response2 = client.post(
            f"/trips/{test_trip.id}/days",
            json={},
            headers=auth_headers
        )
        assert response2.status_code == 200
        assert response2.json()["seq"] == 2
        
        # Create third day
        response3 = client.post(
            f"/trips/{test_trip.id}/days",
            json={},
            headers=auth_headers
        )
        assert response3.status_code == 200
        assert response3.json()["seq"] == 3

    def test_create_day_duplicate_sequence(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test creating a day with duplicate sequence number should fail"""
        # Create first day
        day_data = {"seq": 1}
        response1 = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Try to create another day with same sequence
        response2 = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    def test_create_day_without_authentication(self, client: TestClient, test_trip: Trip):
        """Test creating a day without authentication should fail"""
        day_data = {"seq": 1}
        
        response = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data
        )
        
        assert response.status_code == 401

    def test_create_day_for_nonexistent_trip(self, client: TestClient, auth_headers: dict):
        """Test creating a day for non-existent trip should fail"""
        day_data = {"seq": 1}
        
        response = client.post(
            "/trips/nonexistent-trip-id/days",
            json=day_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Trip not found" in response.json()["detail"]

    def test_create_day_with_invalid_sequence(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test creating a day with invalid sequence number should fail"""
        day_data = {"seq": 0}  # Invalid: must be > 0
        
        response = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_create_day_with_rest_day_flag(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test creating a rest day"""
        day_data = {
            "seq": 1,
            "rest_day": True,
            "notes": {"type": "rest", "reason": "Sightseeing day"}
        }
        
        response = client.post(
            f"/trips/{test_trip.id}/days",
            json=day_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["rest_day"] is True
        assert data["notes"]["type"] == "rest"


class TestDaysList:
    """Test day listing endpoints"""

    def test_list_days_empty(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test listing days when trip has no days"""
        response = client.get(
            f"/trips/{test_trip.id}/days",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["days"] == []
        assert data["total"] == 0
        assert data["trip_id"] == test_trip.id

    def test_list_days_with_data(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test listing days when trip has days"""
        # Create test days
        day1 = Day(trip_id=test_trip.id, seq=1)
        day2 = Day(trip_id=test_trip.id, seq=2, rest_day=True)
        day3 = Day(trip_id=test_trip.id, seq=3)

        db_session.add_all([day1, day2, day3])
        db_session.commit()

        response = client.get(
            f"/trips/{test_trip.id}/days",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["days"]) == 3
        assert data["total"] == 3
        assert data["trip_id"] == test_trip.id

        # Check ordering by sequence
        assert data["days"][0]["seq"] == 1
        assert data["days"][1]["seq"] == 2
        assert data["days"][2]["seq"] == 3

        # Check specific day data
        assert data["days"][1]["rest_day"] is True

    def test_list_days_without_authentication(self, client: TestClient, test_trip: Trip):
        """Test listing days without authentication should fail"""
        response = client.get(f"/trips/{test_trip.id}/days")
        
        assert response.status_code == 401

    def test_list_days_for_nonexistent_trip(self, client: TestClient, auth_headers: dict):
        """Test listing days for non-existent trip should fail"""
        response = client.get(
            "/trips/nonexistent-trip-id/days",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestDaysGet:
    """Test individual day retrieval endpoints"""

    def test_get_day_by_id(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test getting a specific day by ID"""
        # Create test day
        day = Day(
            trip_id=test_trip.id,
            seq=1,
            rest_day=False,
            notes={"description": "Test day"}
        )
        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        response = client.get(
            f"/trips/{test_trip.id}/days/{day.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == day.id
        assert data["seq"] == 1
        assert data["rest_day"] is False
        assert data["notes"]["description"] == "Test day"

    def test_get_nonexistent_day(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test getting a non-existent day should fail"""
        response = client.get(
            f"/trips/{test_trip.id}/days/nonexistent-day-id",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Day not found" in response.json()["detail"]

    def test_get_day_without_authentication(self, client: TestClient, test_trip: Trip, db_session):
        """Test getting a day without authentication should fail"""
        # Create test day
        day = Day(trip_id=test_trip.id, seq=1)
        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)
        
        response = client.get(f"/trips/{test_trip.id}/days/{day.id}")

        assert response.status_code == 401


class TestDaysUpdate:
    """Test day update endpoints"""

    def test_update_day_all_fields(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test updating all fields of a day"""
        # Create test day
        day = Day(trip_id=test_trip.id, seq=1)
        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        update_data = {
            "seq": 2,
            "status": "inactive",
            "rest_day": True,
            "notes": {"updated": True, "reason": "Changed plans"}
        }

        response = client.patch(
            f"/trips/{test_trip.id}/days/{day.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["seq"] == 2
        assert data["status"] == "inactive"
        assert data["rest_day"] is True
        assert data["notes"]["updated"] is True

    def test_update_day_partial_fields(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test updating only some fields of a day"""
        # Create test day
        day = Day(trip_id=test_trip.id, seq=1, rest_day=False)
        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        update_data = {"rest_day": True}

        response = client.patch(
            f"/trips/{test_trip.id}/days/{day.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Updated field
        assert data["rest_day"] is True

        # Unchanged fields
        assert data["seq"] == 1

    def test_update_day_sequence_conflict(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test updating day sequence to existing sequence should fail"""
        # Create two test days
        day1 = Day(trip_id=test_trip.id, seq=1)
        day2 = Day(trip_id=test_trip.id, seq=2)
        db_session.add_all([day1, day2])
        db_session.commit()
        db_session.refresh(day2)

        # Try to update day2 to have same sequence as day1
        update_data = {"seq": 1}

        response = client.patch(
            f"/trips/{test_trip.id}/days/{day2.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_nonexistent_day(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test updating a non-existent day should fail"""
        update_data = {"rest_day": True}

        response = client.patch(
            f"/trips/{test_trip.id}/days/nonexistent-day-id",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404


class TestDaysDelete:
    """Test day deletion endpoints"""

    def test_delete_day(self, client: TestClient, auth_headers: dict, test_trip: Trip, db_session):
        """Test deleting a day"""
        # Create test day
        day = Day(trip_id=test_trip.id, seq=1)
        db_session.add(day)
        db_session.commit()
        db_session.refresh(day)

        response = client.delete(
            f"/trips/{test_trip.id}/days/{day.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

        # Verify day is soft deleted
        db_session.refresh(day)
        assert day.deleted_at is not None

    def test_delete_nonexistent_day(self, client: TestClient, auth_headers: dict, test_trip: Trip):
        """Test deleting a non-existent day should fail"""
        response = client.delete(
            f"/trips/{test_trip.id}/days/nonexistent-day-id",
            headers=auth_headers
        )

        assert response.status_code == 404


# TODO: Add reorder tests when reorder functionality is implemented
# class TestDaysReorder:
#     """Test day reordering endpoints - to be implemented in future enhancement"""
#     pass
