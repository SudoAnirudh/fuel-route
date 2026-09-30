from django.test import TestCase
from fuel_routes.models import RouteCache
from fuel_routes.services.routing.osrm import OSRMProvider


class OSRMProviderTest(TestCase):
    def setUp(self):
        self.provider = OSRMProvider()
        self.start_coords = (41.8781, -87.6298)  # Chicago
        self.finish_coords = (39.7392, -104.9903)  # Denver

    def test_get_route_uncached_and_cached(self):
        # 1. Uncached call
        res1 = self.provider.get_route(self.start_coords, self.finish_coords)
        self.assertGreater(res1.distance_miles, 800.0)
        self.assertIn("coordinates", res1.geometry)
        self.assertIn(res1.external_calls, [0, 1])

        # Verify cached in database
        self.assertEqual(RouteCache.objects.count(), 1)

        # 2. Cached call -> external_calls MUST be 0!
        res2 = self.provider.get_route(self.start_coords, self.finish_coords)
        self.assertEqual(res2.external_calls, 0)
        self.assertEqual(res1.distance_miles, res2.distance_miles)
