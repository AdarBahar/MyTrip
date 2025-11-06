"""
Tests for legacy-compatible batch sync endpoint
"""
import pytest
from fastapi.testclient import TestClient

LOC_TOKEN = "4Q9j0INedMHobgNdJx+PqcXesQjifyl9LCE+W2phLdI="


class TestBatchSync:
    def test_batch_sync_requires_auth(self, client: TestClient):
        payload = {
            "sync_id": "device-1_1710000000000",
            "device_id": "device-1",
            "user_name": "adar",
            "part_number": 1,
            "total_parts": 1,
            "records": [
                {
                    "type": "location",
                    "timestamp": 1710000000000,
                    "latitude": 32.071,
                    "longitude": 34.774,
                }
            ],
        }
        resp = client.post("/location/api/batch-sync", json=payload)
        assert resp.status_code == 401

    def test_batch_sync_success_mixed_records(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "sync_id": "device-2_1710000000000",
            "device_id": "device-2",
            "user_name": "adar",
            "part_number": 1,  # test normalization of part_number -> part
            "total_parts": 1,
            "records": [
                {
                    "type": "location",
                    "timestamp": 1710000000000,
                    "latitude": 32.071,
                    "longitude": 34.774,
                    "accuracy": 10.0,
                    "battery_level": 90,
                    "network_type": "wifi",
                    "provider": "gps",
                },
                {
                    "type": "driving",
                    "timestamp": 1710000000500,
                    "event_type": "driving_start",
                    "location": {"latitude": 32.072, "longitude": 34.775, "accuracy": 5.0},
                    "speed": 0.0,
                    "bearing": 0.0,
                },
            ],
        }
        resp = client.post(
            "/location/api/batch-sync",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["sync_id"] == payload["sync_id"]
        assert data["part"] == payload["part_number"]
        assert data["total_parts"] == payload["total_parts"]
        assert data["records_processed"] == 2
        assert data["sync_complete"] is True
        assert data["storage_mode"] == "database"
        pr = data["processing_results"]
        assert pr["location"] == 1
        assert pr["driving"] == 1
        assert pr["errors"] == 0
        assert len(pr["details"]) == 2

    def test_batch_sync_validation_missing_fields(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        # missing records
        payload = {
            "sync_id": "device-3_1710000000000",
            "device_id": "device-3",
            "user_name": "adar",
            "part": 1,
            "total_parts": 1,
        }
        resp = client.post(
            "/location/api/batch-sync",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        # Pydantic will complain that records is required
        assert resp.status_code == 422

    def test_batch_sync_partial_errors(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "sync_id": "device-4_1710000000000",
            "device_id": "device-4",
            "user_name": "adar",
            "part": 1,
            "total_parts": 2,
            "records": [
                {
                    "type": "location",
                    "timestamp": 1710000000000,
                    "latitude": 32.071,
                    "longitude": 34.774,
                },
                {
                    "type": "foo",  # invalid type should be counted as error
                    "timestamp": 1710000000100,
                },
            ],
        }
        resp = client.post(
            "/location/api/batch-sync",
            json=payload,
            headers={"X-API-Token": LOC_TOKEN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sync_complete"] is False
        pr = data["processing_results"]
        assert pr["location"] == 1
        assert pr["driving"] == 0
        assert pr["errors"] == 1
        assert len(pr["details"]) == 2

