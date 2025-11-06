"""
Tests for legacy-compatible GET /location/api/locations endpoint
"""
import pytest
from fastapi.testclient import TestClient

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestLocationsRead:
    def test_locations_requires_auth(self, client: TestClient):
        resp = client.get("/location/api/locations")
        assert resp.status_code == 401

    def test_locations_query_basic(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed a couple of points for user 'adar'
        payload1 = {
            "id": "device-1",
            "name": "adar",
            "latitude": 32.071,
            "longitude": 34.774,
            "timestamp": 1710000000000,
        }
        payload2 = {
            "id": "device-1",
            "name": "adar",
            "latitude": 32.072,
            "longitude": 34.775,
            "timestamp": 1710000001000,
        }
        r1 = client.post("/location/api/getloc", json=payload1, headers=headers)
        r2 = client.post("/location/api/getloc", json=payload2, headers=headers)
        assert r1.status_code == 200 and r2.status_code == 200

        # Query by user
        resp = client.get("/location/api/locations", params={"user": "adar"}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert set(["locations", "count", "total", "limit", "offset", "source"]).issubset(data.keys())
        assert data["source"] == "database"
        assert data["count"] >= 2 and data["total"] >= 2
        assert len(data["locations"]) == data["count"]
        # Each item should include username and coordinates
        first = data["locations"][0]
        assert "username" in first and first["username"] == "adar"
        assert "latitude" in first and "longitude" in first

    def test_locations_pagination(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Seed three points
        for i in range(3):
            payload = {
                "id": "device-2",
                "name": "adar",
                "latitude": 32.070 + i * 0.001,
                "longitude": 34.770 + i * 0.001,
                "timestamp": 1710000000000 + i * 1000,
            }
            r = client.post("/location/api/getloc", json=payload, headers=headers)
            assert r.status_code == 200

        # Page 1
        resp1 = client.get(
            "/location/api/locations",
            params={"user": "adar", "limit": 2, "offset": 0},
            headers=headers,
        )
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["count"] == 2
        assert d1["total"] >= 3

        # Page 2
        resp2 = client.get(
            "/location/api/locations",
            params={"user": "adar", "limit": 2, "offset": 2},
            headers=headers,
        )
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["count"] >= 1
        assert d2["total"] == d1["total"]

    def test_locations_geo_radius(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        headers = {"X-API-Token": LOC_TOKEN}

        # Close point near center
        near_payload = {
            "id": "device-3",
            "name": "adar",
            "latitude": 32.071,
            "longitude": 34.774,
            "timestamp": 1710000010000,
        }
        # Far point (~>10km)
        far_payload = {
            "id": "device-3",
            "name": "adar",
            "latitude": 32.200,
            "longitude": 34.900,
            "timestamp": 1710000020000,
        }
        r1 = client.post("/location/api/getloc", json=near_payload, headers=headers)
        r2 = client.post("/location/api/getloc", json=far_payload, headers=headers)
        assert r1.status_code == 200 and r2.status_code == 200

        base_params = {"user": "adar", "lat": 32.071, "lng": 34.774}

        # Small radius: only near point
        resp_small = client.get(
            "/location/api/locations",
            params={**base_params, "radius": 500},
            headers=headers,
        )
        assert resp_small.status_code == 200
        d_small = resp_small.json()
        assert d_small["count"] >= 1
        # Ensure all returned are within ~500m of center
        for item in d_small["locations"]:
            assert abs(item["latitude"] - 32.071) <= 0.02  # loose check

        # Larger radius: near still included; far likely still excluded at 3km
        resp_mid = client.get(
            "/location/api/locations",
            params={**base_params, "radius": 3000},
            headers=headers,
        )
        assert resp_mid.status_code == 200
        d_mid = resp_mid.json()
        assert d_mid["count"] >= 1

        # Very large radius: both points should be included
        resp_large = client.get(
            "/location/api/locations",
            params={**base_params, "radius": 20000},
            headers=headers,
        )
        assert resp_large.status_code == 200
        d_large = resp_large.json()
        # At least two points within 20km
        assert d_large["count"] >= 2

