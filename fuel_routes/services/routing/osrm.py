import math
import requests
from typing import Tuple, Dict, Any, List
from fuel_routes.models import RouteCache
from fuel_routes.services.routing.base import RoutingProvider, RouteResult

METERS_TO_MILES = 0.000621371


def calculate_haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in miles."""
    r = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class OSRMProvider(RoutingProvider):
    def __init__(self, base_url: str = "http://router.project-osrm.org/route/v1/driving", timeout: int = 8):
        self.base_url = base_url
        self.timeout = timeout

    def get_route(
        self,
        start_coords: Tuple[float, float],
        finish_coords: Tuple[float, float]
    ) -> RouteResult:
        start_lat, start_lon = start_coords
        finish_lat, finish_lon = finish_coords

        cache_key = f"osrm:{start_lat:.4f},{start_lon:.4f}->{finish_lat:.4f},{finish_lon:.4f}"
        
        # 1. Check RouteCache in Database
        cached_route = RouteCache.objects.filter(cache_key=cache_key).first()
        if cached_route:
            return RouteResult(
                distance_miles=cached_route.distance_miles,
                duration_seconds=cached_route.duration_seconds,
                geometry=cached_route.geometry,
                provider="OSRM (cached)",
                external_calls=0
            )

        # 2. Query OSRM HTTP API
        # Format: {lon},{lat};{lon},{lat}
        url = f"{self.base_url}/{start_lon},{start_lat};{finish_lon},{finish_lat}"
        params = {
            "overview": "full",
            "geometries": "geojson"
        }

        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()

            if "routes" not in data or not data["routes"]:
                raise ValueError("OSRM returned empty routes.")

            route = data["routes"][0]
            distance_meters = float(route["distance"])
            duration_seconds = float(route["duration"])
            geometry = route["geometry"]
            distance_miles = round(distance_meters * METERS_TO_MILES, 2)

            # Store in cache
            RouteCache.objects.create(
                cache_key=cache_key,
                distance_miles=distance_miles,
                duration_seconds=duration_seconds,
                geometry=geometry
            )

            return RouteResult(
                distance_miles=distance_miles,
                duration_seconds=duration_seconds,
                geometry=geometry,
                provider="OSRM",
                external_calls=1
            )

        except Exception as e:
            # Fallback mock polyline route generator if network fails
            direct_dist = calculate_haversine_miles(start_lat, start_lon, finish_lat, finish_lon)
            road_dist = round(direct_dist * 1.25, 2)  # Approx road distance factor
            duration = round(road_dist * 60.0, 1)    # Approx 60 mph average

            # Generate 20 interpolated waypoints
            num_points = 20
            coordinates = []
            for i in range(num_points + 1):
                t = i / float(num_points)
                curr_lat = start_lat + t * (finish_lat - start_lat)
                curr_lon = start_lon + t * (finish_lon - start_lon)
                coordinates.append([round(curr_lon, 6), round(curr_lat, 6)])

            mock_geometry = {
                "type": "LineString",
                "coordinates": coordinates
            }

            # Store fallback in cache
            RouteCache.objects.create(
                cache_key=cache_key,
                distance_miles=road_dist,
                duration_seconds=duration,
                geometry=mock_geometry
            )

            return RouteResult(
                distance_miles=road_dist,
                duration_seconds=duration,
                geometry=mock_geometry,
                provider="OSRM (fallback_interpolated)",
                external_calls=1
            )
