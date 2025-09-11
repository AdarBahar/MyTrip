"""
Geometric utility functions for routing and distance calculations.

This module provides various geometric calculations commonly used in routing
and location-based services.
"""
from math import radians, sin, cos, sqrt, atan2
from typing import Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.
    
    Uses the Haversine formula to calculate the distance between two points
    on the Earth's surface given their latitude and longitude coordinates.
    
    Args:
        lat1: Latitude of the first point in decimal degrees
        lon1: Longitude of the first point in decimal degrees
        lat2: Latitude of the second point in decimal degrees
        lon2: Longitude of the second point in decimal degrees
        
    Returns:
        Distance between the two points in kilometers
        
    Example:
        >>> distance = haversine_km(32.0853, 34.7818, 31.7683, 35.2137)
        >>> print(f"Distance: {distance:.2f} km")
        Distance: 54.23 km
    """
    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371.0
    
    # Convert decimal degrees to radians
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    
    # Haversine formula
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return EARTH_RADIUS_KM * c


def estimate_travel_time_minutes(
    distance_km: float, 
    profile: str = "car",
    context: str = "urban"
) -> float:
    """
    Estimate travel time based on distance, profile, and context.
    
    Provides a more sophisticated fallback for travel time estimation
    than the naive 30 km/h assumption.
    
    Args:
        distance_km: Distance to travel in kilometers
        profile: Transportation profile ('car', 'bike', 'motorcycle', 'walking')
        context: Travel context ('urban', 'highway', 'rural', 'mixed')
        
    Returns:
        Estimated travel time in minutes
        
    Example:
        >>> time = estimate_travel_time_minutes(10.0, "car", "urban")
        >>> print(f"Estimated time: {time:.1f} minutes")
        Estimated time: 20.0 minutes
    """
    # Speed estimates in km/h based on profile and context
    speed_matrix = {
        "car": {
            "urban": 30.0,
            "highway": 80.0,
            "rural": 60.0,
            "mixed": 45.0
        },
        "motorcycle": {
            "urban": 35.0,
            "highway": 90.0,
            "rural": 70.0,
            "mixed": 50.0
        },
        "bike": {
            "urban": 15.0,
            "highway": 20.0,  # Unlikely but possible
            "rural": 18.0,
            "mixed": 16.0
        },
        "walking": {
            "urban": 5.0,
            "highway": 4.0,
            "rural": 4.5,
            "mixed": 4.5
        }
    }
    
    # Get speed for profile and context, with fallbacks
    profile_speeds = speed_matrix.get(profile, speed_matrix["car"])
    speed_kmh = profile_speeds.get(context, profile_speeds["mixed"])
    
    # Convert to minutes
    return (distance_km / speed_kmh) * 60.0


def calculate_bounding_box(
    points: list[Tuple[float, float]], 
    padding_km: float = 1.0
) -> Tuple[float, float, float, float]:
    """
    Calculate bounding box for a set of coordinate points.
    
    Args:
        points: List of (latitude, longitude) tuples
        padding_km: Additional padding around the bounding box in kilometers
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    if not points:
        raise ValueError("Cannot calculate bounding box for empty points list")
    
    lats, lons = zip(*points)
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Convert padding from km to approximate degrees
    # 1 degree latitude ≈ 111 km
    lat_padding = padding_km / 111.0
    # 1 degree longitude varies by latitude, use average
    avg_lat = (min_lat + max_lat) / 2
    lon_padding = padding_km / (111.0 * cos(radians(avg_lat)))
    
    return (
        min_lat - lat_padding,
        min_lon - lon_padding,
        max_lat + lat_padding,
        max_lon + lon_padding
    )
