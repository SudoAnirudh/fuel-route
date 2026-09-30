from rest_framework import serializers


class RoutePlanRequestSerializer(serializers.Serializer):
    start = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Start location in the USA (e.g. 'Chicago, IL')"
    )
    finish = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Finish location in the USA (e.g. 'Denver, CO')"
    )


class LocationPointSerializer(serializers.Serializer):
    query = serializers.CharField()
    display_name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class VehicleAssumptionsSerializer(serializers.Serializer):
    max_range_miles = serializers.FloatField(default=500.0)
    fuel_economy_mpg = serializers.FloatField(default=10.0)


class FuelStopSerializer(serializers.Serializer):
    station_id = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    retail_price = serializers.CharField(help_text="Price per gallon in USD (Decimal)")
    route_mile = serializers.FloatField()
    detour_miles = serializers.FloatField()
    gallons_purchased = serializers.FloatField()
    cost = serializers.CharField(help_text="Total cost at this stop in USD (Decimal)")


class RoutePlanMetadataSerializer(serializers.Serializer):
    routing_provider = serializers.CharField()
    external_routing_calls = serializers.IntegerField()
    candidate_stations_evaluated = serializers.IntegerField()
    optimizer_time_ms = serializers.FloatField()
    total_request_time_ms = serializers.FloatField()


class RoutePlanResponseSerializer(serializers.Serializer):
    start = LocationPointSerializer()
    finish = LocationPointSerializer()
    route_distance_miles = serializers.FloatField()
    route_duration_seconds = serializers.FloatField()
    route_geometry = serializers.DictField(help_text="GeoJSON LineString geometry")
    vehicle_assumptions = VehicleAssumptionsSerializer()
    total_gallons_consumed = serializers.FloatField()
    total_fuel_cost = serializers.CharField(help_text="Total fuel cost in USD (Decimal)")
    fuel_stops_count = serializers.IntegerField()
    fuel_stops = FuelStopSerializer(many=True)
    metadata = RoutePlanMetadataSerializer()
