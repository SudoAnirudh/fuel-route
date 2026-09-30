from decimal import Decimal
from django.test import TestCase
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from fuel_routes.models import FuelStation


class FuelRouteAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('import_fuel_prices', clear=True)

    def setUp(self):
        self.client = APIClient()
        self.plan_url = reverse('fuel_routes:route-plan')
        self.health_url = reverse('fuel_routes:health-check')

    def test_healthz_endpoint(self):
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["database"], "healthy")

    def test_valid_route_plan_request(self):
        payload = {
            "start": "Chicago, IL",
            "finish": "Denver, CO"
        }
        response = self.client.post(self.plan_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("route_distance_miles", data)
        self.assertIn("route_geometry", data)
        self.assertIn("total_fuel_cost", data)
        self.assertIn("fuel_stops", data)

        # Check vehicle assumptions
        self.assertEqual(data["vehicle_assumptions"]["max_range_miles"], 500.0)
        self.assertEqual(data["vehicle_assumptions"]["fuel_economy_mpg"], 10.0)

        # Check metadata
        self.assertIn("routing_provider", data["metadata"])
        self.assertIn("external_routing_calls", data["metadata"])
        self.assertLessEqual(data["metadata"]["external_routing_calls"], 1)

    def test_non_us_location_validation(self):
        payload = {
            "start": "Toronto, ON",
            "finish": "Denver, CO"
        }
        response = self.client.post(self.plan_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start", response.data)

    def test_missing_required_fields(self):
        payload = {
            "start": "Chicago, IL"
        }
        response = self.client.post(self.plan_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("finish", response.data)

    def test_cached_route_plan_minimizes_routing_calls(self):
        payload = {
            "start": "Chicago, IL",
            "finish": "Denver, CO"
        }
        # First call -> external_calls <= 1
        resp1 = self.client.post(self.plan_url, payload, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Second call -> external_calls MUST be 0!
        resp2 = self.client.post(self.plan_url, payload, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertEqual(resp2.data["metadata"]["external_routing_calls"], 0)
