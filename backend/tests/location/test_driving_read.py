"""
Tests for legacy-compatible GET /location/api/driving-records endpoint
"""
import pytest
from fastapi.testclient import TestClient
from typing import Optional

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestDrivingRecordsRead:
    def test_driving_records_requires_auth(self, client: TestClient):
        resp = client.get("/location/api/driving-records")
        assert resp.status_code == 401

    def _seed_driving_events(self, client: TestClient, headers: dict, user: str = "adar", device: str = "dev-dr-1", trip_id: Optional[str] = None):
        # Seed a start, data, stop sequence
        events = [
            ("start", 1710000100000, 32.071, 34.774),
            ("data", 1710000105000, 32.072, 34.775),
            ("stop", 1710000110000, 32.073, 34.776),
        ]
        rec_ids = []
        for ev, ts, lat, lng in events:
            payload = {
                "id": device,
                "name": user,
                "event": ev,
                "timestamp": ts,
                "location": {"latitude": lat, "longitude": lng, "accuracy": 5.0},
            }
            if trip_id:
                payload["trip_id"] = trip_id
            r = client.post("/location/api/driving", json=payload, headers=headers)
            assert r.status_code == 200
            rec_ids.append(r.json().get("record_id"))
        return rec_ids

    def test_driving_records_basic_query(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed two trips for user 'adar'
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-a", trip_id="trip-A")
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-b", trip_id="trip-B")

        resp = client.get("/location/api/driving-records", params={"user": "adar"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(["driving_records", "count", "total", "limit", "offset", "source"]).issubset(data.keys())
        assert data["source"] == "database"
        assert data["count"] >= 6 and data["total"] >= 6
        # Check fields
        first = data["driving_records"][0]
        assert first["username"] == "adar"
        assert first["event_type"] in ("start", "data", "stop")

    def test_driving_records_filter_event_type(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-c", trip_id="trip-C")

        resp = client.get(
            "/location/api/driving-records",
            params={"user": "adar", "event_type": "start"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        for item in data["driving_records"]:
            assert item["event_type"] == "start"

    def test_driving_records_pagination(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-d", trip_id="trip-D")

        # Page 1
        r1 = client.get(
            "/location/api/driving-records",
            params={"user": "adar", "limit": 2, "offset": 0},
            headers=headers,
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["count"] == 2

        # Page 2
        r2 = client.get(
            "/location/api/driving-records",
            params={"user": "adar", "limit": 2, "offset": 2},
            headers=headers,
        )
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["count"] >= 1
        assert d2["total"] == d1["total"]

    def test_driving_records_filter_trip_id(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed two trips
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-e", trip_id="trip-E")
        self._seed_driving_events(client, headers, user="adar", device="dev-dr-f", trip_id="trip-F")

        # Filter trip-E
        r = client.get(
            "/location/api/driving-records",
            params={"user": "adar", "trip_id": "trip-E"},
            headers=headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 3
        for item in data["driving_records"]:
            assert item["trip_id"] == "trip-E"

