from dataclasses import dataclass
from typing import Protocol, List, Tuple, Dict, Any


@dataclass(frozen=True)
class RouteResult:
    distance_miles: float
    duration_seconds: float
    geometry: Dict[str, Any]  # GeoJSON LineString e.g. {"type": "LineString", "coordinates": [[lon, lat], ...]}
    provider: str
    external_calls: int


class RoutingProvider(Protocol):
    def get_route(
        self,
        start_coords: Tuple[float, float],  # (lat, lon)
        finish_coords: Tuple[float, float]  # (lat, lon)
    ) -> RouteResult:
        """
        Fetch driving route between start and finish coordinates.
        Returns GeoJSON geometry, total distance in miles, duration in seconds.
        Target exactly 1 external routing call per uncached request.
        """
        ...
