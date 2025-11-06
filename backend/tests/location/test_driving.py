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

