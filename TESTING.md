# Testing & Quality Strategy

## Unit tests

### Money

- Decimal multiplication.
- rounding to cents.
- zero/negative price rejection.

### Distance

- route projection.
- cumulative route distance.
- station ordering.
- corridor threshold.

### Optimizer

Test fixtures should be deterministic and tiny.

Example:

```text
Route = 1,200 miles
Range = 500
MPG = 10

Station A: mile 420, $3.80
Station B: mile 700, $3.10
Station C: mile 960, $3.70
```

Expected behavior should be asserted from the documented fuel policy rather than hard-coded to an unexplained station sequence.

## API tests

- missing start;
- missing finish;
- empty strings;
- excessively long strings;
- malformed JSON;
- non-U.S. geocode;
- ambiguous geocode;
- no route;
- no feasible fuel plan;
- provider timeout;
- success;
- long route with multiple stops.

## Contract tests

Mock OSRM and assert:

- exactly one route request;
- correct coordinate ordering;
- required query parameters;
- provider response validation.

## Performance tests

Record:

```text
routing_call_count
geocoding_call_count
candidate_count
optimizer_ms
total_ms
```

A regression test should ensure no implementation accidentally introduces per-station route requests.

## Property tests

If Hypothesis is used:

- no selected leg > max range;
- selected stations are ordered;
- total route miles >= 0;
- total gallons ~= route miles / MPG;
- total cost >= 0;
- selected station prices come from the imported dataset.

## Data tests

After import:

- no null required fields;
- price > 0;
- coordinates valid when geocode status is success;
- U.S.-only state filter;
- source IDs preserved;
- duplicate handling documented.

## External services

Never make unit tests depend on public OSRM/Nominatim/Census uptime.

Use mocks/VCR-style recorded fixtures if appropriate.

Integration tests may be opt-in with an environment flag.
