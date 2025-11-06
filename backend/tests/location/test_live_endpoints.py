"""
Tests for legacy-compatible live endpoints under /location/api/live/*
"""
import pytest
from fastapi.testclient import TestClient

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestLiveEndpoints:
    def test_stream_requires_auth(self, client: TestClient):
        # with all=true to satisfy validation; still should 401 without auth
        resp = client.get("/location/api/live/stream", params={"all": "true"})
        assert resp.status_code == 401

    def test_stream_basic_flow(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed one point
        payload = {
            "id": "dev-live-1",
            "name": "adar",
            "latitude": 32.0777,
            "longitude": 34.7733,
            "timestamp": 1710001000000,
            "accuracy": 6.0,
        }
        res = client.post("/location/api/getloc", json=payload, headers=headers)
        assert res.status_code == 200

        # Stream since=0 for user=adar
        resp = client.get(
            "/location/api/live/stream",
            params={"since": 0, "user": "adar", "limit": 10},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "points" in data and isinstance(data["points"], list)
        assert data["count"] == len(data["points"]) 
        assert data["cursor"] >= 0

        # Subsequent call with same cursor should return 200 and usually 0 new points
        resp2 = client.get(
            "/location/api/live/stream",
            params={"since": data["cursor"], "user": "adar", "limit": 10},
            headers=headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "points" in data2
        assert data2["cursor"] >= data["cursor"]

    def test_latest_basic_all(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed two points (possibly same user/device)
        client.post(
            "/location/api/getloc",
            json={
                "id": "dev-live-2",
                "name": "adar",
                "latitude": 32.08,
                "longitude": 34.78,
                "timestamp": 1710001100000,
                "accuracy": 5.0,
            },
            headers=headers,
        )
        client.post(
            "/location/api/getloc",
            json={
                "id": "dev-live-3",
                "name": "ben",
                "latitude": 32.09,
                "longitude": 34.79,
                "timestamp": 1710001200000,
                "accuracy": 5.0,
            },
            headers=headers,
        )

        resp = client.get(
            "/location/api/live/latest",
            params={"all": "true"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        first = data["locations"][0]
        for k in ("device_id", "user_id", "username", "latitude", "longitude"):
            assert k in first
        assert isinstance(first.get("age_seconds"), int)
        assert isinstance(first.get("is_recent"), bool)

    def test_history_basic_user(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed two points for the same user
        client.post(
            "/location/api/getloc",
            json={
                "id": "dev-live-4",
                "name": "adar",
                "latitude": 32.10,
                "longitude": 34.80,
                "timestamp": 1710001300000,
                "accuracy": 4.0,
            },
            headers=headers,
        )
        client.post(
            "/location/api/getloc",
            json={
                "id": "dev-live-4",
                "name": "adar",
                "latitude": 32.11,
                "longitude": 34.81,
                "timestamp": 1710001400000,
                "accuracy": 3.0,
            },
            headers=headers,
        )

        resp = client.get(
            "/location/api/live/history",
            params={"user": "adar", "limit": 5},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        pt = data["points"][0]
        assert "server_timestamp" in pt

    def test_session_create_and_delete(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Create session
        resp = client.post(
            "/location/api/live/session",
            json={"device_ids": ["dev-live-5"], "duration": 120},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data and "session_token" in data
        assert data["duration"] == 120
        assert f"session_id={data['session_id']}" in data["stream_url"]  # contains session_id as query param
        assert "expires_at" in data

        # Revoke session
        sid = data["session_id"]
        resp2 = client.delete(f"/location/api/live/session/{sid}", headers=headers)
        assert resp2.status_code == 200
        assert resp2.json().get("revoked") is True

