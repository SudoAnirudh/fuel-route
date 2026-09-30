# Fuel Route Optimizer — Production Django REST API

A production-minded Django REST API that calculates cost-effective fuel stops along U.S. driving routes. It accepts a U.S. start and finish location and returns:

1. Map-ready GeoJSON route geometry.
2. Ordered cost-effective fuel stops.
3. Total fuel consumed (at 10 MPG default) and total estimated fuel cost (using `Decimal` arithmetic).
4. Detailed per-stop breakdown including location, fuel price, route-mile position, detour estimate, gallons purchased, and stop cost.
5. Strict enforcement of vehicle max range constraint (default **500 miles** per leg).
6. Routing efficiency: **Target exactly 1 external routing call** per uncached route request.

---

## 🚀 Quickstart (Clean Clone Setup)

Follow these exact commands to setup and run the project locally:

```bash
# 1. Clone repository and navigate to folder
git clone https://github.com/example/fuel-route-optimizer.git
cd fuel-route-assessment-package

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env

# 5. Run database migrations
python manage.py migrate

# 6. Ingest workbook dataset and preprocessed geocoding fixture
python manage.py import_fuel_prices

# 7. Run test suite
pytest

# 8. Start local Django development server
python manage.py runserver
```

---

## 📡 API Endpoint Usage

### Route Planning Endpoint

`POST /api/v1/routes/plan/`

#### Sample Request

```bash
curl -X POST http://127.0.0.1:8000/api/v1/routes/plan/ \
  -H "Content-Type: application/json" \
  -d '{
        "start": "Chicago, IL",
        "finish": "Denver, CO"
      }'
```

#### Sample Response (HTTP 200 OK)

```json
{
  "start": {
    "query": "Chicago, IL",
    "display_name": "Chicago, Cook County, Illinois, United States",
    "latitude": 41.8781,
    "longitude": -87.6298
  },
  "finish": {
    "query": "Denver, CO",
    "display_name": "Denver, City and County of Denver, Colorado, United States",
    "latitude": 39.7392,
    "longitude": -104.9903
  },
  "route_distance_miles": 1005.1,
  "route_duration_seconds": 64095.5,
  "route_geometry": {
    "type": "LineString",
    "coordinates": [
      [-87.6298, 41.8781],
      [-95.9345, 41.2565],
      [-104.9903, 39.7392]
    ]
  },
  "vehicle_assumptions": {
    "max_range_miles": 500.0,
    "fuel_economy_mpg": 10.0
  },
  "total_gallons_consumed": 100.51,
  "total_fuel_cost": "148.07",
  "fuel_stops_count": 2,
  "fuel_stops": [
    {
      "station_id": 796,
      "name": "QUIKTRIP #598",
      "address": "I-80, EXIT 440",
      "city": "Omaha",
      "state": "NE",
      "latitude": 41.2565,
      "longitude": -95.9345,
      "retail_price": "2.9273",
      "route_mile": 465.5,
      "detour_miles": 0.2,
      "gallons_purchased": 46.55,
      "cost": "136.27"
    },
    {
      "station_id": 1420,
      "name": "FATDOGS LEXINGTON",
      "address": "I-80, EXIT 237",
      "city": "Lexington",
      "state": "NE",
      "latitude": 40.7808,
      "longitude": -99.7415,
      "retail_price": "2.9790",
      "route_mile": 682.9,
      "detour_miles": 0.4,
      "gallons_purchased": 3.96,
      "cost": "11.80"
    }
  ],
  "metadata": {
    "routing_provider": "OSRM",
    "external_routing_calls": 1,
    "candidate_stations_evaluated": 145,
    "optimizer_time_ms": 12.4,
    "total_request_time_ms": 145.2
  }
}
```

### Health Check Endpoint

`GET /healthz`

```json
{
  "status": "ok",
  "database": "healthy"
}
```

---

## 🏗️ Architecture & Data Flow

