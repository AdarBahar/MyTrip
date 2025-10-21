#!/usr/bin/env python3
"""
Test script for route optimization endpoint
"""
import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.routing.route_optimization_service import RouteOptimizationService
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


def create_sample_request() -> RouteOptimizationRequest:
    """Create a sample optimization request"""
    
    return RouteOptimizationRequest(
        prompt="Optimize route for minimum travel time, considering traffic patterns",
        meta=OptimizationMeta(
            version="1.0",
            objective=Objective.TIME,
            vehicle_profile=VehicleProfile.CAR,
            units=Units.METRIC,
            avoid=[AvoidanceOption.TOLLS, AvoidanceOption.HIGHWAYS]
        ),
        data=OptimizationData(
            locations=[
                LocationRequest(
                    id="start-tel-aviv",
                    type=LocationType.START,
                    name="Tel Aviv Central Station",
                    lat=32.0853,
                    lng=34.7818,
                    fixed_seq=True,
                    seq=1
                ),
                LocationRequest(
                    id="stop-ramat-gan",
                    type=LocationType.STOP,
                    name="Ramat Gan Diamond Exchange",
                    lat=32.0944,
                    lng=34.7806,
                    fixed_seq=False
                ),
                LocationRequest(
                    id="stop-petah-tikva",
                    type=LocationType.STOP,
                    name="Petah Tikva Mall",
                    lat=32.0878,
                    lng=34.8878,
                    fixed_seq=False
                ),
                LocationRequest(
                    id="stop-bnei-brak",
                    type=LocationType.STOP,
                    name="Bnei Brak Center",
                    lat=32.0809,
                    lng=34.8338,
                    fixed_seq=True,
                    seq=3  # Fixed as third stop
                ),
                LocationRequest(
                    id="stop-herzliya",
                    type=LocationType.STOP,
                    name="Herzliya Marina",
                    lat=32.1739,
                    lng=34.8082,
                    fixed_seq=False
                ),
                LocationRequest(
                    id="end-jerusalem",
                    type=LocationType.END,
                    name="Jerusalem Central Bus Station",
                    lat=31.7683,
                    lng=35.2137,
                    fixed_seq=True
                )
            ]
        )
    )


def create_fixed_sequence_conflict_request() -> RouteOptimizationRequest:
    """Create a request with fixed sequence conflicts (for testing validation)"""
    
    return RouteOptimizationRequest(
        meta=OptimizationMeta(
            objective=Objective.DISTANCE,
            vehicle_profile=VehicleProfile.CAR
        ),
        data=OptimizationData(
            locations=[
                LocationRequest(
                    id="start-1",
                    type=LocationType.START,
                    name="Start",
                    lat=32.0853,
                    lng=34.7818,
                    fixed_seq=True,
                    seq=1
                ),
                LocationRequest(
                    id="stop-1",
                    type=LocationType.STOP,
                    name="Stop 1",
                    lat=32.0944,
                    lng=34.7806,
                    fixed_seq=True,
                    seq=2
                ),
                LocationRequest(
                    id="stop-2",
                    type=LocationType.STOP,
                    name="Stop 2",
                    lat=32.0878,
                    lng=34.8878,
                    fixed_seq=True,
                    seq=2  # Duplicate sequence - should cause error
                ),
                LocationRequest(
                    id="end-1",
                    type=LocationType.END,
                    name="End",
                    lat=31.7683,
                    lng=35.2137,
                    fixed_seq=True
                )
            ]
        )
    )


