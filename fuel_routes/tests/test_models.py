from decimal import Decimal
from django.test import TestCase
from fuel_routes.models import FuelStation, GeocodeCache, RouteCache


class FuelStationModelTest(TestCase):
    def test_create_fuel_station(self):
        station = FuelStation.objects.create(
            source_id=101,
            name="TEST TRUCKSTOP",
            address="123 HIGHWAY 80",
            city="CHICAGO",
            state="IL",
            rack_id=50,
            retail_price=Decimal("3.259"),
            latitude=Decimal("41.8781"),
            longitude=Decimal("-87.6298"),
            geocode_status="SUCCESS"
        )
        self.assertEqual(str(station), "TEST TRUCKSTOP - CHICAGO, IL ($3.259/gal)")
        self.assertEqual(station.retail_price, Decimal("3.259"))
        self.assertEqual(FuelStation.objects.filter(state="IL").count(), 1)


class GeocodeCacheModelTest(TestCase):
    def test_create_geocode_cache(self):
        cache = GeocodeCache.objects.create(
            query="Chicago, IL",
            latitude=Decimal("41.8781"),
            longitude=Decimal("-87.6298"),
            display_name="Chicago, Illinois, USA",
            state="IL",
            country_code="us"
        )
        self.assertIn("Chicago, IL", str(cache))
        self.assertEqual(GeocodeCache.objects.filter(query="Chicago, IL").count(), 1)


class RouteCacheModelTest(TestCase):
    def test_create_route_cache(self):
        route_cache = RouteCache.objects.create(
            cache_key="osrm:41.8781,-87.6298->39.7392,-104.9903",
            distance_miles=1002.5,
            duration_seconds=36000.0,
            geometry={"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-104.9903, 39.7392]]}
        )
        self.assertIn("1002.5 mi", str(route_cache))
        self.assertEqual(route_cache.distance_miles, 1002.5)
