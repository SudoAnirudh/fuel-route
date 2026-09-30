from django.db import models


class FuelStation(models.Model):
    """
    Model representing a fuel station imported from the OPIS workbook,
    enriched with geocoding information and spatial coordinates.
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'Successfully Geocoded'),
        ('FAILED', 'Geocoding Failed'),
        ('AMBIGUOUS', 'Ambiguous Address'),
        ('EXCLUDED_NON_US', 'Excluded Non-US Region'),
    ]

    source_id = models.BigIntegerField(help_text="OPIS Truckstop ID from workbook")
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=10, db_index=True)
    rack_id = models.BigIntegerField()
    retail_price = models.DecimalField(max_digits=10, decimal_places=4, db_index=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    geocode_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='SUCCESS', db_index=True)
    geocode_provider = models.CharField(max_length=50, default='geocoded_fixture_v1')
    geocode_confidence = models.FloatField(default=1.0)
    dataset_version = models.CharField(max_length=50, default='v1.0')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fuel Station"
        verbose_name_plural = "Fuel Stations"
        indexes = [
            models.Index(fields=['state', 'retail_price']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['source_id']),
            models.Index(fields=['geocode_status']),
        ]

    def __str__(self) -> str:
        return f"{self.name} - {self.city}, {self.state} (${self.retail_price}/gal)"


class GeocodeCache(models.Model):
    """
    Cache table for geocoding queries (e.g. user start/finish location strings).
    """
    query = models.CharField(max_length=255, unique=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    display_name = models.CharField(max_length=500, blank=True)
    state = models.CharField(max_length=10, blank=True)
    country_code = models.CharField(max_length=10, default='us')
    raw_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.query} -> ({self.latitude}, {self.longitude})"


class RouteCache(models.Model):
    """
    Cache table for external routing provider API responses.
    """
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    distance_miles = models.FloatField()
    duration_seconds = models.FloatField()
    geometry = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"RouteCache: {self.cache_key} ({self.distance_miles:.1f} mi)"
