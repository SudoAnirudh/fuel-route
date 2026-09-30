# Fuel Stop Optimization Algorithm

## Objective

Find a feasible sequence of fuel stations along a fixed road route that minimizes estimated fuel cost.

Primary constraint:

`distance between fuel events <= 500 miles`

Fuel economy:

`10 MPG`

## Inputs

```text
route geometry
route distance
fuel stations:
  route_position_miles
  detour_miles
  price_usd_per_gallon
vehicle:
  max_range_miles = 500
  mpg = 10
```

## Step 1 — Position stations on route

For every station in the route corridor:

```text
station -> nearest point on route -> route_position_miles
```

Reject stations whose detour exceeds the configured threshold.

Sort candidates by `route_position_miles`.

## Step 2 — Add virtual endpoints

```text
START: position = 0
DESTINATION: position = route_distance
```

START begins with 500 miles of usable range.

## Step 3 — Feasibility graph

Create an edge `i -> j` when:

```text
position[j] - position[i] <= 500
```

For station-to-station edges, this means the vehicle can physically reach the next station if it has enough fuel/range.

For start-to-station:

```text
position[j] <= 500
```

For station-to-destination:

```text
route_distance - position[i] <= 500
```

## Step 4 — Cost model

Fuel consumption:

```text
gallons = miles / mpg
```

Cost:

```text
cost = gallons * price
```

Because the exact tank capacity in gallons is not provided, use 500 miles as the capacity state.

At a station:

```text
remaining_range = remaining_range - miles_since_last_event
purchase_miles = min(
    500 - remaining_range,
    miles_needed_to_target
)
purchase_gallons = purchase_miles / mpg
purchase_cost = purchase_gallons * station_price
```

## Step 5 — Greedy fuel policy

At station `i`:

1. Find the next station ahead with a strictly lower price that is reachable within 500 miles.
2. If one exists, buy only enough range to reach that cheaper station.
3. Otherwise buy enough to maximize useful range subject to the remaining trip.
4. Never buy beyond the 500-mile range capacity.

This is the classic “next cheaper station” fuel strategy adapted to route-positioned stations.

## Step 6 — Why this is appropriate

The assessment's primary objective is cost effectiveness, not arbitrary station selection.

A cheaper station ahead should be favored when reachable.

If no cheaper station is reachable, buying more at the current station avoids being forced to buy at an even more expensive future station.

## Step 7 — Stop selection

A station is returned only when the plan actually purchases fuel there.

Do not return every candidate station.

## Step 8 — Tie breakers

When prices are equal:

1. lower detour;
2. earlier route position if needed for deterministic output;
3. stable source ID.

## Step 9 — Failure handling

If:

```text
no station can be reached before remaining_range <= 0
```

return:

```json
{
  "error": {
    "code": "NO_FEASIBLE_FUEL_PLAN",
    "message": "No fuel station in the configured route corridor can satisfy the 500-mile range constraint."
  }
}
```

Do not invent a station or silently exceed the vehicle range.

## Algorithm tests

Minimum test cases:

1. destination < 500 miles: zero stops;
2. exactly 500 miles: zero stops if full tank reaches destination;
3. 501 miles: at least one refuel;
4. cheap station immediately before an expensive station;
5. cheaper reachable station 300 miles ahead;
6. no station within 500 miles;
7. multiple stops;
8. equal-price stations;
9. detour tie-break;
10. destination exactly 500 miles after final stop;
11. route with no candidate stations;
12. duplicate stations from imported data.

## Numerical precision

Use `Decimal` for monetary calculations.

Never use binary floating-point directly for final USD arithmetic.

Store price as `Decimal` with sufficient scale, then round presentation to cents.

Distance calculations may use float internally but final response should use a sensible precision.
