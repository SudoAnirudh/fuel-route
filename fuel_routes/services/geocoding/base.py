from dataclasses import dataclass
from typing import Protocol, Optional


@dataclass(frozen=True)
class GeocodeResult:
    query: str
    latitude: float
    longitude: float
    display_name: str
    state: str
    country_code: str
    is_us_location: bool


class GeocoderProvider(Protocol):
    def geocode(self, location_query: str) -> GeocodeResult:
        """
        Geocode a location query string (e.g. 'Chicago, IL') to coordinates.
        Must enforce US-only validation.
        """
        ...
