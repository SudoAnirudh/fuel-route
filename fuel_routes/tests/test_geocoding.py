from django.test import TestCase
from fuel_routes.models import GeocodeCache
from fuel_routes.services.geocoding.nominatim import NominatimGeocoder


class NominatimGeocoderTest(TestCase):
    def setUp(self):
        self.geocoder = NominatimGeocoder()

    def test_geocode_known_us_location(self):
        res = self.geocoder.geocode("Chicago, IL")
        self.assertEqual(res.query, "Chicago, IL")
        self.assertTrue(res.is_us_location)
        self.assertEqual(res.state, "IL")
        self.assertEqual(res.country_code, "us")
        
        # Verify cached in database
        self.assertEqual(GeocodeCache.objects.filter(query="Chicago, IL").count(), 1)

    def test_geocode_known_non_us_location(self):
        res = self.geocoder.geocode("Toronto, ON")
        self.assertFalse(res.is_us_location)
        self.assertEqual(res.country_code, "ca")

    def test_geocode_caches_repeated_queries(self):
        # First call
        res1 = self.geocoder.geocode("Denver, CO")
        # Second call
        res2 = self.geocoder.geocode("Denver, CO")
        
        self.assertEqual(res1.latitude, res2.latitude)
        self.assertEqual(res1.longitude, res2.longitude)
        self.assertEqual(GeocodeCache.objects.filter(query="Denver, CO").count(), 1)
