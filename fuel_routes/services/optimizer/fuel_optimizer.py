import math
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from fuel_routes.models import FuelStation


class NoFeasiblePlanException(Exception):
    """Raised when no fuel plan can satisfy the 500-mile vehicle range constraint."""
    pass


@dataclass
class CandidateStation:
    station: FuelStation
    route_mile: float
    detour_miles: float


@dataclass
class FuelStopResult:
    station_id: int
    name: str
    address: str
    city: str
    state: str
    latitude: float
    longitude: float
    retail_price: Decimal
    route_mile: float
    detour_miles: float
    gallons_purchased: float
    cost: Decimal


@dataclass
class OptimizationPlan:
    total_gallons_consumed: float
    total_fuel_cost: Decimal
    fuel_stops: List[FuelStopResult]
    candidate_count: int


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def point_to_segment_distance(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float
) -> Tuple[float, float]:
    """
    Project point (px, py) onto segment AB (ax, ay -> bx, by).
    Returns (distance_in_miles, fractional_t_along_segment [0..1]).
    """
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return haversine_miles(py, px, ay, ax), 0.0

    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    proj_x = ax + t * dx
    proj_y = ay + t * dy

    dist = haversine_miles(py, px, proj_y, proj_x)
    return dist, t


class FuelOptimizer:
    def __init__(
        self,
        max_range_miles: float = 500.0,
        mpg: float = 10.0,
        max_detour_miles: float = 15.0
    ):
        self.max_range_miles = max_range_miles
        self.mpg = mpg
        self.max_detour_miles = max_detour_miles

    def project_stations_to_route(
        self,
        stations: List[FuelStation],
        geometry: Dict[str, Any],
        total_route_distance: float
    ) -> List[CandidateStation]:
        """
        Projects each station onto the route GeoJSON geometry.
        Calculates route_mile and detour_miles for each station.
        Filters out stations with detour > max_detour_miles.
        """
        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            return []

        # 1. Compute cumulative distance along geometry segments
        segment_miles = []
        cum_miles = [0.0]
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i + 1]
            dist = haversine_miles(lat1, lon1, lat2, lon2)
            segment_miles.append(dist)
            cum_miles.append(cum_miles[-1] + dist)

        geom_total_miles = cum_miles[-1] if cum_miles[-1] > 0 else 1.0
        scale_factor = total_route_distance / geom_total_miles

        candidates = []

        for station in stations:
            if station.latitude is None or station.longitude is None:
                continue

            st_lat = float(station.latitude)
            st_lon = float(station.longitude)

            min_detour = float('inf')
            best_route_mile = 0.0

            # Project station onto each polyline segment
            for i in range(len(coordinates) - 1):
                ax, ay = coordinates[i]
                bx, by = coordinates[i + 1]

                dist, t = point_to_segment_distance(st_lon, st_lat, ax, ay, bx, by)
                detour = dist * 2.0  # round-trip detour

                if detour < min_detour:
                    min_detour = detour
                    best_route_mile = (cum_miles[i] + t * segment_miles[i]) * scale_factor

            if min_detour <= self.max_detour_miles:
                candidates.append(CandidateStation(
                    station=station,
                    route_mile=best_route_mile,
                    detour_miles=round(min_detour, 2)
                ))

        # Sort candidates by route_mile ascending
        candidates.sort(key=lambda c: (c.route_mile, c.station.retail_price, c.detour_miles, c.station.source_id))
        return candidates

    def optimize(
        self,
        stations: List[FuelStation],
        geometry: Dict[str, Any],
        total_route_distance: float
    ) -> OptimizationPlan:
        """
        Executes the greedy next-cheaper-station fuel optimization.
        Enforces that every leg <= 500 miles.
        """
        # If total route is within initial full tank range, no refuels needed!
        if total_route_distance <= self.max_range_miles:
            total_gallons = round(total_route_distance / self.mpg, 2)
            return OptimizationPlan(
                total_gallons_consumed=total_gallons,
                total_fuel_cost=Decimal('0.00'),
                fuel_stops=[],
                candidate_count=len(stations)
            )

        candidates = self.project_stations_to_route(stations, geometry, total_route_distance)
        if not candidates:
            raise NoFeasiblePlanException("No fuel stations found in route corridor to satisfy route range.")

        current_mile = 0.0
        current_range = self.max_range_miles
        selected_stops: List[FuelStopResult] = []
        total_cost = Decimal('0.00')

        while current_mile + current_range < total_route_distance:
            # Stations reachable with remaining range
            reachable = [
                c for c in candidates
                if c.route_mile > current_mile and c.route_mile <= current_mile + current_range
            ]

            if not reachable:
                raise NoFeasiblePlanException(
                    f"No fuel station reachable between mile {current_mile:.1f} and {current_mile + current_range:.1f}. "
                    f"Gap exceeds maximum {self.max_range_miles:.0f}-mile vehicle range."
                )

            # Look for cheaper station ahead within reachable window
            # If current stop exists, compare to current stop price, else compare reachable options
            cheaper_stations = []
            if selected_stops:
                curr_price = selected_stops[-1].retail_price
                cheaper_stations = [c for c in reachable if c.station.retail_price < curr_price]

            if cheaper_stations:
                # Pick cheapest reachable station ahead
                best_cand = min(cheaper_stations, key=lambda c: (c.station.retail_price, c.detour_miles, -c.route_mile))
            else:
                # Pick station that maximizes progress with lowest price/detour
                best_cand = min(reachable, key=lambda c: (c.station.retail_price, c.detour_miles, -c.route_mile))

            # Drive to best_cand
            dist_driven = best_cand.route_mile - current_mile
            current_range -= dist_driven
            current_mile = best_cand.route_mile

            # Determine how much fuel to purchase at best_cand
            # Look ahead from best_cand: Is there a cheaper station reachable within max range?
            lookahead_reachable = [
                c for c in candidates
                if c.route_mile > current_mile and c.route_mile <= current_mile + self.max_range_miles
            ]
            future_cheaper = [
                c for c in lookahead_reachable
                if c.station.retail_price < best_cand.station.retail_price
            ]

            if future_cheaper:
                # Buy only enough to reach that future cheaper station
                next_cheaper = min(future_cheaper, key=lambda c: c.route_mile)
                needed_range = next_cheaper.route_mile - current_mile
                purchase_range = max(0.0, min(self.max_range_miles - current_range, needed_range - current_range))
            else:
                # Fill tank to max capacity (or amount to complete trip)
                rem_trip_range = max(0.0, total_route_distance - current_mile)
                target_range = min(self.max_range_miles, rem_trip_range)
                purchase_range = max(0.0, target_range - current_range)

            # Prevent zero/infinitesimal purchases
            if purchase_range < 0.1 and current_mile + current_range < total_route_distance:
                purchase_range = min(self.max_range_miles - current_range, total_route_distance - current_mile - current_range)

            gallons = round(purchase_range / self.mpg, 2)
            stop_cost = (Decimal(str(gallons)) * best_cand.station.retail_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            current_range += purchase_range
            total_cost += stop_cost

            selected_stops.append(FuelStopResult(
                station_id=best_cand.station.source_id,
                name=best_cand.station.name,
                address=best_cand.station.address,
                city=best_cand.station.city,
                state=best_cand.station.state,
                latitude=float(best_cand.station.latitude),
                longitude=float(best_cand.station.longitude),
                retail_price=best_cand.station.retail_price,
                route_mile=round(best_cand.route_mile, 1),
                detour_miles=best_cand.detour_miles,
                gallons_purchased=gallons,
                cost=stop_cost
            ))

        total_gallons_consumed = round(total_route_distance / self.mpg, 2)

        return OptimizationPlan(
            total_gallons_consumed=total_gallons_consumed,
            total_fuel_cost=total_cost,
            fuel_stops=selected_stops,
            candidate_count=len(candidates)
        )
