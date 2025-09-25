"""USGS earthquake data ingestion service - extracted from monolith."""

import json
import logging
import os
from datetime import UTC, datetime
from typing import List

import httpx
from prometheus_client import Counter, Gauge, Histogram

from ..domain.disaster_event import (
    DisasterType,
    EarthquakeMagnitude,
    Location,
    ProcessedDisasterEvent,
    RawDisasterData,
)

logger = logging.getLogger(__name__)

# Prometheus metrics
usgs_api_requests_total = Counter(
    'usgs_api_requests_total',
    'Total requests to USGS API',
    ['endpoint', 'status']
)

usgs_api_request_duration = Histogram(
    'usgs_api_request_duration_seconds',
    'USGS API request duration',
    ['endpoint']
)

usgs_earthquakes_fetched = Gauge(
    'usgs_earthquakes_fetched_total',
    'Number of earthquakes fetched from USGS',
    ['magnitude_filter', 'period']
)

usgs_parse_errors = Counter(
    'usgs_parse_errors_total',
    'Number of parsing errors from USGS data'
)


class USGSIngestionService:
    """Service for fetching earthquake data from USGS GeoJSON feeds."""

    def __init__(self):
        self.base_url = os.getenv(
            "USGS_GEOJSON_BASE_URL",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary",
        )
        timeout = float(os.getenv("USGS_API_TIMEOUT", "30"))
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_raw_earthquake_data(
        self, period: str = "day", magnitude: str = "all"
    ) -> List[RawDisasterData]:
        """
        Fetch raw earthquake data from USGS.

        Args:
            period: Time period ('hour', 'day', 'week', 'month')
            magnitude: Magnitude filter ('all', 'significant', '4.5', '2.5', '1.0')

        Returns:
            List of RawDisasterData objects
        """
        url = f"{self.base_url}/{magnitude}_{period}.geojson"

        with usgs_api_request_duration.labels(endpoint=url).time():
            try:
                logger.info(f"Fetching earthquakes from USGS: {url}")
                response = await self.client.get(url)
                response.raise_for_status()

                usgs_api_requests_total.labels(
                    endpoint=url, status=response.status_code
                ).inc()

                data = response.json()
                features = data.get("features", [])

                raw_data_list = []
                for feature in features:
                    try:
                        # Extract USGS earthquake ID
                        external_id = feature.get("id")
                        if not external_id:
                            continue

                        raw_data = RawDisasterData(
                            disaster_type=DisasterType.EARTHQUAKE,
                            external_id=external_id,
                            source="USGS",
                            raw_payload=feature
                        )
                        raw_data_list.append(raw_data)

                    except Exception as e:
                        usgs_parse_errors.inc()
                        logger.warning(f"Failed to create raw data from feature: {e}")
                        continue

                usgs_earthquakes_fetched.labels(
                    magnitude_filter=magnitude, period=period
                ).set(len(raw_data_list))

                logger.info(f"Successfully fetched {len(raw_data_list)} earthquakes from USGS")
                return raw_data_list

            except httpx.HTTPError as e:
                usgs_api_requests_total.labels(
                    endpoint=url, status=getattr(e.response, 'status_code', 'unknown')
                ).inc()
                logger.error(f"HTTP error fetching USGS data: {e}")
                raise
            except Exception as e:
                usgs_api_requests_total.labels(endpoint=url, status='error').inc()
                logger.error(f"Error fetching USGS data: {e}")
                raise

    def process_earthquake_feature(self, raw_data: RawDisasterData) -> ProcessedDisasterEvent | None:
        """Process a raw USGS feature into a ProcessedDisasterEvent."""
        try:
            feature = raw_data.raw_payload
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            if len(coordinates) < 3:
                logger.warning("Invalid coordinates in earthquake feature")
                return None

            # Extract basic data
            longitude, latitude, depth = coordinates[0], coordinates[1], coordinates[2]
            magnitude_value = properties.get("mag")
            occurred_at_timestamp = properties.get("time")

            if magnitude_value is None or occurred_at_timestamp is None:
                logger.warning("Missing required earthquake data")
                return None

            # Validate and clean data
            if magnitude_value < 0:
                logger.warning(f"Invalid negative magnitude: {magnitude_value}, skipping")
                return None

            if depth is not None and depth < 0:
                logger.warning(f"Invalid negative depth: {depth}, setting to 0")
                depth = 0.0

            # Convert timestamp to datetime
            occurred_at = datetime.fromtimestamp(
                occurred_at_timestamp / 1000, UTC  # USGS uses milliseconds
            )

            # Create domain entities
            location = Location(
                latitude=float(latitude),
                longitude=float(longitude),
                depth=float(depth) if depth is not None else 0.0,
            )

            magnitude = EarthquakeMagnitude(
                value=float(magnitude_value),
                scale="MOMENT"  # USGS typically uses moment magnitude
            )

            # Create processed event
            processed_event = ProcessedDisasterEvent(
                event_id=raw_data.data_id,  # Use our internal ID
                disaster_type=DisasterType.EARTHQUAKE,
                location=location,
                severity=magnitude,
                occurred_at=occurred_at,
                source="USGS",
                external_id=raw_data.external_id,
                title=properties.get("title"),
                metadata={
                    "magnitude_type": properties.get("magType", "mw"),
                    "place": properties.get("place"),
                    "tsunami_flag": properties.get("tsunami", 0),
                    "alert_level": properties.get("alert"),
                    "significance": properties.get("sig"),
                    "url": properties.get("url"),
                    "detail_url": properties.get("detail")
                }
            )

            return processed_event

        except Exception as e:
            usgs_parse_errors.inc()
            logger.error(f"Error processing earthquake feature: {e}")
            return None

    async def get_available_feeds(self) -> dict:
        """Get information about available USGS earthquake feeds."""
        feeds = {
            "real_time": {
                "significant_month": f"{self.base_url}/significant_month.geojson",
                "significant_week": f"{self.base_url}/significant_week.geojson",
                "significant_day": f"{self.base_url}/significant_day.geojson",
                "significant_hour": f"{self.base_url}/significant_hour.geojson",
                "m4.5_month": f"{self.base_url}/4.5_month.geojson",
                "m4.5_week": f"{self.base_url}/4.5_week.geojson",
                "m4.5_day": f"{self.base_url}/4.5_day.geojson",
                "m4.5_hour": f"{self.base_url}/4.5_hour.geojson",
                "m2.5_month": f"{self.base_url}/2.5_month.geojson",
                "m2.5_week": f"{self.base_url}/2.5_week.geojson",
                "m2.5_day": f"{self.base_url}/2.5_day.geojson",
                "m2.5_hour": f"{self.base_url}/2.5_hour.geojson",
                "m1.0_month": f"{self.base_url}/1.0_month.geojson",
                "m1.0_week": f"{self.base_url}/1.0_week.geojson",
                "m1.0_day": f"{self.base_url}/1.0_day.geojson",
                "m1.0_hour": f"{self.base_url}/1.0_hour.geojson",
                "all_month": f"{self.base_url}/all_month.geojson",
                "all_week": f"{self.base_url}/all_week.geojson",
                "all_day": f"{self.base_url}/all_day.geojson",
                "all_hour": f"{self.base_url}/all_hour.geojson",
            }
        }
        return feeds
