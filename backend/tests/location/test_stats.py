"""
Tests for legacy-compatible stats endpoint /location/api/stats (GET/POST)
"""
from fastapi.testclient import TestClient
import pytest

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestStatsEndpoint:
    def test_stats_requires_auth(self, client: TestClient):
        # Provide a device_id to satisfy validation but expect 401
        resp = client.get("/location/api/stats", params={"device_id": "dev-stats-auth"})
        assert resp.status_code == 401

    def test_stats_basic_counts_last_24h(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        device_id = "dev-stats-1"
        user_name = "adar"

        # Seed realtime location points (3)
        for i in range(3):
            payload = {
                "id": device_id,
                "name": user_name,
                "latitude": 32.070 + i * 0.001,
                "longitude": 34.770 + i * 0.001,
                "timestamp": 1710001000000 + i * 1000,
                "accuracy": 5.0,
            }
            res = client.post("/location/api/getloc", json=payload, headers=headers)
            assert res.status_code == 200

        # Seed batch location points (2) via batch-sync
        batch_payload = {
            "sync_id": "sync-1",
            "user_name": user_name,
            "device_id": device_id,
            "part": 1,
            "total_parts": 1,
            "records": [
                {
                    "type": "location",
                    "timestamp": 1710002000000,
                    "latitude": 32.080,
                    "longitude": 34.780,
                    "accuracy": 4.0,
                },
                {
                    "type": "location",
                    "timestamp": 1710002100000,
                    "latitude": 32.081,
                    "longitude": 34.781,
                    "accuracy": 4.0,
                },
            ],
        }
        res = client.post("/location/api/batch-sync", json=batch_payload, headers=headers)
        assert res.status_code == 200

        # Seed driving events for two trips (distinct trip_id)
        for trip_id in ["trip-1", "trip-2"]:
            drv_payload = {
                "id": device_id,
                "name": user_name,
                "event": "start",
                "timestamp": 1710002200000,
                "location": {"latitude": 32.09, "longitude": 34.79, "accuracy": 5.0},
                "trip_id": trip_id,
            }
            res = client.post("/location/api/driving", json=drv_payload, headers=headers)
            assert res.status_code == 200

        # Query stats using device_id and timeframe=last_24h
        resp = client.get(
            "/location/api/stats",
            params={"device_id": device_id, "timeframe": "last_24h"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["device_id"] == device_id
        assert data["timeframe"] == "last_24h"
        assert "range" in data and "from" in data["range"] and "to" in data["range"]

        counts = data["counts"]
        assert counts["location_updates"] == 5
        assert counts["updates_realtime"] == 3
        assert counts["updates_batched"] == 2
        assert counts["driving_sessions"] == 2

        meta = data["meta"]
        assert "first_seen_at" in meta
        assert "last_update_at" in meta
        assert meta.get("version") == "1.0"
        assert meta.get("cached") is False

        # Second call should hit cache and set cached=true
        resp2 = client.get(
            "/location/api/stats",
            params={"device_id": device_id, "timeframe": "last_24h"},
            headers=headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["counts"]["location_updates"] == 5
        assert data2["meta"]["cached"] is True

    def test_stats_post_body(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        device_id = "dev-stats-2"
        user_name = "ben"

        # Seed one realtime location point
        payload = {
            "id": device_id,
            "name": user_name,
            "latitude": 32.100,
            "longitude": 34.800,
            "timestamp": 1710003000000,
            "accuracy": 5.0,
        }
        res = client.post("/location/api/getloc", json=payload, headers=headers)
        assert res.status_code == 200

        # POST to stats with JSON body
        resp = client.post(
            "/location/api/stats",
            json={"device_id": device_id, "timeframe": "today"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["device_id"] == device_id
        assert data["counts"]["location_updates"] >= 1



    def test_stats_segments_last_24h_hourly(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        device_id = "dev-stats-seg-24h"
        user_name = "seguser"

        # Seed realtime and batch points
        for i in range(3):
            payload = {
                "id": device_id,
                "name": user_name,
                "latitude": 31.0 + i * 0.001,
                "longitude": 34.0 + i * 0.001,
                "timestamp": 1711001000000 + i * 1000,
                "accuracy": 5.0,
            }
            assert client.post("/location/api/getloc", json=payload, headers=headers).status_code == 200

        batch_payload = {
            "sync_id": "sync-seg-1",
            "user_name": user_name,
            "device_id": device_id,
            "part": 1,
            "total_parts": 1,
            "records": [
                {"type": "location", "timestamp": 1711002000000, "latitude": 31.1, "longitude": 34.1, "accuracy": 4.0},
                {"type": "location", "timestamp": 1711002100000, "latitude": 31.11, "longitude": 34.11, "accuracy": 4.0},
            ],
        }
        assert client.post("/location/api/batch-sync", json=batch_payload, headers=headers).status_code == 200

        # Two driving sessions
        for trip_id in ["trip-a", "trip-b"]:
            drv_payload = {
                "id": device_id,
                "name": user_name,
                "event": "start",
                "timestamp": 1711002200000,
                "location": {"latitude": 31.2, "longitude": 34.2, "accuracy": 5.0},
                "trip_id": trip_id,
            }
            assert client.post("/location/api/driving", json=drv_payload, headers=headers).status_code == 200

        # Request segments
        resp = client.get(
            "/location/api/stats",
            params={"device_id": device_id, "timeframe": "last_24h", "segments": True},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["counts"]["location_updates"] == 5
        assert data["counts"]["updates_realtime"] == 3
        assert data["counts"]["updates_batched"] == 2
        assert data["counts"]["driving_sessions"] == 2
        assert data.get("segments") is not None
        assert data["segments"]["granularity"] == "hour"
        buckets = data["segments"]["buckets"]
        assert len(buckets) == 24
        # Sum across buckets should equal totals
        su = sum(b["counts"]["location_updates"] for b in buckets)
        sr = sum(b["counts"]["updates_realtime"] for b in buckets)
        sb = sum(b["counts"]["updates_batched"] for b in buckets)
        sd = sum(b["counts"]["driving_sessions"] for b in buckets)
        assert su == 5 and sr == 3 and sb == 2 and sd == 2

    def test_stats_segments_last_7d_daily(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        device_id = "dev-stats-seg-7d"
        user_name = "seguser7"

        # Seed one realtime and one batch
        assert client.post(
            "/location/api/getloc",
            json={
                "id": device_id,
                "name": user_name,
                "latitude": 30.0,
                "longitude": 35.0,
                "timestamp": 1712001000000,
                "accuracy": 5.0,
            },
            headers=headers,
        ).status_code == 200
        assert client.post(
            "/location/api/batch-sync",
            json={
                "sync_id": "sync-seg-7",
                "user_name": user_name,
                "device_id": device_id,
                "part": 1,
                "total_parts": 1,
                "records": [
                    {"type": "location", "timestamp": 1712002000000, "latitude": 30.1, "longitude": 35.1, "accuracy": 4.0}
                ],
            },
            headers=headers,
        ).status_code == 200

        # Query last_7d with segments
        resp = client.get(
            "/location/api/stats",
            params={"device_id": device_id, "timeframe": "last_7d", "segments": True},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("segments") is not None
        assert data["segments"]["granularity"] == "day"
        buckets = data["segments"]["buckets"]
        assert len(buckets) == 7
        su = sum(b["counts"]["location_updates"] for b in buckets)
        assert su >= 2  # at least the two seeded records
