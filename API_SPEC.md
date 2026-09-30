# API Specification

## POST /api/v1/routes/plan/

### Request

```json
{
  "start": "Austin, TX",
  "finish": "Phoenix, AZ"
}
```

Optional:

```json
{
  "start": "Austin, TX",
  "finish": "Phoenix, AZ",
  "vehicle": {
    "max_range_miles": 500,
    "mpg": 10
  }
}
```

For the assessment, reject unsafe/unsupported overrides or restrict them to documented bounds.

## 200 response

```json
{
  "route": {
    "distance_miles": 0,
    "duration_minutes": 0,
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
    "total_gallons_consumed": 0,
    "estimated_total_cost_usd": "0.00"
  },
  "stops": [],
  "meta": {
    "routing_provider": "osrm",
    "routing_api_calls": 1,
    "fuel_price_source": "assessment_workbook",
    "cache": {
      "route": "miss",
      "geocoding": {
        "start": "hit",
        "finish": "hit"
      }
    }
  }
}
```

## Error response

```json
{
  "error": {
    "code": "INVALID_LOCATION",
    "message": "The start location could not be resolved to a U.S. location."
  }
}
```

Suggested HTTP status mapping:

| Condition | HTTP |
|---|---:|
| invalid JSON | 400 |
| validation error | 400 |
| non-U.S. location | 400 |
| ambiguous location | 400 |
| no route | 422 |
| no feasible fuel plan | 422 |
| provider timeout | 503 |
| provider rate limited | 503 |
| unexpected server error | 500 |

## Station object

```json
{
  "sequence": 1,
  "station_id": 123,
  "name": "STATION NAME",
  "address": "ADDRESS",
  "city": "CITY",
  "state": "TX",
  "latitude": 0.0,
  "longitude": 0.0,
  "retail_price_usd_per_gallon": "3.25",
  "route_mile": 345.2,
  "detour_miles": 2.1,
  "estimated_gallons": "34.52",
  "estimated_cost_usd": "112.19"
}
```

## Health endpoint

`GET /healthz`

Response:

```json
{
  "status": "ok"
}
```

Keep this endpoint independent of the external routing provider.

## OpenAPI

Generate OpenAPI schema using DRF Spectacular or an equivalent maintained package.

The README should expose the interactive schema endpoint in development.
