# AGENTS.md — Fuel Route Optimizer

## Mission

Implement a production-minded Django REST API for the fuel-route assessment.

The output must be deterministic, testable, explainable, and honest about data limitations.

## Non-negotiable requirements

1. Use the latest stable Django release available when implementation begins.
2. Use the supplied fuel-price workbook as the source dataset.
3. Do not invent fuel stations, prices, coordinates, API responses, or routing results.
4. Start and finish must resolve to U.S. locations.
5. Vehicle maximum range defaults to 500 miles.
6. Fuel economy defaults to 10 MPG.
7. Support multiple fuel stops.
8. Return map-ready route geometry.
9. Return total fuel consumed and estimated fuel cost.
10. Minimize external routing calls. One route call per uncached plan is the target.
11. Never route separately to every fuel station.
12. Never geocode all fuel stations during an API request.
13. Use Decimal for money.
14. Write tests before/alongside algorithm changes.
15. Document assumptions.
16. Never commit secrets.

## Source-of-truth rule

Before coding:

- inspect the workbook;
- verify its sheet and columns;
- verify U.S./Canadian state codes;
- verify price field type;
- verify whether coordinates exist.

If implementation assumptions conflict with the workbook, stop and adapt the implementation.

## Provider rule

External providers must be hidden behind interfaces.

Example:

```python
class RoutingProvider(Protocol):
    def route(...): ...
```

This allows OSRM to be replaced without rewriting the domain logic.

## Routing rule

The route provider is responsible for road geometry.

The optimizer is responsible for fuel stations.

Do not ask the routing provider to solve the entire fuel optimization problem.

## Geospatial rule

Fuel stations should be positioned along the route using local geometry.

Use PostGIS where available.

If a station cannot be reliably geocoded, mark it unavailable for route optimization rather than fabricating a location.

## Algorithm rule

The optimizer must make its assumptions explicit.

It must guarantee:

```text
every selected travel segment <= 500 miles
```

If no feasible station exists, return a structured error.

## API rule

Keep views thin.

Preferred flow:

```text
View
  -> Serializer
  -> PlannerService
      -> Geocoder
      -> RoutingProvider
      -> CandidateRepository
      -> FuelOptimizer
      -> CostCalculator
  -> Serializer
```

## Performance rule

Avoid:

- N+1 database queries;
- per-station external routing;
- per-request bulk geocoding;
- repeated route decoding;
- scanning all stations if spatial indexing is available.

## Testing rule

Every bug found in the optimizer gets a regression test.

Minimum tests:

- <500 mile trip;
- 500 mile trip;
- >500 mile trip;
- multiple stops;
- no feasible station;
- cheaper station ahead;
- expensive station ahead;
- equal prices;
- detour tie;
- Decimal cost;
- provider timeout;
- cached route;
- exactly one route API call.

## Documentation rule

Update README when:

- environment variables change;
- commands change;
- API response changes;
- assumptions change;
- provider changes.

## Git rule

Prefer small commits:

```text
chore: bootstrap django project
feat: add fuel price ingestion
feat: add geocoding abstraction
feat: add osrm routing adapter
feat: implement route geometry indexing
feat: implement fuel optimizer
feat: expose route planning endpoint
test: add optimizer regression suite
docs: add assessment setup and architecture
```

## Completion gate

Before declaring the task complete:

```bash
python manage.py check
python manage.py test
```

Run formatter/linter if configured.

Verify:

- clean clone setup;
- workbook import;
- endpoint;
- sample request;
- response schema;
- no secrets;
- README commands.
