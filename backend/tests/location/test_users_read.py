"""
Tests for legacy-compatible GET /location/api/users endpoint
"""
import pytest
from fastapi.testclient import TestClient
from typing import Optional

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestUsersRead:
    def test_users_requires_auth(self, client: TestClient):
        resp = client.get("/location/api/users")
        assert resp.status_code == 401

    def test_users_with_location_data_default(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed one user with a location record
        payload = {
            "id": "device-u1",
            "name": "adar",
            "latitude": 32.07,
            "longitude": 34.77,
            "timestamp": 1710000200000,
            "accuracy": 5.0,
        }
        r = client.post("/location/api/getloc", json=payload, headers=headers)
        assert r.status_code == 200

        # Seed another user with only driving (no location)
        drv_payload = {
            "id": "device-u2",
            "name": "ben",
            "event": "start",
            "timestamp": 1710000300000,
            "location": {"latitude": 32.08, "longitude": 34.78, "accuracy": 5.0},
        }
        r2 = client.post("/location/api/driving", json=drv_payload, headers=headers)
        assert r2.status_code == 200

        # Default with_location_data=True: only users with location records should appear
        resp = client.get("/location/api/users", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(["users", "count", "source"]).issubset(data.keys())
        names = [u["username"] for u in data["users"]]
        assert "adar" in names
        assert "ben" not in names

    def test_users_include_counts_and_metadata(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed one location for 'adar'
        payload = {
            "id": "device-u3",
            "name": "adar",
            "latitude": 32.10,
            "longitude": 34.80,
            "timestamp": 1710000400000,
            "accuracy": 4.0,
        }
        r = client.post("/location/api/getloc", json=payload, headers=headers)
        assert r.status_code == 200

        # Query with counts and metadata
        resp = client.get(
            "/location/api/users",
            params={"include_counts": "true", "include_metadata": "true"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        user = next(u for u in data["users"] if u["username"] == "adar")
        assert "location_count" in user and isinstance(user["location_count"], int)
        assert "driving_count" in user and isinstance(user["driving_count"], int)
        assert user["location_count"] >= 1
        # No driving seeded for 'adar' in this test
        assert user["driving_count"] == 0
        assert "last_location_time" in user
        assert user["last_location_time"] is not None
        assert "last_driving_time" in user
        assert user["last_driving_time"] is None

    def test_users_with_location_data_false_returns_all(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed: 'adar' with location; 'ben' with driving only
        client.post(
            "/location/api/getloc",
            json={
                "id": "device-u4",
                "name": "adar",
                "latitude": 32.11,
                "longitude": 34.81,
                "timestamp": 1710000500000,
                "accuracy": 3.0,
            },
            headers=headers,
        )
        client.post(
            "/location/api/driving",
            json={
                "id": "device-u5",
                "name": "ben",
                "event": "data",
                "timestamp": 1710000600000,
                "location": {"latitude": 32.12, "longitude": 34.82, "accuracy": 6.0},
            },
            headers=headers,
        )

        resp = client.get(
            "/location/api/users",
            params={"with_location_data": "false"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        names = [u["username"] for u in data["users"]]
        assert "adar" in names and "ben" in names

