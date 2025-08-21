"""
Base routing provider interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from shapely.geometry import LineString


@dataclass
class RoutePoint:
    """A point in a route"""
    lat: float
    lon: float
    name: Optional[str] = None


@dataclass
class RouteLeg:
    """A leg of a route between two points"""
    distance_km: float
    duration_min: float
    geometry: LineString
    instructions: List[Dict[str, Any]]
    meta: Dict[str, Any]


@dataclass
class RouteResult:
    """Result of a route computation"""
    total_km: float
    total_min: float
    geometry: LineString
    legs: List[RouteLeg]
    debug: Dict[str, Any]


class RoutingProvider(ABC):
    """Abstract base class for routing providers"""

    @abstractmethod
    def build_request(
        self,
        points: List[RoutePoint],
        profile: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build request parameters for the routing service"""
        pass

    @abstractmethod
    async def compute_route(
        self,
        points: List[RoutePoint],
        profile: str = "car",
        options: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        Compute a route between the given points

        Args:
            points: List of route points (minimum 2)
            profile: Routing profile (car, motorcycle, bike)
            options: Additional routing options

        Returns:
            RouteResult with computed route data
        """
        pass

    def supports_map_match(self) -> bool:
        """Check if provider supports map matching"""
        return False

    def supports_matrix(self) -> bool:
        """Check if provider supports distance matrix"""
        return False

    def get_supported_profiles(self) -> List[str]:
        """Get list of supported routing profiles"""
        return ["car", "motorcycle", "bike"]