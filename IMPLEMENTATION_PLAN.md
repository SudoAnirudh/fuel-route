# 3-Day Implementation Plan

## Day 1 — Foundation + data

### Block 1: repository setup

- initialize Git;
- create Django project;
- configure settings;
- install DRF;
- configure PostgreSQL/PostGIS;
- add `.env.example`;
- add formatting/linting/test tooling;
- add pre-commit if time allows.

### Block 2: workbook ingestion

- inspect workbook programmatically;
- create normalized `FuelStation` model;
- build `import_fuel_prices` command;
- filter to U.S. states + DC;
- normalize prices;
- preserve source IDs;
- deduplicate only when the identity rule is explicit.

### Block 3: geospatial enrichment design

- create geocoder adapter;
- create cached geocoding model;
- create a preprocessing command;
- never geocode all stations during an API request.

Because the supplied addresses include highway/exit descriptions, measure geocoder match rate. Store failed/tied matches explicitly.

### Block 4: routing adapter

- implement OSRM adapter;
- request GeoJSON geometry;
- implement timeout;
- validate provider response;
- write mocked adapter tests.

### End-of-day checkpoint

Must have:

- migrations;
- imported fuel dataset;
- provider interfaces;
- route response fixture;
- basic health endpoint.

---

## Day 2 — Algorithm + API

### Block 1: geometry

Implement:

- route decoding;
- route-distance indexing;
- station-to-route projection;
- corridor filtering;
- detour calculation.

### Block 2: optimizer

Implement:

- 500-mile range;
- 10 MPG;
- full initial range;
- next-cheaper-station policy;
- cost accounting;
- deterministic tie breakers;
- no-feasible-plan error.

### Block 3: API

Implement:

`POST /api/v1/routes/plan/`

Add:

- serializers;
- service orchestration;
- error mapping;
- response schema.

### Block 4: caching

Cache:

- geocoding;
- route result;
- optionally final plan.

Cache keys must include normalized coordinates and relevant vehicle/config parameters.

### End-of-day checkpoint

A complete end-to-end request should work locally using mocked providers and, if external services are available, with the real OSRM endpoint.

---

## Day 3 — Hardening + presentation

### Block 1: tests

Add:

- optimizer unit tests;
- cost tests;
- API validation tests;
- provider tests;
- integration tests;
- regression fixture.

### Block 2: performance

Measure:

- cold request;
- warm request;
- database candidate query;
- optimization time;
- serialization time;
- external provider latency.

Record routing API call count.

### Block 3: docs

Finalize:

- README;
- architecture;
- API examples;
- assumptions;
- limitations;
- provider attribution;
- setup;
- test commands.

### Block 4: demo

Prepare a 3–5 minute Loom:

1. show architecture;
2. show imported data;
3. make an API request;
4. show route map-ready geometry;
5. show multiple fuel stops on a long route;
6. explain cost calculation;
7. show tests;
8. show external-call optimization;
9. show GitHub repository.

## Final submission checklist

- [ ] GitHub repository is accessible.
- [ ] README works from a clean clone.
- [ ] `.env.example` exists.
- [ ] No secrets committed.
- [ ] Workbook ingestion is documented.
- [ ] API endpoint works.
- [ ] Tests pass.
- [ ] Route geometry is returned.
- [ ] Multiple stops work.
- [ ] 500-mile constraint is enforced.
- [ ] 10 MPG calculation is correct.
- [ ] Total cost uses Decimal.
- [ ] External routing calls are minimized.
- [ ] Limitations are documented.
- [ ] Loom link is ready.
