"""
Tests for legacy-compatible driving events endpoint
"""
import os
import pytest
from fastapi.testclient import TestClient

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestDrivingIngest:
    def test_driving_requires_auth(self, client: TestClient):
        payload = {
            "id": "device-1",
            "name": "adar",
            "event": "start",
            "timestamp": 1710000000000,
            "location": {"latitude": 32.1, "longitude": 34.8, "accuracy": 10.0},
        }
        resp = client.post("/location/api/driving", json=payload)
        assert resp.status_code == 401

    @pytest.mark.parametrize("event", ["start", "data", "stop"])
    def test_driving_events_success_short_form(self, client: TestClient, monkeypatch, event: str):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-2",
            "name": "adar",
            "event": event,
            "timestamp": 1710000000000,
            "location": {"latitude": 32.071, "longitude": 34.774, "accuracy": 5.0},
            "speed": 30.5,
            "bearing": 180.0,
            "altitude": 50.0,
        }
        resp = client.post(
            "/location/api/driving",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == payload["id"]
        assert data["name"] == payload["name"]
        assert data["event_type"] == event
        assert data["status"] == "success"
        assert isinstance(data["request_id"], str)
        assert isinstance(data["record_id"], int)
        assert data["storage_mode"] == "database"

    @pytest.mark.parametrize(
        "event_type,expected",
        [("driving_start", "start"), ("driving_data", "data"), ("driving_stop", "stop")],
    )
    def test_driving_events_success_long_form(self, client: TestClient, monkeypatch, event_type: str, expected: str):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-3",
            "name": "adar",
            "event_type": event_type,
            "timestamp": 1710000000000,
            "location": {"latitude": 32.2, "longitude": 34.9},
        }
        resp = client.post(
            "/location/api/driving",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["event_type"] == expected

    @pytest.mark.parametrize(
        "bad_payload",
        [
            {  # invalid event
                "id": "device-4",
                "name": "adar",
                "event": "foo",
                "timestamp": 1710000000000,
                "location": {"latitude": 32.0, "longitude": 34.0},
            },
            {  # missing location
                "id": "device-4",
                "name": "adar",
                "event": "start",
                "timestamp": 1710000000000,
            },
            {  # invalid lat
                "id": "device-4",
                "name": "adar",
                "event": "start",
                "timestamp": 1710000000000,
                "location": {"latitude": 91, "longitude": 34.0},
            },
            {  # invalid lon
                "id": "device-4",
                "name": "adar",
                "event": "start",
                "timestamp": 1710000000000,
                "location": {"latitude": 32.0, "longitude": 181},
            },
            {  # negative speed
                "id": "device-4",
                "name": "adar",
                "event": "data",
                "timestamp": 1710000000000,
                "location": {"latitude": 32.0, "longitude": 34.0},
                "speed": -1,
            },
            {  # bearing out of range
                "id": "device-4",
                "name": "adar",
                "event": "data",
                "timestamp": 1710000000000,
                "location": {"latitude": 32.0, "longitude": 34.0},
                "bearing": 361,
            },
            {  # location accuracy negative
                "id": "device-4",
                "name": "adar",
                "event": "data",
                "timestamp": 1710000000000,
                "location": {"latitude": 32.0, "longitude": 34.0, "accuracy": -1},
            },
        ],
    )
    def test_driving_validation_errors(self, client: TestClient, monkeypatch, bad_payload):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        resp = client.post(
            "/location/api/driving",
            json=bad_payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 422


class TestDrivingTripSummary:
    SUMMARY = {
        "duration_seconds": 1834.0,
        "distance_meters": 21450.5,
        "avg_speed": 42.1,
        "max_speed": 97.3,
    }

    def _stored(self, record_id: int):
        from tests.conftest import LocationTestingSessionLocal
        from app.models.location_records import DrivingRecord

        db = LocationTestingSessionLocal()
        try:
            return db.get(DrivingRecord, record_id)
        finally:
            db.close()

    def test_stop_with_trip_summary_is_stored(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-ts-1",
            "name": "adar",
            "event": "stop",
            "timestamp": 1710000000000,
            "location": {"latitude": 32.071, "longitude": 34.774},
            "trip_id": "trip-ts-1",
            "trip_summary": self.SUMMARY,
        }
        resp = client.post(
            "/location/api/driving", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 200
        rec = self._stored(resp.json()["record_id"])
        assert rec.event_type == "driving_stop"
        assert rec.trip_id == "trip-ts-1"
        assert rec.trip_duration_seconds == pytest.approx(1834.0)
        assert rec.trip_distance_meters == pytest.approx(21450.5)
        assert rec.trip_avg_speed == pytest.approx(42.1)
        assert rec.trip_max_speed == pytest.approx(97.3)

    def test_partial_trip_summary_is_stored(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-ts-2",
            "name": "adar",
            "event_type": "driving_stop",
            "timestamp": 1710000000000,
            "location": {"latitude": 32.071, "longitude": 34.774},
            "trip_summary": {"distance_meters": 500.0},
        }
        resp = client.post(
            "/location/api/driving", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 200
        rec = self._stored(resp.json()["record_id"])
        assert rec.trip_distance_meters == pytest.approx(500.0)
        assert rec.trip_duration_seconds is None
        assert rec.trip_avg_speed is None
        assert rec.trip_max_speed is None

    def test_event_without_trip_summary_stores_nulls(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-ts-3",
            "name": "adar",
            "event": "data",
            "timestamp": 1710000000000,
            "location": {"latitude": 32.071, "longitude": 34.774},
        }
        resp = client.post(
            "/location/api/driving", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 200
        rec = self._stored(resp.json()["record_id"])
        assert rec.trip_duration_seconds is None
        assert rec.trip_distance_meters is None
        assert rec.trip_avg_speed is None
        assert rec.trip_max_speed is None

    def test_negative_trip_summary_value_rejected(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-ts-4",
            "name": "adar",
            "event": "stop",
            "timestamp": 1710000000000,
            "location": {"latitude": 32.071, "longitude": 34.774},
            "trip_summary": {"distance_meters": -1},
        }
        resp = client.post(
            "/location/api/driving", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 422

