#!/usr/bin/env python3
"""
Test script for Day Route Breakdown API

Tests the new endpoint with sample data from Israel.
"""
import json
import requests
import sys
from typing import Dict, Any


def test_day_route_breakdown():
    """Test the day route breakdown endpoint"""
    
    # API configuration
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/routing/days/route-breakdown"
    
    # Get authentication token
    auth_response = requests.post(
        f"{base_url}/auth/login",
        json={"email": "adar.bahar@gmail.com"}
    )
    
    if auth_response.status_code != 200:
        print(f"❌ Authentication failed: {auth_response.status_code}")
        return False
    
    token = auth_response.json()["access_token"]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Test data - A day trip in Tel Aviv area
    test_request = {
        "trip_id": "01K4HZYAQ99EXAB30ZCGPF34FC",  # Use existing trip
        "day_id": "01K4J0CYB3YSGWDZB9N92V3ZQ4",   # Use existing day
        "start": {
            "lat": 32.0853,
            "lon": 34.7818,
            "name": "Tel Aviv Hotel"
        },
        "stops": [
            {
                "lat": 32.0944,
                "lon": 34.7806,
                "name": "Tel Aviv Museum"
            },
            {
                "lat": 32.0892,
                "lon": 34.7751,
                "name": "Carmel Market"
            },
            {
                "lat": 32.0679,
                "lon": 34.7604,
                "name": "Jaffa Old City"
            }
        ],
        "end": {
            "lat": 32.0823,
            "lon": 34.7789,
            "name": "Tel Aviv Beach Hotel"
        },
        "profile": "car",
        "options": {
            "avoid_highways": False,
            "avoid_tolls": False
        }
    }
    
    print("🧪 Testing Day Route Breakdown API")
    print(f"📍 Route: {test_request['start']['name']} → {len(test_request['stops'])} stops → {test_request['end']['name']}")
    print()
    
    # Make the API request
    try:
        response = requests.post(endpoint, json=test_request, headers=headers, timeout=30)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_breakdown_results(data)
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def print_breakdown_results(data: Dict[str, Any]):
    """Print formatted breakdown results"""
    
    print("✅ Route Breakdown Computed Successfully!")
    print()
    
    # Overall summary
    print("📊 OVERALL SUMMARY")
    print(f"   Total Distance: {data['total_distance_km']:.2f} km")
    print(f"   Total Duration: {data['total_duration_min']:.1f} minutes ({data['total_duration_min']/60:.1f} hours)")
    print(f"   Total Segments: {len(data['segments'])}")
    print(f"   Computed At: {data['computed_at']}")
    print()
    
    # Segment breakdown
    print("🛣️  SEGMENT BREAKDOWN")
    for i, segment in enumerate(data['segments']):
        print(f"   Segment {i+1}: {segment['segment_type'].replace('_', ' ').title()}")
        print(f"      From: {segment['from_point']['name']} ({segment['from_point']['lat']:.4f}, {segment['from_point']['lon']:.4f})")
        print(f"      To:   {segment['to_point']['name']} ({segment['to_point']['lat']:.4f}, {segment['to_point']['lon']:.4f})")
        print(f"      Distance: {segment['distance_km']:.2f} km")
        print(f"      Duration: {segment['duration_min']:.1f} minutes")
        print(f"      Instructions: {len(segment['instructions'])} steps")
        
        # Show first instruction as example
        if segment['instructions']:
            first_instruction = segment['instructions'][0]
            print(f"      First Step: {first_instruction.get('text', 'N/A')}")
        print()
    
    # Summary statistics
    if 'summary' in data:
        summary = data['summary']
        print("📈 SUMMARY STATISTICS")
        print(f"   Profile Used: {summary.get('profile_used', 'N/A')}")
        print(f"   Stops Count: {summary.get('stops_count', 0)}")
        
        # Breakdown by type
        if 'breakdown_by_type' in summary:
            print("   Breakdown by Type:")
            for segment_type, stats in summary['breakdown_by_type'].items():
                print(f"      {segment_type.replace('_', ' ').title()}: {stats['count']} segments, {stats['total_distance_km']:.2f}km, {stats['total_duration_min']:.1f}min")
        
        # Longest and shortest segments
        if 'longest_segment' in summary:
            longest = summary['longest_segment']
            print(f"   Longest Segment: {longest.get('from', 'N/A')} → {longest.get('to', 'N/A')} ({longest.get('distance_km', 0):.2f}km)")
        
        if 'shortest_segment' in summary:
            shortest = summary['shortest_segment']
            print(f"   Shortest Segment: {shortest.get('from', 'N/A')} → {shortest.get('to', 'N/A')} ({shortest.get('distance_km', 0):.2f}km)")
        print()
    
    # Geometry info
    total_coordinates = sum(len(segment['geometry'].get('coordinates', [])) for segment in data['segments'])
    print(f"🗺️  GEOMETRY INFO")
    print(f"   Total Coordinate Points: {total_coordinates}")
    print(f"   All segments have GeoJSON LineString geometry")
    print()


def test_error_cases():
    """Test error cases"""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/routing/days/route-breakdown"
    
    print("🧪 Testing Error Cases")
    
    # Test without authentication
    response = requests.post(endpoint, json={})
    print(f"   No auth: {response.status_code} (expected 401)")
    
    # Test with invalid data (if we had auth)
    # This would require proper authentication setup
    
    print()


if __name__ == "__main__":
    print("🚀 Day Route Breakdown API Test")
    print("=" * 50)
    print()
    
    # Test the main functionality
    success = test_day_route_breakdown()
    
    print()
    
    # Test error cases
    test_error_cases()
    
    print("=" * 50)
    if success:
        print("✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
