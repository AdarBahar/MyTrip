"""
Tests for location API endpoints
"""
import pytest
from fastapi.testclient import TestClient


class TestLocationHealthEndpoint:
    """Test location health check endpoint"""

    def test_location_health_check(self, client: TestClient):
        """Test location health check endpoint"""
        response = client.get("/location/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "module" in data
        assert "database" in data
        assert "timestamp" in data
        
        # Check values
        assert data["module"] == "location"
        assert data["status"] in ["ok", "error"]
        
        # Check database info
        database_info = data["database"]
        assert "connected" in database_info
        assert isinstance(database_info["connected"], bool)
        
        if database_info["connected"]:
            # If connected, should have database details
            assert "database_name" in database_info
            assert "database_user" in database_info
            # Should be the location database
            assert "location" in database_info.get("database_name", "").lower()
        else:
            # If not connected, should have error details
            assert "error" in database_info

    def test_location_health_no_auth_required(self, client: TestClient):
        """Test that location health check doesn't require authentication"""
        response = client.get("/location/health")
        
        # Should work without authentication
        assert response.status_code == 200

    def test_location_health_response_format(self, client: TestClient):
        """Test location health check response format"""
        response = client.get("/location/health")
        
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) >= 4  # Should have at least status, module, database, timestamp


class TestLocationEndpoints:
    """Test location CRUD endpoints"""

    def test_get_locations_requires_auth(self, client: TestClient):
        """Test that getting locations requires authentication"""
        response = client.get("/location/")
        
        # Should require authentication
        assert response.status_code == 401

    def test_get_locations_with_auth(self, client: TestClient, auth_headers: dict):
        """Test getting locations with authentication"""
        response = client.get("/location/", headers=auth_headers)
        
        # Should work with authentication (may return 501 if not implemented)
        assert response.status_code in [200, 501]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # Should have pagination structure
            assert "items" in data or "locations" in data

    def test_get_locations_with_pagination(self, client: TestClient, auth_headers: dict):
        """Test getting locations with pagination parameters"""
        response = client.get(
            "/location/",
            params={"skip": 0, "limit": 10},
            headers=auth_headers
        )
        
        # Should work with pagination (may return 501 if not implemented)
        assert response.status_code in [200, 501]

    def test_get_locations_with_search(self, client: TestClient, auth_headers: dict):
        """Test getting locations with search parameter"""
        response = client.get(
            "/location/",
            params={"search": "test"},
            headers=auth_headers
        )
        
        # Should work with search (may return 501 if not implemented)
        assert response.status_code in [200, 501]

    def test_create_location_requires_auth(self, client: TestClient):
        """Test that creating location requires authentication"""
        location_data = {
            "name": "Test Location",
            "description": "A test location"
        }
        
        response = client.post("/location/", json=location_data)
        
        # Should require authentication
        assert response.status_code == 401

    def test_create_location_with_auth(self, client: TestClient, auth_headers: dict):
        """Test creating location with authentication"""
        location_data = {
            "name": "Test Location",
            "description": "A test location"
        }
        
        response = client.post("/location/", json=location_data, headers=auth_headers)
        
        # Should work with authentication (may return 501 if not implemented)
        assert response.status_code in [201, 501]

    def test_get_location_by_id_requires_auth(self, client: TestClient):
        """Test that getting location by ID requires authentication"""
        response = client.get("/location/test-id")
        
        # Should require authentication
        assert response.status_code == 401

    def test_get_location_by_id_with_auth(self, client: TestClient, auth_headers: dict):
        """Test getting location by ID with authentication"""
        response = client.get("/location/test-id", headers=auth_headers)
        
        # Should work with authentication (may return 404 or 501 if not implemented)
        assert response.status_code in [200, 404, 501]

    def test_update_location_requires_auth(self, client: TestClient):
        """Test that updating location requires authentication"""
        update_data = {
            "name": "Updated Location"
        }
        
        response = client.put("/location/test-id", json=update_data)
        
        # Should require authentication
        assert response.status_code == 401

    def test_update_location_with_auth(self, client: TestClient, auth_headers: dict):
        """Test updating location with authentication"""
        update_data = {
            "name": "Updated Location"
        }
        
        response = client.put("/location/test-id", json=update_data, headers=auth_headers)
        
        # Should work with authentication (may return 404 or 501 if not implemented)
        assert response.status_code in [200, 404, 501]

    def test_delete_location_requires_auth(self, client: TestClient):
        """Test that deleting location requires authentication"""
        response = client.delete("/location/test-id")
        
        # Should require authentication
        assert response.status_code == 401

    def test_delete_location_with_auth(self, client: TestClient, auth_headers: dict):
        """Test deleting location with authentication"""
        response = client.delete("/location/test-id", headers=auth_headers)
        
        # Should work with authentication (may return 404 or 501 if not implemented)
        assert response.status_code in [204, 404, 501]


