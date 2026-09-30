from django.test import TestCase
from django.core.management import call_command
from fuel_routes.models import FuelStation


class ImportFuelPricesCommandTest(TestCase):
    def test_import_command_populates_database(self):
        call_command('import_fuel_prices', clear=True)
        
        total_count = FuelStation.objects.count()
        us_count = FuelStation.objects.filter(geocode_status='SUCCESS').count()
        non_us_count = FuelStation.objects.filter(geocode_status='EXCLUDED_NON_US').count()

        self.assertEqual(total_count, 8151)
        self.assertEqual(us_count, 7531)
        self.assertEqual(non_us_count, 620)