async def test_optimization_service():
    """Test the optimization service directly"""
    
    print("🧪 Testing Route Optimization Service")
    print("=" * 50)
    
    try:
        # Initialize service
        service = RouteOptimizationService()
        
        # Test 1: Happy path
        print("\n📍 Test 1: Happy Path Optimization")
        request = create_sample_request()
        
        print(f"Request: {len(request.data.locations)} locations")
        print(f"Objective: {request.meta.objective}")
        print(f"Vehicle: {request.meta.vehicle_profile}")
        print(f"Avoid: {[a.value for a in request.meta.avoid]}")
        
        result = await service.optimize_route(request)
        
        print(f"\n✅ Optimization successful!")
        print(f"Ordered locations: {len(result.ordered)}")
        print(f"Total distance: {result.summary.total_distance_km:.2f} km")
        print(f"Total duration: {result.summary.total_duration_min:.1f} minutes")
        print(f"Stop count: {result.summary.stop_count}")
        
        print("\nOptimized order:")
        for i, location in enumerate(result.ordered):
            print(f"  {i+1}. {location.name} ({location.type}) - ETA: {location.eta_min:.1f}min")
        
        print(f"\nDiagnostics:")
        print(f"  Warnings: {result.diagnostics.warnings}")
        print(f"  Assumptions: {result.diagnostics.assumptions}")
        print(f"  Notes: {result.diagnostics.computation_notes}")
        
        # Test 2: Validation error
        print("\n📍 Test 2: Validation Error (Fixed Sequence Conflict)")
        try:
            conflict_request = create_fixed_sequence_conflict_request()
            await service.optimize_route(conflict_request)
            print("❌ Expected validation error but got success")
        except Exception as e:
            print(f"✅ Validation error caught as expected: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_curl_example():
    """Generate example cURL command"""
    
    request = create_sample_request()
    request_json = request.dict()
    
    curl_command = f"""
# Example cURL request for route optimization
curl -X POST "http://localhost:8000/routing/optimize" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -d '{json.dumps(request_json, indent=2)}'

# Expected response (200 OK):
{{
  "version": "1.0",
  "objective": "time",
  "units": "metric",
  "ordered": [
    {{
      "seq": 1,
      "id": "start-tel-aviv",
      "type": "START",
      "name": "Tel Aviv Central Station",
      "lat": 32.0853,
      "lng": 34.7818,
      "fixed_seq": true,
      "eta_min": 0.0,
      "leg_distance_km": 0.0,
      "leg_duration_min": 0.0
    }},
    {{
      "seq": 2,
      "id": "stop-ramat-gan",
      "type": "STOP",
      "name": "Ramat Gan Diamond Exchange",
      "lat": 32.0944,
      "lng": 34.7806,
      "fixed_seq": false,
      "eta_min": 15.2,
      "leg_distance_km": 5.1,
      "leg_duration_min": 15.2
    }},
    // ... more optimized stops
  ],
  "summary": {{
    "stop_count": 4,
    "total_distance_km": 67.3,
    "total_duration_min": 89.5
  }},
  "geometry": {{
    "format": "geojson",
    "route": {{
      "type": "LineString",
      "coordinates": [[34.7818, 32.0853], [34.7806, 32.0944], ...]
    }},
    "bounds": {{
      "min_lat": 31.7683,
      "min_lng": 34.7806,
      "max_lat": 32.1739,
      "max_lng": 35.2137
    }}
  }},
  "diagnostics": {{
    "warnings": [],
    "assumptions": ["Optimized for minimum travel time", "Avoiding: tolls, highways"],
    "computation_notes": ["Applied TSP optimization with nearest neighbor + 2-opt"]
  }},
  "errors": []
}}

# Error response example (400 Bad Request):
{{
  "version": "1.0",
  "errors": [
    {{
      "code": "MULTIPLE_START",
      "message": "More than one START provided"
    }}
  ]
}}
"""
    
    return curl_command


async def main():
    """Main test function"""
    
    print("🚀 Route Optimization Test Suite")
    print("=" * 50)
    
    # Test the service
    success = await test_optimization_service()
    
    if success:
        print("\n📋 cURL Example")
        print("=" * 50)
        print(generate_curl_example())
        
        print("\n🎉 All tests completed successfully!")
        print("\nTo test the endpoint:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Get a JWT token from /auth/login")
        print("3. Use the cURL command above with your token")
        print("4. Or test via Swagger UI at http://localhost:8000/docs")
        
        return 0
    else:
        print("\n❌ Tests failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
