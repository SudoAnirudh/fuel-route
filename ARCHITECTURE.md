# Architecture & Technical Design

## 1. Stack

- Python: use a currently supported version compatible with the selected Django release.
- Django: latest stable patch at implementation time.
- Django REST Framework.
- PostgreSQL recommended.
- PostGIS strongly recommended if available.
- Redis optional for response/geocoding caching.
- OSRM for routing.
- Pluggable geocoder interface.

## 2. Django structure

```text
src/
  config/
    settings/
      base.py
      local.py
      production.py
    urls.py
  routes/
    api/
      serializers.py
      views.py
      urls.py
    domain/
      models.py
      optimizer.py
      cost.py
      geometry.py
    services/
      planner.py
      geocoding.py
      routing.py
      candidates.py
      caching.py
    management/
      commands/
        import_fuel_prices.py
        geocode_fuel_stops.py
    tests/
      test_optimizer.py
      test_cost.py
      test_api.py
      test_routing_adapter.py
      test_geocoding_adapter.py
```

Keep HTTP concerns separate from domain logic.

## 3. Data model

### FuelStation

Suggested fields:

- `source_id`
- `name`
- `address`
- `city`
- `state`
- `rack_id`
- `retail_price`
- `latitude`
- `longitude`
- `location` (PostGIS Point, optional but recommended)
- `geocode_status`
- `geocode_source`
- `geocode_confidence`
- `dataset_version`
- timestamps

Indexes:

- `(state)`
- `(retail_price)`
- spatial index on `location`
- unique constraint appropriate to source identity.

Do not use station name as a primary key.

### GeocodeCache

- normalized_query
- latitude
- longitude
- country_code
- provider
- provider_response_hash
- status
- created_at
- expires_at

### RouteCache

- normalized start coordinate
- normalized finish coordinate
- routing profile
- provider/version
- distance
- duration
- geometry
- created_at
- expires_at

## 4. Request flow

```text
POST /api/v1/routes/plan
        |
        v
Validate request
        |
        v
Geocode start + finish
        |
        +---- cache hit ---> no external call
        |
        v
Route cache lookup
        |
        +---- cache hit ---> reuse geometry
        |
        v
OSRM route call
        |
        v
Decode route geometry
        |
        v
Generate route-distance index
        |
        v
Query fuel stations near route corridor
        |
        v
Project candidates onto route
        |
        v
Feasibility + cost optimizer
        |
        v
Calculate cost
        |
        v
Return map-ready JSON
```

## 5. Why one routing call is enough

The route geometry contains the road path.

Fuel stops are not used as routing waypoints during optimization. Instead:

1. find stations spatially near the route;
2. project each station to its nearest route position;
3. compute cumulative route miles;
4. optimize over route-mile positions.

This avoids `N` routing calls for `N` stations.

A later production enhancement could validate final station detours using a matrix/routing service, but that is not required for the assessment.

## 6. Candidate corridor

Use a configurable route corridor, e.g. 10–20 miles.

Do not hard-code the value into the optimizer.

If PostGIS is available:

- create route geometry;
- use `ST_DWithin`;
- use `ST_LineLocatePoint` for route position.

If PostGIS is unavailable:

- decode GeoJSON/polyline;
- use a spatial index such as an R-tree or Shapely STRtree;
- project candidates using Shapely.

PostGIS is preferable because the database performs candidate filtering efficiently.

## 7. Route-mile projection

For every candidate station:

- determine nearest point on route;
- compute normalized route fraction;
- convert fraction to cumulative route miles.

A candidate at route mile 425 is not automatically feasible just because it is geographically close. Feasibility depends on route-mile distance from the previous fuel event.

## 8. Optimization

Let:

- `R` = total route miles;
- `M` = max range = 500;
- `P_i` = price at station i;
- `x_i` = route mile position of station i;
- `d_i` = route miles from previous refuel point to station i.

Initial full tank means first refuel must occur no later than mile 500.

The final leg from the last refuel point to destination must be <= 500.

