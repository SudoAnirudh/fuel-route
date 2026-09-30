# Product Requirements Document — Fuel Route Optimizer API

## 1. Executive summary

Build a fast REST API using the latest stable Django that plans a road trip between two U.S. locations and recommends cost-effective fuel stops using the supplied fuel-price dataset.

The API should solve a constrained route-planning problem:

- road route is determined by a routing provider;
- vehicle can travel at most 500 miles between refuels;
- fuel economy is fixed at 10 MPG;
- fuel stops must lie on/near the selected route;
- fuel price is the primary optimization signal;
- multiple stops are required when the route exceeds the vehicle's range;
- total estimated fuel spend must be returned.

The solution should be deliberately designed so that external routing is called once per uncached request.

## 2. Assessment goals

The implementation should demonstrate:

- Django engineering quality.
- API design.
- data ingestion.
- geospatial reasoning.
- algorithmic optimization.
- external API integration.
- caching.
- testability.
- performance awareness.
- production-minded error handling.

## 3. Users

Primary user: an assessment reviewer consuming the API.

Secondary user: a frontend/map client displaying the returned route and stops.

## 4. Core user story

> As a driver, I provide a U.S. origin and destination. I want the API to return a route and recommend fuel stations that let me complete the trip without exceeding the vehicle's 500-mile maximum range, while keeping fuel cost low.

## 5. Functional requirements

### FR-1: Route request

Endpoint:

`POST /api/v1/routes/plan/`

Request:

```json
{
  "start": "Chicago, IL",
  "finish": "Denver, CO"
}
```

Optional advanced request:

```json
{
  "start": "Chicago, IL",
  "finish": "Denver, CO",
  "vehicle": {
    "max_range_miles": 500,
    "mpg": 10
  }
}
```

For the assessment, defaults must remain 500 miles and 10 MPG.

### FR-2: U.S.-only validation

Reject inputs that cannot be confidently resolved to the United States.

Return HTTP 400 with a machine-readable error.

Do not infer that an arbitrary city name is U.S.-based.

### FR-3: Route retrieval

Resolve start/finish to coordinates, then call the routing provider.

Target: exactly one routing call for an uncached request.

Use route geometry in GeoJSON or another map-ready representation.

### FR-4: Fuel station dataset

Import the supplied workbook into a normalized database table.

At minimum store:

- source identifier
- station name
- address
- city
- state
- rack ID
- retail price
- latitude
- longitude
- geocode status
- source/version metadata

### FR-5: Fuel candidate filtering

Only consider stations:

1. in U.S. states/DC;
2. with valid coordinates;
3. within a configurable corridor around the selected route;
4. reachable in sequence from the vehicle's previous fuel point.

### FR-6: Range feasibility

No selected fuel-stop leg may exceed 500 route miles.

The start and finish are treated as route endpoints.

The algorithm must fail clearly if no feasible station exists in a required segment.

Do not silently claim a plan is feasible.

### FR-7: Cost model

Fuel required for a route segment:

`segment_miles / MPG`

Segment fuel cost:

`segment_miles / MPG * station_price`

Default MPG = 10.

The implementation should define whether the first fuel purchase occurs at the origin, at the first stop, or through an assumed full tank. Recommended assessment interpretation:

**Assume the vehicle starts with a full tank and therefore has 500 miles of usable range before the first refuel.**

The cost calculation then charges only fuel purchased at recommended stops, plus any final top-up required by the chosen plan if the algorithm's purchase model explicitly models it.

To avoid ambiguity, the final README must state the exact purchase convention.

### FR-8: Optimization objective

Primary objective:

- minimize estimated fuel purchase cost while maintaining feasibility.

Secondary objectives:

- minimize unnecessary detour;
- minimize number of stops;
- prefer lower-priced stations when alternatives have similar route position.

A deterministic lexicographic objective is recommended:

1. feasible route plan;
2. minimum estimated fuel cost;
3. minimum total station detour;
4. minimum number of stops;
5. stable station-ID tie-breaker.

### FR-9: Multiple stops

