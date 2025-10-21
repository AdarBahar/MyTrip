"""
Tests for route optimization endpoint
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from app.main import app
from app.schemas.route_optimization import (
    RouteOptimizationRequest,
    OptimizationMeta,
    OptimizationData,
    LocationRequest,
    LocationType,
    Objective,
    VehicleProfile,
    Units,
    AvoidanceOption
)


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    with patch("app.core.auth.get_current_user") as mock:
        mock_user = Mock()
        mock_user.id = "test-user-123"
        mock.return_value = mock_user
        yield mock


@pytest.fixture
def sample_optimization_request():
    """Sample optimization request"""
    return {
        "prompt": "Optimize route for minimum travel time",
        "meta": {
            "version": "1.0",
            "objective": "time",
            "vehicle_profile": "car",
            "units": "metric",
            "avoid": ["tolls"]
        },
        "data": {
            "locations": [
                {
                    "id": "start-1",
                    "type": "START",
                    "name": "Tel Aviv",
                    "lat": 32.0853,
                    "lng": 34.7818,
                    "fixed_seq": True,
                    "seq": 1
                },
                {
                    "id": "stop-1",
                    "type": "STOP",
                    "name": "Ramat Gan",
                    "lat": 32.0944,
                    "lng": 34.7806,
                    "fixed_seq": False
                },
                {
                    "id": "stop-2",
                    "type": "STOP",
                    "name": "Petah Tikva",
                    "lat": 32.0878,
                    "lng": 34.8878,
                    "fixed_seq": False
                },
                {
                    "id": "end-1",
                    "type": "END",
                    "name": "Jerusalem",
                    "lat": 31.7683,
                    "lng": 35.2137,
                    "fixed_seq": True
                }
            ]
        }
    }


class TestRouteOptimization:
    """Test route optimization endpoint"""
    
    def test_optimization_happy_path(self, client, mock_auth, sample_optimization_request):
        """Test successful route optimization"""
        
        with patch("app.services.routing.route_optimization_service.RouteOptimizationService") as mock_service:
            # Mock successful optimization
            mock_instance = mock_service.return_value
            mock_instance.optimize_route = AsyncMock(return_value=Mock(
                version="1.0",
                objective=Objective.TIME,
                units=Units.METRIC,
                ordered=[
                    Mock(
                        seq=1, id="start-1", type=LocationType.START,
                        name="Tel Aviv", lat=32.0853, lng=34.7818,
                        fixed_seq=True, eta_min=0.0,
                        leg_distance_km=0.0, leg_duration_min=0.0
                    ),
                    Mock(
                        seq=2, id="stop-1", type=LocationType.STOP,
                        name="Ramat Gan", lat=32.0944, lng=34.7806,
                        fixed_seq=False, eta_min=15.0,
                        leg_distance_km=5.2, leg_duration_min=15.0
                    ),
                    Mock(
                        seq=3, id="stop-2", type=LocationType.STOP,
                        name="Petah Tikva", lat=32.0878, lng=34.8878,
                        fixed_seq=False, eta_min=35.0,
                        leg_distance_km=8.1, leg_duration_min=20.0
                    ),
                    Mock(
                        seq=4, id="end-1", type=LocationType.END,
                        name="Jerusalem", lat=31.7683, lng=35.2137,
                        fixed_seq=True, eta_min=95.0,
                        leg_distance_km=45.3, leg_duration_min=60.0
                    )
                ],
                summary=Mock(
                    stop_count=2,
                    total_distance_km=58.6,
                    total_duration_min=95.0
                ),
                geometry=Mock(
                    format="geojson",
                    route=Mock(
                        type="LineString",
                        coordinates=[[34.7818, 32.0853], [34.7806, 32.0944], [34.8878, 32.0878], [35.2137, 31.7683]]
                    ),
                    bounds=Mock(
                        min_lat=31.7683, min_lng=34.7806,
                        max_lat=32.0944, max_lng=35.2137
                    )
                ),
                diagnostics=Mock(
                    warnings=[],
                    assumptions=["Optimized for minimum travel time", "Avoiding: tolls"],
                    computation_notes=["Applied TSP optimization with nearest neighbor + 2-opt"]
                ),
                errors=[]
            ))
            
            response = client.post("/routing/optimize", json=sample_optimization_request)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["version"] == "1.0"
            assert data["objective"] == "time"
            assert data["units"] == "metric"
            assert len(data["ordered"]) == 4
            assert data["summary"]["stop_count"] == 2
            assert data["summary"]["total_distance_km"] == 58.6
            assert data["summary"]["total_duration_min"] == 95.0
    
    def test_multiple_start_error(self, client, mock_auth):
        """Test error for multiple START locations"""
        
        request_data = {
            "meta": {
                "objective": "time",
                "vehicle_profile": "car"
            },
            "data": {
                "locations": [
                    {
                        "id": "start-1",
                        "type": "START",
                        "name": "Tel Aviv",
                        "lat": 32.0853,
                        "lng": 34.7818,
                        "fixed_seq": True
                    },
                    {
                        "id": "start-2",
                        "type": "START",
                        "name": "Haifa",
                        "lat": 32.7940,
                        "lng": 34.9896,
                        "fixed_seq": True
                    },
                    {
                        "id": "end-1",
                        "type": "END",
                        "name": "Jerusalem",
                        "lat": 31.7683,
                        "lng": 35.2137,
                        "fixed_seq": True
                    }
                ]
            }
        }
        
        response = client.post("/routing/optimize", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data
        assert any(error["code"] == "MULTIPLE_START" for error in data["errors"])
    
    def test_missing_end_error(self, client, mock_auth):
        """Test error for missing END location"""
        
        request_data = {
            "meta": {
                "objective": "time",
                "vehicle_profile": "car"
            },
            "data": {
                "locations": [
                    {
                        "id": "start-1",
                        "type": "START",
                        "name": "Tel Aviv",
                        "lat": 32.0853,
                        "lng": 34.7818,
                        "fixed_seq": True
                    },
                    {
                        "id": "stop-1",
                        "type": "STOP",
                        "name": "Ramat Gan",
                        "lat": 32.0944,
                        "lng": 34.7806,
                        "fixed_seq": False
                    }
                ]
            }
        }
        
        response = client.post("/routing/optimize", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data
        assert any(error["code"] == "MISSING_END" for error in data["errors"])
    
    def test_fixed_sequence_conflict(self, client, mock_auth):
        """Test error for conflicting fixed sequences"""
        
        request_data = {
            "meta": {
                "objective": "time",
                "vehicle_profile": "car"
            },
            "data": {
                "locations": [
                    {
                        "id": "start-1",
                        "type": "START",
                        "name": "Tel Aviv",
                        "lat": 32.0853,
                        "lng": 34.7818,
                        "fixed_seq": True,
                        "seq": 1
                    },
                    {
                        "id": "stop-1",
                        "type": "STOP",
                        "name": "Ramat Gan",
                        "lat": 32.0944,
                        "lng": 34.7806,
                        "fixed_seq": True,
                        "seq": 2
                    },
                    {
                        "id": "stop-2",
                        "type": "STOP",
                        "name": "Petah Tikva",
                        "lat": 32.0878,
                        "lng": 34.8878,
                        "fixed_seq": True,
                        "seq": 2  # Duplicate sequence
                    },
                    {
                        "id": "end-1",
                        "type": "END",
                        "name": "Jerusalem",
                        "lat": 31.7683,
                        "lng": 35.2137,
                        "fixed_seq": True
                    }
                ]
            }
        }
        
        response = client.post("/routing/optimize", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data
        assert any(error["code"] == "FIXED_CONFLICT" for error in data["errors"])
    
    def test_invalid_coordinates(self, client, mock_auth):
        """Test error for invalid coordinates"""
        
        request_data = {
            "meta": {
                "objective": "time",
                "vehicle_profile": "car"
            },
            "data": {
                "locations": [
                    {
                        "id": "start-1",
                        "type": "START",
                        "name": "Invalid Location",
                        "lat": 91.0,  # Invalid latitude
                        "lng": 34.7818,
                        "fixed_seq": True
                    },
                    {
                        "id": "end-1",
                        "type": "END",
                        "name": "Jerusalem",
                        "lat": 31.7683,
                        "lng": 35.2137,
                        "fixed_seq": True
                    }
                ]
            }
        }
        
        response = client.post("/routing/optimize", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_disconnected_graph_error(self, client, mock_auth, sample_optimization_request):
        """Test error for unroutable locations"""
        
        with patch("app.services.routing.route_optimization_service.RouteOptimizationService") as mock_service:
            # Mock routability check failure
            from fastapi import HTTPException
            mock_instance = mock_service.return_value
            mock_instance.optimize_route = AsyncMock(side_effect=HTTPException(
                status_code=422,
                detail={"errors": [{"code": "DISCONNECTED_GRAPH", "message": "Locations are not routable"}]}
            ))
            
            response = client.post("/routing/optimize", json=sample_optimization_request)
            
            assert response.status_code == 422
    
    def test_authentication_required(self, client, sample_optimization_request):
        """Test that authentication is required"""
        
        response = client.post("/routing/optimize", json=sample_optimization_request)
        
        assert response.status_code == 401
