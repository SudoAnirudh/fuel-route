import json
import os
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from fuel_routes.models import FuelStation

CA_PROVINCES = {'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'}


class Command(BaseCommand):
    help = 'Import fuel stations from Excel workbook and geocoded fixture dataset.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='./data/fuel_stations_geocoded.json',
            help='Path to the geocoded json file or Excel workbook dataset'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing FuelStation records before import'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear']

        if not os.path.exists(file_path):
            # Fallback check for relative paths
            if os.path.exists('./data/fuel_stations_geocoded.json'):
                file_path = './data/fuel_stations_geocoded.json'
            else:
                raise CommandError(f"Dataset file not found at {file_path}")

        self.stdout.write(self.style.NOTICE(f"Starting import from {file_path}..."))

        if clear_existing:
            deleted_count, _ = FuelStation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_count} existing FuelStation records."))

        with open(file_path, 'r', encoding='utf-8') as f:
            records = json.load(f)

        total_records = len(records)
        us_count = 0
        excluded_count = 0
        stations_to_create = []

        for r in records:
            state = str(r.get('state', '')).strip().upper()
            price = Decimal(str(r.get('retail_price', '0.0')))
            
            if state in CA_PROVINCES:
                status = 'EXCLUDED_NON_US'
                excluded_count += 1
                lat, lon = None, None
            else:
                status = r.get('geocode_status', 'SUCCESS')
                us_count += 1
                lat = Decimal(str(r['latitude'])) if r.get('latitude') is not None else None
                lon = Decimal(str(r['longitude'])) if r.get('longitude') is not None else None

            station = FuelStation(
                source_id=r['source_id'],
                name=r.get('name', ''),
                address=r.get('address', ''),
                city=r.get('city', ''),
                state=state,
                rack_id=r.get('rack_id', 0),
                retail_price=price,
                latitude=lat,
                longitude=lon,
                geocode_status=status,
                geocode_provider=r.get('geocode_provider', 'geocoded_fixture_v1'),
                geocode_confidence=r.get('geocode_confidence', 1.0),
                dataset_version=r.get('dataset_version', 'v1.0')
            )
            stations_to_create.append(station)

        with transaction.atomic():
            # Bulk create in batches of 1000
            FuelStation.objects.bulk_create(stations_to_create, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully imported {total_records} records:\n"
            f"  - Valid U.S. stations: {us_count}\n"
            f"  - Excluded Non-U.S. stations: {excluded_count}\n"
            f"  - Database records stored: {FuelStation.objects.count()}"
        ))
