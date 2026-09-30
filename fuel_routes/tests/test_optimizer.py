from decimal import Decimal
from django.test import TestCase
from fuel_routes.models import FuelStation
from fuel_routes.services.optimizer.fuel_optimizer import (
    FuelOptimizer,
    NoFeasiblePlanException
)


class FuelOptimizerTest(TestCase):
    def setUp(self):
        self.optimizer = FuelOptimizer(max_range_miles=500.0, mpg=10.0, max_detour_miles=15.0)

    def _create_mock_geometry(self):
        # Straight line geometry from (-87.0, 40.0) to (-103.0, 40.0)
        return {
            "type": "LineString",
            "coordinates": [
                [-87.0, 40.0],
                [-95.0, 40.0],
                [-103.0, 40.0]
            ]
        }

    def test_trip_under_500_miles(self):
        geometry = {
            "type": "LineString",
            "coordinates": [[-87.0, 40.0], [-90.0, 40.0]]
        }
        plan = self.optimizer.optimize(stations=[], geometry=geometry, total_route_distance=250.0)
        
        self.assertEqual(len(plan.fuel_stops), 0)
        self.assertEqual(plan.total_fuel_cost, Decimal("0.00"))
        self.assertEqual(plan.total_gallons_consumed, 25.0)

    def test_trip_exactly_500_miles(self):
        geometry = {
            "type": "LineString",
            "coordinates": [[-87.0, 40.0], [-92.0, 40.0]]
        }
        plan = self.optimizer.optimize(stations=[], geometry=geometry, total_route_distance=500.0)
        
        self.assertEqual(len(plan.fuel_stops), 0)
        self.assertEqual(plan.total_fuel_cost, Decimal("0.00"))
        self.assertEqual(plan.total_gallons_consumed, 50.0)

    def test_trip_over_500_miles_with_stops(self):
        geometry = self._create_mock_geometry()
        
        st_a = FuelStation.objects.create(
            source_id=1, name="Station A", address="I-80 Exit 1", city="Town A", state="IL",
            rack_id=1, retail_price=Decimal("3.50"), latitude=Decimal("40.0"), longitude=Decimal("-91.0"),
            geocode_status="SUCCESS"
        )
        st_b = FuelStation.objects.create(
            source_id=2, name="Station B", address="I-80 Exit 2", city="Town B", state="IA",
            rack_id=2, retail_price=Decimal("3.20"), latitude=Decimal("40.0"), longitude=Decimal("-98.0"),
            geocode_status="SUCCESS"
        )

        plan = self.optimizer.optimize(
            stations=[st_a, st_b],
            geometry=geometry,
            total_route_distance=900.0
        )

        self.assertGreater(len(plan.fuel_stops), 0)
        self.assertGreater(plan.total_fuel_cost, Decimal("0.00"))

        # Verify no segment > 500 miles
        curr = 0.0
        for stop in plan.fuel_stops:
            leg = stop.route_mile - curr
            self.assertLessEqual(leg, 500.0)
            curr = stop.route_mile
        self.assertLessEqual(900.0 - curr, 500.0)

    def test_no_feasible_plan_raises_exception(self):
        geometry = self._create_mock_geometry()
        with self.assertRaises(NoFeasiblePlanException):
            self.optimizer.optimize(stations=[], geometry=geometry, total_route_distance=1200.0)

    def test_cheaper_station_ahead_preference(self):
        geometry = self._create_mock_geometry()
        
        # Station A at mile ~280 ($3.80/gal)
        # Station B at mile ~450 ($3.00/gal) - cheaper!
        # Station C at mile ~700 ($3.20/gal) - needed to reach 900 miles
        st_a = FuelStation.objects.create(
            source_id=1, name="Expensive A", address="Add 1", city="City A", state="IL",
            rack_id=1, retail_price=Decimal("3.80"), latitude=Decimal("40.0"), longitude=Decimal("-89.5"),
            geocode_status="SUCCESS"
        )
        st_b = FuelStation.objects.create(
            source_id=2, name="Cheap B", address="Add 2", city="City B", state="IL",
            rack_id=2, retail_price=Decimal("3.00"), latitude=Decimal("40.0"), longitude=Decimal("-92.0"),
            geocode_status="SUCCESS"
        )
        st_c = FuelStation.objects.create(
            source_id=3, name="Station C", address="Add 3", city="City C", state="IA",
            rack_id=3, retail_price=Decimal("3.20"), latitude=Decimal("40.0"), longitude=Decimal("-98.0"),
            geocode_status="SUCCESS"
        )

        plan = self.optimizer.optimize(
            stations=[st_a, st_b, st_c],
            geometry=geometry,
            total_route_distance=900.0
        )

        selected_ids = [s.station_id for s in plan.fuel_stops]
        self.assertIn(2, selected_ids)  # Cheap B selected

    def test_equal_prices_detour_tiebreak(self):
        geometry = self._create_mock_geometry()

        # Equal price, station 1 has 0 detour, station 2 has 5 mile detour
        # Station 3 at mile ~700 to reach 900 miles
        st_1 = FuelStation.objects.create(
            source_id=10, name="Direct Station", address="Add 1", city="City 1", state="IL",
            rack_id=1, retail_price=Decimal("3.00"), latitude=Decimal("40.0"), longitude=Decimal("-90.0"),
            geocode_status="SUCCESS"
        )
        st_2 = FuelStation.objects.create(
            source_id=11, name="Detour Station", address="Add 2", city="City 2", state="IL",
            rack_id=2, retail_price=Decimal("3.00"), latitude=Decimal("40.05"), longitude=Decimal("-90.0"),
            geocode_status="SUCCESS"
        )
        st_3 = FuelStation.objects.create(
            source_id=12, name="Next Leg Station", address="Add 3", city="City 3", state="NE",
            rack_id=3, retail_price=Decimal("3.10"), latitude=Decimal("40.0"), longitude=Decimal("-98.0"),
            geocode_status="SUCCESS"
        )

        plan = self.optimizer.optimize(
            stations=[st_1, st_2, st_3],
            geometry=geometry,
            total_route_distance=900.0
        )

        self.assertEqual(plan.fuel_stops[0].station_id, 10)  # Picked Direct Station
