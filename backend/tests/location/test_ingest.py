"""
Tests for legacy-compatible location ingestion endpoints
"""
import os
import pytest
from fastapi.testclient import TestClient


LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestLocationIngest:
    def test_ping(self, client: TestClient):
        resp = client.get("/location/ping")
        assert resp.status_code == 200
        assert resp.json()["message"] == "pong"

    def test_getloc_requires_auth(self, client: TestClient):
        payload = {
            "id": "device-1",
            "name": "adar",
            "latitude": 32.1,
            "longitude": 34.8,
        }
        resp = client.post("/location/api/getloc", json=payload)
        assert resp.status_code == 401

    def test_getloc_with_api_token_success(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-1",
            "name": "adar",
            "latitude": 32.071,
            "longitude": 34.774,
            "accuracy": 12.3,
            "speed": 0.0,
            "bearing": 0.0,
            "battery_level": 80,
            "network_type": "wifi",
            "provider": "gps",
            "timestamp": 1710000000000,
        }
        resp = client.post(
            "/location/api/getloc",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == payload["id"]
        assert data["name"] == payload["name"]
        assert data["storage_mode"] == "database"
        assert isinstance(data["request_id"], str)
        assert isinstance(data["record_id"], int)

    @pytest.mark.parametrize(
        "bad_field,bad_value",
        [
            ("latitude", 91),
            ("latitude", -91),
            ("longitude", 181),
            ("longitude", -181),
            ("accuracy", -1),
            ("speed", -0.1),
            ("bearing", 361),
            ("battery_level", -1),
            ("battery_level", 101),
        ],
    )
    def test_getloc_validation_errors(self, client: TestClient, monkeypatch, bad_field, bad_value):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "id": "device-2",
            "name": "adar",
            "latitude": 32.0,
            "longitude": 34.0,
        }
        payload[bad_field] = bad_value
        resp = client.post(
            "/location/api/getloc",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 422

