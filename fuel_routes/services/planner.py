import time
from decimal import Decimal
from typing import Dict, Any, Optional
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import status
from fuel_routes.models import FuelStation
from fuel_routes.services.geocoding.nominatim import NominatimGeocoder
from fuel_routes.services.routing.osrm import OSRMProvider
from fuel_routes.services.optimizer.fuel_optimizer import FuelOptimizer, NoFeasiblePlanException


class UnprocessableEntityException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Unprocessable entity'
    default_code = 'unprocessable_entity'



class PlannerService:
    def __init__(
        self,
        geocoder=None,
        routing_provider=None,
        optimizer=None
    ):
        self.geocoder = geocoder or NominatimGeocoder()
        self.routing_provider = routing_provider or OSRMProvider()
        self.optimizer = optimizer or FuelOptimizer()

    def plan_route(self, start_location: str, finish_location: str) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Geocode Start Location
        try:
            start_geo = self.geocoder.geocode(start_location)
        except Exception as e:
            raise ValidationError({"start": f"Could not resolve start location '{start_location}': {str(e)}"})

        if not start_geo.is_us_location:
            raise ValidationError({"start": f"Start location '{start_location}' is outside the United States."})

        # 2. Geocode Finish Location
        try:
            finish_geo = self.geocoder.geocode(finish_location)
        except Exception as e:
            raise ValidationError({"finish": f"Could not resolve finish location '{finish_location}': {str(e)}"})

        if not finish_geo.is_us_location:
            raise ValidationError({"finish": f"Finish location '{finish_location}' is outside the United States."})

        # 3. Request Route Geometry & Distance
        route_res = self.routing_provider.get_route(
            start_coords=(start_geo.latitude, start_geo.longitude),
            finish_coords=(finish_geo.latitude, finish_geo.longitude)
        )

        # 4. Filter Candidate Fuel Stations using Bounding Box Corridor
        coords = route_res.geometry.get("coordinates", [])
        if coords:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            min_lat, max_lat = min(lats) - 0.5, max(lats) + 0.5
            min_lon, max_lon = min(lons) - 0.5, max(lons) + 0.5

            candidate_qs = FuelStation.objects.filter(
                geocode_status='SUCCESS',
                latitude__gte=Decimal(str(round(min_lat, 4))),
                latitude__lte=Decimal(str(round(max_lat, 4))),
                longitude__gte=Decimal(str(round(min_lon, 4))),
                longitude__lte=Decimal(str(round(max_lon, 4)))
            )
        else:
            candidate_qs = FuelStation.objects.filter(geocode_status='SUCCESS')

        candidate_stations = list(candidate_qs)

        # 5. Run Fuel Optimizer
        opt_start = time.time()
        try:
            plan = self.optimizer.optimize(
                stations=candidate_stations,
                geometry=route_res.geometry,
                total_route_distance=route_res.distance_miles
            )
        except NoFeasiblePlanException as e:
            raise UnprocessableEntityException({
                "error": {
                    "code": "NO_FEASIBLE_FUEL_PLAN",
                    "message": str(e)
                }
            })
        opt_duration_ms = round((time.time() - opt_start) * 1000.0, 2)

        total_duration_ms = round((time.time() - start_time) * 1000.0, 2)

        # 6. Build Serialized Result Payload
        formatted_stops = [
            {
                "station_id": s.station_id,
                "name": s.name,
                "address": s.address,
                "city": s.city,
                "state": s.state,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "retail_price": str(s.retail_price),
                "route_mile": s.route_mile,
                "detour_miles": s.detour_miles,
                "gallons_purchased": s.gallons_purchased,
                "cost": str(s.cost)
            }
            for s in plan.fuel_stops
        ]

        return {
            "start": {
                "query": start_location,
                "display_name": start_geo.display_name,
                "latitude": start_geo.latitude,
                "longitude": start_geo.longitude
            },
            "finish": {
                "query": finish_location,
                "display_name": finish_geo.display_name,
                "latitude": finish_geo.latitude,
                "longitude": finish_geo.longitude
            },
            "route_distance_miles": route_res.distance_miles,
            "route_duration_seconds": route_res.duration_seconds,
            "route_geometry": route_res.geometry,
            "vehicle_assumptions": {
                "max_range_miles": self.optimizer.max_range_miles,
                "fuel_economy_mpg": self.optimizer.mpg
            },
            "total_gallons_consumed": plan.total_gallons_consumed,
            "total_fuel_cost": str(plan.total_fuel_cost),
            "fuel_stops_count": len(plan.fuel_stops),
            "fuel_stops": formatted_stops,
            "metadata": {
                "routing_provider": route_res.provider,
                "external_routing_calls": route_res.external_calls,
                "candidate_stations_evaluated": plan.candidate_count,
                "optimizer_time_ms": opt_duration_ms,
                "total_request_time_ms": total_duration_ms
            }
        }
