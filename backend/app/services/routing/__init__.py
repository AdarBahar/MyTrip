"""
Routing services
"""
from app.services.routing.base import (
    RoutingProvider,
    RoutePoint,
    RouteLeg,
    RouteResult
)
from app.services.routing.graphhopper_cloud import GraphHopperCloudProvider
from app.services.routing.graphhopper_selfhost import GraphHopperSelfHostProvider
from app.core.config import settings


def get_routing_provider() -> RoutingProvider:
    """Get the configured routing provider"""

    mode = settings.GRAPHHOPPER_MODE.lower()

    if mode == "cloud":
        return GraphHopperCloudProvider()
    elif mode == "selfhost":
        return GraphHopperSelfHostProvider()
    else:
        raise ValueError(f"Unknown routing mode: {mode}")


__all__ = [
    "RoutingProvider",
    "RoutePoint",
    "RouteLeg",
    "RouteResult",
    "GraphHopperCloudProvider",
    "GraphHopperSelfHostProvider",
    "get_routing_provider"
]