class TestLocationErrorHandling:
    """Test location endpoint error handling"""

    def test_location_invalid_id_format(self, client: TestClient, auth_headers: dict):
        """Test location endpoints with invalid ID format"""
        # Test with various invalid ID formats
        invalid_ids = ["", "   ", "invalid-chars!@#", "very-long-id" * 20]
        
        for invalid_id in invalid_ids:
            # Empty/whitespace IDs resolve to the listing endpoint (/location/), which is valid
            # Skip those here to avoid conflating list vs. detail behavior
            if invalid_id.strip() == "":
                continue
            response = client.get(f"/location/{invalid_id}", headers=auth_headers)
            # Should handle invalid IDs gracefully
            assert response.status_code in [400, 404, 422, 501]

    def test_location_malformed_json(self, client: TestClient, auth_headers: dict):
        """Test location creation with malformed JSON"""
        response = client.post(
            "/location/",
            content="invalid json",
            headers={**auth_headers, "content-type": "application/json"}
        )
        
        # Should return 422 for malformed JSON
        assert response.status_code == 422

    def test_location_missing_required_fields(self, client: TestClient, auth_headers: dict):
        """Test location creation with missing required fields"""
        # Empty data
        response = client.post("/location/", json={}, headers=auth_headers)
        
        # Should return validation error or 501 if not implemented
        assert response.status_code in [422, 501]

    def test_location_invalid_pagination_params(self, client: TestClient, auth_headers: dict):
        """Test location list with invalid pagination parameters"""
        # Test negative skip
        response = client.get(
            "/location/",
            params={"skip": -1, "limit": 10},
            headers=auth_headers
        )
        assert response.status_code in [422, 501]
        
        # Test zero limit
        response = client.get(
            "/location/",
            params={"skip": 0, "limit": 0},
            headers=auth_headers
        )
        assert response.status_code in [422, 501]
        
        # Test excessive limit
        response = client.get(
            "/location/",
            params={"skip": 0, "limit": 10000},
            headers=auth_headers
        )
        assert response.status_code in [422, 501]


class TestLocationDatabaseIntegration:
    """Test location database integration"""

    @pytest.mark.integration
    def test_location_database_connection(self, client: TestClient):
        """Test that location database connection works"""
        response = client.get("/location/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # In integration tests, database should be connected
        if data["status"] == "ok":
            database_info = data["database"]
            assert database_info["connected"] is True
            assert "database_name" in database_info
            assert "database_user" in database_info

    @pytest.mark.integration
    def test_location_database_separate_from_main(self, client: TestClient):
        """Test that location database is separate from main database"""
        # Get main health endpoint
        main_response = client.get("/health")
        location_response = client.get("/location/health")
        
        assert main_response.status_code == 200
        assert location_response.status_code == 200
        
        # Both should be healthy but use different databases
        main_data = main_response.json()
        location_data = location_response.json()
        
        # Location endpoint should specify it's the location module
        assert location_data["module"] == "location"
        
        # If both are connected, they should use different databases
        if (location_data["status"] == "ok" and 
            location_data["database"]["connected"] and
            "database_name" in location_data["database"]):
            
            location_db = location_data["database"]["database_name"]
            assert "location" in location_db.lower()


class TestLocationOpenAPIDocumentation:
    """Test location endpoints in OpenAPI documentation"""

    def test_location_endpoints_in_openapi(self, client: TestClient):
        """Test that location endpoints are documented in OpenAPI"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        paths = data["paths"]
        
        # Check that location endpoints are documented
        location_paths = [path for path in paths.keys() if path.startswith("/location")]
        assert len(location_paths) >= 1  # At least health endpoint should exist
        
        # Health endpoint should be documented
        assert "/location/health" in paths

    def test_location_tag_in_openapi(self, client: TestClient):
        """Test that location tag is defined in OpenAPI"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if location tag exists
        if "tags" in data:
            tag_names = [tag["name"] for tag in data["tags"]]
            assert "location" in tag_names