For long routes, return every selected stop in driving order.

Example:

```text
Start
  |
  | 380 mi
  v
Stop A
  |
  | 410 mi
  v
Stop B
  |
  | 290 mi
  v
Finish
```

### FR-10: Map-ready response

Return:

- route geometry;
- start coordinate;
- finish coordinate;
- station coordinates;
- station metadata;
- route order;
- route distance.

The frontend should not need to call the routing provider again.

### FR-11: Cost summary

Return:

- total route miles;
- MPG;
- total fuel consumed;
- estimated total fuel cost;
- number of fuel stops;
- selected stations.

## 6. Suggested response

```json
{
  "route": {
    "distance_miles": 1002.4,
    "duration_minutes": 902.2,
    "geometry": {
      "type": "LineString",
      "coordinates": []
    }
  },
  "vehicle": {
    "max_range_miles": 500,
    "mpg": 10
  },
  "fuel": {
    "total_gallons_consumed": 100.24,
    "estimated_total_cost_usd": 341.17
  },
  "stops": [
    {
      "sequence": 1,
      "station_id": 123,
      "name": "Example Station",
      "city": "Example",
      "state": "KS",
      "latitude": 0,
      "longitude": 0,
      "retail_price_usd_per_gallon": 3.11,
      "route_mile": 401.3,
      "detour_miles": 1.4,
      "estimated_gallons": 41.0,
      "estimated_cost_usd": 127.51
    }
  ],
  "meta": {
    "routing_provider": "osrm",
    "fuel_price_source": "assessment_workbook",
    "fuel_price_snapshot": "import timestamp/version",
    "routing_api_calls": 1,
    "geocoding_cache_hit": true
  }
}
```

Numbers above are illustrative schema examples, not expected real results.

## 7. Non-functional requirements

### Performance

Target for a warm-cache request:

- application logic should be fast enough that external I/O dominates;
- no per-station routing calls;
- no per-request bulk geocoding;
- route response should be cacheable;
- candidate selection should use indexed database queries.

Suggested engineering target:

- p50 < 1.5s warm cache;
- p95 < 3s under local assessment conditions.

These are engineering targets, not promises about a public routing provider.

### External call budget

For an uncached request:

- geocoding: up to 2 user-location lookups, ideally cached after first use;
- routing: 1 OSRM route call;
- no routing calls for individual fuel stations.

### Reliability

- external timeouts;
- bounded retries;
- circuit/failure response;
- stale cache policy;
- structured error messages.

### Security

- validate input length;
- avoid arbitrary URL fetching;
- allow-list outbound hosts;
- rate-limit the public endpoint;
- never expose provider credentials;
- set secure Django settings in production;
- do not log sensitive request data unnecessarily.

## 8. Out of scope

- live fuel prices;
- live traffic;
- vehicle-specific tank size;
- electric vehicle charging;
- toll optimization;
- multi-vehicle optimization;
- guaranteed real-world station availability;
- guaranteed real-world price accuracy after the workbook snapshot;
- turn-by-turn navigation.

## 9. Assumptions that must be documented

1. The workbook is a historical/snapshot price source.
2. Retail Price is treated as dollars per gallon.
3. Vehicle begins with a full 500-mile usable range.
4. MPG is fixed at 10 unless explicitly overridden.
5. The route returned by the routing provider is the route being optimized.
6. A station is considered route-compatible based on a configurable corridor/detour threshold.
7. Fuel station coordinates are derived during preprocessing, not at request time.
8. Geocoding is imperfect and must expose status/confidence where available.
9. Price optimization cannot guarantee the globally cheapest possible trip if candidate station coverage is incomplete.

## 10. Acceptance criteria

A reviewer can:

- import the workbook;
- start Django;
- submit a U.S.-to-U.S. request;
- receive route geometry;
- see multiple fuel stops for sufficiently long routes;
- verify no stop-to-stop leg exceeds 500 route miles;
- verify cost arithmetic;
- verify the API does not make one routing request per station;
- run tests;
- inspect architecture and algorithm documentation;
- understand all assumptions from the README.