### Recommended deterministic dynamic programming

Discretize candidate stations by route position.

For each station candidate `j`, calculate the minimum fuel purchase cost required to reach it from each feasible predecessor `i`.

Because fuel price determines the amount to purchase, a more precise implementation can model fuel state.

For the assessment, a simpler and transparent strategy is acceptable if its purchase convention is explicitly documented.

Recommended practical strategy:

1. Build route-positioned candidate stations.
2. Add virtual nodes for start and destination.
3. Create directed edges between nodes if distance <= 500.
4. Assign station price to fuel purchased after arriving at that station.
5. Use dynamic programming / shortest path over route order.
6. Penalize station detour only as a secondary term.
7. Return the least-cost feasible sequence.

If modeling exact fuel inventory, the state becomes `(station_index, fuel_remaining)` and should use discretization or a continuous closed-form decision rule. Prefer the closed-form “buy enough to reach the next sufficiently cheaper station, otherwise fill enough to cover the remaining reachable distance” rule for a fixed MPG/500-mile tank.

## 9. Fuel purchase model

The cleanest assessment model is:

- start with a full tank;
- at each selected stop, buy enough fuel to reach the next planned stop/destination;
- if the next reachable station is cheaper, purchase only enough to reach it;
- otherwise fill to capacity;
- never exceed 500 miles of usable range.

This produces a realistic greedy solution and keeps cost tied to station prices.

However, the exact tank capacity is not supplied; range is supplied directly. Therefore implement the model in **miles of usable range** rather than gallons:

- capacity = 500 miles;
- consuming `d` miles reduces remaining range by `d`;
- purchasing `g` gallons restores `g * MPG` miles, capped at 500.

## 10. External providers

### Routing

Use an adapter:

```python
class RoutingProvider(Protocol):
    def route(self, start: Coordinate, finish: Coordinate) -> RouteResult: ...
```

Implementation:

`OSRMRoutingProvider`

Request:

`/route/v1/driving/{lon1},{lat1};{lon2},{lat2}`

Use:

- `overview=full`
- `geometries=geojson`
- `steps=false`
- `alternatives=false`

OSRM's route API is documented to return route geometry, distance and duration.

### Geocoding

Use:

```python
class GeocodingProvider(Protocol):
    def geocode(self, query: str) -> GeocodeResult: ...
```

Possible implementation:

`NominatimGeocoder`

But public Nominatim must be used only with deliberate compliance, caching, valid User-Agent, low request volume, and a switchable provider.

For one-time bulk U.S. fuel-station enrichment, evaluate Census Geocoder first. Its batch API supports up to 10,000 addresses, but the workbook's highway/intersection strings may not all geocode successfully.

## 11. Provider configuration

Environment variables:

```env
ROUTING_PROVIDER=osrm
OSRM_BASE_URL=https://router.project-osrm.org
GEOCODER_PROVIDER=nominatim
GEOCODER_BASE_URL=https://nominatim.openstreetmap.org
GEOCODER_USER_AGENT=fuel-route-assessment/1.0 contact@example.com
ROUTE_CACHE_TTL_SECONDS=86400
GEOCODE_CACHE_TTL_SECONDS=2592000
FUEL_ROUTE_CORRIDOR_MILES=15
```

Never make provider URLs user-controlled.

## 12. Performance

Do:

- cache geocoding;
- cache routes;
- precompute station coordinates;
- spatially index station points;
- use one route request;
- project stations locally;
- query only candidates near the route;
- serialize only needed fields.

Do not:

- route from start to every station;
- geocode every station during an API request;
- call an external map API from the frontend for every stop;
- perform O(N) full-dataset scans for every request if PostGIS can index it.

## 13. Error states

- invalid request;
- non-U.S. location;
- ambiguous geocode;
- geocoder unavailable;
- no route;
- routing provider timeout;
- no fuel stations near route;
- route segment exceeds 500 miles without a feasible station;
- malformed imported fuel price;
- missing station coordinates.

Each should return a stable error code and human-readable message.
