# Fuel Price Data Pipeline

## Source

`fuel-prices-for-be-assessment.xlsx`

Sheet:

`Sheet1`

## Verified columns

```text
OPIS Truckstop ID
Truckstop Name
Address
City
State
Rack ID
Retail Price
```

## Import requirements

The import command should:

1. read the workbook;
2. validate required columns;
3. validate data types;
4. normalize state codes;
5. filter to U.S. states + DC;
6. normalize retail price to Decimal;
7. preserve source identifiers;
8. report duplicate counts;
9. report rejected rows;
10. write a dataset version/import timestamp.

## U.S. state allow-list

Use an explicit allow-list:

```text
AL AR AZ CA CO CT DE FL GA IA ID IL IN KS KY LA MA MD ME MI MN
MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT
VA VT WA WI WV WY
DC
```

Do not include Canadian province codes from the workbook.

If Puerto Rico or U.S. territories are intentionally supported, add them explicitly and document that decision.

## Geocoding

The workbook does not contain latitude/longitude.

The addresses frequently look like:

```text
I-44, EXIT 283 & US-69
```

rather than:

```text
123 Main Street
```

Therefore, geocoding quality must be treated as a data-quality concern.

Recommended fields:

```text
geocode_status:
  pending
  matched
  ambiguous
  failed

geocode_provider
geocode_confidence
matched_address
latitude
longitude
```

Do not silently substitute a city centroid for a failed station geocode unless the product explicitly labels it as approximate. For a fuel-stop optimizer, approximate coordinates can materially change route compatibility.

## One-time enrichment

Prefer a dedicated management command:

```bash
python manage.py geocode_fuel_stops
```

The command should support:

- `--limit`
- `--state`
- `--retry-failed`
- `--provider`
- `--dry-run`

Persist results.

Runtime API requests must never start an 8,000-row geocoding job.

## Reproducibility

Record:

- input filename/hash;
- import timestamp;
- provider;
- geocoder benchmark/version where applicable;
- count matched;
- count ambiguous;
- count failed.

This makes the assessment result reproducible.
