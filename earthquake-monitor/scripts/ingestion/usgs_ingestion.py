#!/usr/bin/env python3
"""
USGS Earthquake Data Ingestion Script

This script fetches earthquake data from the USGS API and ingests it into the system.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

from src.application.use_cases.create_earthquake import (
    CreateEarthquakeRequest,
    CreateEarthquakeUseCase,
)
from src.presentation.dependencies import get_earthquake_repository


class USGSClient:
    """Client for fetching earthquake data from USGS API."""

    def __init__(self, base_url: str = "https://earthquake.usgs.gov/fdsnws/event/1"):
        self.base_url = base_url

    async def fetch_earthquakes(
        self,
        start_time: datetime,
        end_time: datetime,
        min_magnitude: float = 2.5,
    ) -> List[Dict[str, Any]]:
        """Fetch earthquakes from USGS API."""
        params = {
            "format": "geojson",
            "starttime": start_time.isoformat(),
            "endtime": end_time.isoformat(),
            "minmagnitude": min_magnitude,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/query", params=params)
            response.raise_for_status()
            data = response.json()

        return data.get("features", [])


class EarthquakeIngestionService:
    """Service for ingesting earthquake data."""

    def __init__(self, use_case: CreateEarthquakeUseCase):
        self.use_case = use_case

    async def ingest_earthquakes(
        self, earthquakes_data: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Ingest earthquake data into the system."""
        created = 0
        errors = 0

        for feature in earthquakes_data:
            try:
                properties = feature["properties"]
                geometry = feature["geometry"]
                coordinates = geometry["coordinates"]

                request = CreateEarthquakeRequest(
                    latitude=coordinates[1],
                    longitude=coordinates[0],
                    depth=coordinates[2],
                    magnitude_value=properties["mag"],
                    magnitude_scale=properties.get("magType", "unknown"),
                    occurred_at=datetime.fromtimestamp(properties["time"] / 1000),
                    source="USGS",
                )

                await self.use_case.execute(request)
                created += 1

            except Exception as e:
                print(f"Error ingesting earthquake: {e}")
                errors += 1

        return {"created": created, "errors": errors}


async def main():
    """Main ingestion function."""
    print("Starting USGS earthquake data ingestion...")

    # Initialize services
    repository = get_earthquake_repository()
    use_case = CreateEarthquakeUseCase(repository)
    usgs_client = USGSClient()
    ingestion_service = EarthquakeIngestionService(use_case)

    # Fetch data from last 24 hours
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

    print(f"Fetching earthquakes from {start_time} to {end_time}")

    try:
        earthquakes_data = await usgs_client.fetch_earthquakes(
            start_time=start_time,
            end_time=end_time,
            min_magnitude=2.5,
        )

        print(f"Found {len(earthquakes_data)} earthquakes to process")

        result = await ingestion_service.ingest_earthquakes(earthquakes_data)

        print(f"Ingestion completed: {result}")

    except Exception as e:
        print(f"Ingestion failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
