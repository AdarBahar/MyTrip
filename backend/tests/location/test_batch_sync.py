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

    def _driving_rows(self, device_id: str):
        from tests.conftest import LocationTestingSessionLocal
        from app.models.location_records import DrivingRecord

        db = LocationTestingSessionLocal()
        try:
            return (
                db.query(DrivingRecord)
                .filter(DrivingRecord.device_id == device_id)
                .order_by(DrivingRecord.client_time)
                .all()
            )
        finally:
            db.close()

    def test_batch_sync_driving_trip_summary_stored(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "sync_id": "device-ts_1710000000000",
            "device_id": "device-ts",
            "user_name": "adar",
            "part": 1,
            "total_parts": 1,
            "records": [
                {
                    "type": "driving",
                    "event_type": "driving_data",
                    "timestamp": 1710000000000,
                    "location": {"latitude": 32.07, "longitude": 34.77},
                    "trip_id": "trip-batch-1",
                },
                {
                    "type": "driving",
                    "event_type": "driving_stop",
                    "timestamp": 1710000001000,
                    "location": {"latitude": 32.08, "longitude": 34.78, "accuracy": 4.0},
                    "trip_id": "trip-batch-1",
                    "trip_summary": {
                        "duration_seconds": 900.0,
                        "distance_meters": 12000.0,
                        "avg_speed": 48.0,
                        "max_speed": 91.2,
                    },
                },
            ],
        }
        resp = client.post(
            "/location/api/batch-sync", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 200
        pr = resp.json()["processing_results"]
        assert pr["driving"] == 2
        assert pr["errors"] == 0

        data_row, stop_row = self._driving_rows("device-ts")
        assert data_row.trip_duration_seconds is None
        assert data_row.trip_max_speed is None
        assert stop_row.event_type == "driving_stop"
        assert stop_row.trip_id == "trip-batch-1"
        assert stop_row.trip_duration_seconds == pytest.approx(900.0)
        assert stop_row.trip_distance_meters == pytest.approx(12000.0)
        assert stop_row.trip_avg_speed == pytest.approx(48.0)
        assert stop_row.trip_max_speed == pytest.approx(91.2)

    def test_batch_sync_invalid_trip_summary_keeps_event(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("LOC_API_TOKEN", LOC_TOKEN)
        payload = {
            "sync_id": "device-ts-bad_1710000000000",
            "device_id": "device-ts-bad",
            "user_name": "adar",
            "part": 1,
            "total_parts": 1,
            "records": [
                {
                    "type": "driving",
                    "event_type": "driving_stop",
                    "timestamp": 1710000000000,
                    "location": {"latitude": 32.07, "longitude": 34.77},
                    "trip_summary": {"distance_meters": -5, "avg_speed": "fast"},
                }
            ],
        }
        resp = client.post(
            "/location/api/batch-sync", json=payload, headers={"X-API-Token": LOC_TOKEN}
        )
        assert resp.status_code == 200
        pr = resp.json()["processing_results"]
        assert pr["driving"] == 1
        assert pr["errors"] == 0
        assert "trip_summary ignored" in pr["details"][0]

        (row,) = self._driving_rows("device-ts-bad")
        assert row.trip_distance_meters is None
        assert row.trip_avg_speed is None

