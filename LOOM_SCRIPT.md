# Loom Demo Script — 3 to 5 Minutes

## 0:00–0:30 — Problem

“This API takes two U.S. locations and plans a road route with cost-effective fuel stops. The vehicle can travel 500 miles and gets 10 MPG.”

## 0:30–1:00 — Architecture

Show:

```text
Django API
 -> Geocoder/cache
 -> OSRM route
 -> spatial fuel candidates
 -> optimizer
 -> cost calculator
```

Highlight:

“One routing call produces the route geometry. I do not route separately to every gas station.”

## 1:00–1:40 — Dataset

Show the workbook import/model.

Mention:
- station name;
- city/state;
- retail price;
- source ID.

Mention that Canadian region codes were explicitly filtered out.

## 1:40–2:30 — API demo

Run:

```bash
curl -X POST http://localhost:8000/api/v1/routes/plan/ \
  -H 'Content-Type: application/json' \
  -d '{"start":"Chicago, IL","finish":"Denver, CO"}'
```

Show:
- route distance;
- geometry;
- selected stations;
- prices;
- total gallons;
- total cost.

## 2:30–3:10 — Algorithm

Explain:

- station coordinates are projected onto route;
- route-mile positions are computed;
- 500-mile feasibility is enforced;
- cheaper reachable stations are preferred;
- no feasible plan is returned if a required gap cannot be covered.

## 3:10–3:40 — Tests

Show:

```bash
python manage.py test
```

Open the optimizer tests.

## 3:40–4:20 — Performance

Show request timing/logs.

Point out:

- one route request on cache miss;
- no per-station routing;
- cached geocoding;
- spatial candidate filtering.

## 4:20–5:00 — Engineering judgment

Mention limitations:

- workbook price snapshot;
- geocoding quality;
- no live traffic;
- route optimization is only as complete as geocoded station coverage.

Finish by showing GitHub README and repository structure.
