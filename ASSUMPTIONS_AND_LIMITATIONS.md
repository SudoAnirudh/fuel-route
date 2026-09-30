# Assumptions, Trade-offs & Limitations

## 1. Fuel price freshness

The supplied workbook is the authoritative assessment dataset.

The API does not claim live fuel prices.

## 2. Initial fuel

Recommended implementation assumption:

The vehicle starts with a full usable range of 500 miles.

Therefore the first 500 miles require no purchase.

## 3. Tank capacity

The assessment specifies maximum range and MPG, not gallons of tank capacity.

The implementation models capacity in miles:

`500 miles / 10 MPG = 50 gallons equivalent`

This is an implied capacity for modeling, not a claim about a real vehicle.

## 4. Route

The selected routing provider determines the road route.

The fuel optimizer does not invent a different road path.

## 5. Station location

The workbook has no coordinates.

Station coordinates therefore require preprocessing/geocoding.

Geocoding failures are expected and must be visible.

## 6. Global optimality

If station coverage is incomplete because some records cannot be geocoded, the optimizer cannot guarantee global cheapest fuel cost.

It can guarantee the best plan under the candidate set and documented objective.

## 7. Detours

A station may be near the route geometrically but require a road detour.

The assessment primarily asks for cost-effective stations. A configurable detour corridor is used as a practical approximation.

A production version could validate each selected detour through a routing matrix provider.

## 8. Traffic

No live traffic optimization is promised.

## 9. Station availability

No live station-open/closed or inventory information is available.

## 10. Provider dependency

Public free routing/geocoding services can have rate limits, outages, or policy changes.

Adapters and caching are used to minimize coupling.

## 11. Why not query every station through routing?

That would be slow and violate the external-call objective.

The route geometry is used as the common coordinate system for station selection.

## 12. Why not geocode at request time?

Because thousands of fuel records cannot be safely geocoded on every API request.

Geocoding is a data-preparation concern.

## 13. What the API guarantees

Within the documented candidate data and model:

- route geometry comes from the routing provider;
- selected stops are ordered;
- selected travel segments do not exceed 500 miles;
- money arithmetic is deterministic;
- response contains enough information for a map client.