```text
User Request ("Chicago, IL" -> "Denver, CO")
                  │
                  ▼
         POST /api/v1/routes/plan/
                  │
                  ▼
         PlannerService Orchestrator
         ├── 1. Geocoder (Nominatim + Cache) -> Resolves & validates U.S. coordinates
         ├── 2. RoutingProvider (OSRM + RouteCache) -> Target 1 external routing call
         ├── 3. Spatial Bounding Box Filter -> Query FuelStation records
         ├── 4. FuelOptimizer -> Polyline projection & Greedy "next cheaper station" algorithm
         └── 5. CostCalculator -> Decimal arithmetic for USD currency precision
                  │
                  ▼
         HTTP 200 JSON Response
```

---

## 🧮 Optimization Algorithm Summary

The fuel stop optimizer (`FuelOptimizer`) operates on the polyline geometry returned by OSRM:

1. **Projection**: Fuel stations are projected onto the route geometry to compute `route_mile` (cumulative mile along route) and `detour_miles` (round-trip detour from route polyline).
2. **Corridor Filtering**: Stations exceeding a 15-mile detour threshold are excluded.
3. **Vehicle Tank State**: Vehicle starts with a FULL tank (500 miles range). Per assessment recommendation, initial fuel is uncharged; only additional purchases are charged.
4. **Next-Cheaper-Station Policy**:
   - At current position, look ahead in the reachable range window (`(current_mile, current_mile + 500)`).
   - If a cheaper station exists ahead, drive to it and purchase only enough fuel to reach that cheaper station.
   - If no cheaper station exists ahead, purchase enough fuel to fill the tank (or complete the trip).
5. **Leg Enforcement**: Guaranteed `travel_segment <= 500.0 miles`. If a gap exceeds 500 miles, returns structured HTTP 422 `NO_FEASIBLE_FUEL_PLAN` error.

---

## 🧪 Running Tests

Run the complete test suite:

```bash
# Using pytest (Recommended)
pytest

# Or using Django test runner
python manage.py test fuel_routes.tests
```

### Verified Test Cases (19/19 Passing)

- ✅ **API Validation**: missing fields, invalid JSON, non-U.S. locations rejected (HTTP 400).
- ✅ **U.S. Only Validation**: Canadian start/finish inputs (e.g. Toronto, ON) rejected.
- ✅ **Routing Adapter**: OSRM response parsing, distance conversion, and fallback polyline generator.
- ✅ **Route Caching**: Uncached route = 1 external call; cached route = 0 external calls.
- ✅ **Optimizer <500 miles**: 0 stops returned, $0 cost.
- ✅ **Optimizer 500 miles**: 0 stops returned, $0 cost.
- ✅ **Optimizer >500 miles**: Multiple fuel stops selected, all legs <= 500 miles.
- ✅ **No Feasible Plan**: Gap > 500 miles raises `NoFeasiblePlanException` (HTTP 422).
- ✅ **Cheaper Station Ahead**: Prefers lower-cost station over immediate expensive station.
- ✅ **Equal Prices Tie-break**: Prefers lower detour distance.
- ✅ **Decimal Arithmetic**: Exact currency math without binary float rounding issues.
- ✅ **Dataset Import**: Ingests all 8,151 rows (7,531 U.S. stations, 620 non-U.S. excluded).

---

## 📊 Performance & Optimization

- **Runtime External Routing Calls**: Exactly **1 call** per uncached route request. Never makes per-station routing calls.
- **Geocoding**: Station locations preprocessed offline into `data/fuel_stations_geocoded.json`. Runtime user geocoding cached in `GeocodeCache`.
- **Database Indexing**: Composite spatial/cost indexes on `(state, retail_price)` and `(latitude, longitude)`.

---

## ⚠️ Data Limitations & Disclaimer

- **Live Traffic/Prices**: Fuel prices are static values sourced from `fuel-prices-for-be-assessment.xlsx`.
- **Address Geocoding**: Stations are mapped using city/interstate corridor coordinates. Canadian provinces (`AB`, `BC`, `MB`, `NB`, `NS`, `ON`, `QC`, `SK`, `YT`) are marked `EXCLUDED_NON_US` and excluded from route planning.
- **Station Availability**: Live fuel station operational status or tank availability is not guaranteed.

---

## 📜 Provider Attribution

- **Routing**: [OSRM (Open Source Routing Machine)](https://project-osrm.org/)
- **Geocoding**: [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/)
