from datetime import UTC, datetime

from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert


class TestEarthquakeDetected:
    def test_create_earthquake_detected_event(self):
        event = EarthquakeDetected(
            earthquake_id="test-123",
            occurred_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
            magnitude=5.5,
            latitude=37.7749,
            longitude=-122.4194,
            depth=10.5,
            source="USGS",
        )

        assert event.earthquake_id == "test-123"
        assert event.magnitude == 5.5
        assert event.latitude == 37.7749
        assert event.longitude == -122.4194
        assert event.depth == 10.5
        assert event.source == "USGS"
        assert event.timestamp is not None


class TestHighMagnitudeAlert:
    def test_create_high_magnitude_alert(self):
        event = HighMagnitudeAlert(
            earthquake_id="test-456",
            magnitude=7.2,
            alert_level="CRITICAL",
            latitude=35.0,
            longitude=-118.0,
            affected_radius_km=150.0,
            requires_immediate_response=True,
        )

        assert event.earthquake_id == "test-456"
        assert event.magnitude == 7.2
        assert event.alert_level == "CRITICAL"
        assert event.latitude == 35.0
        assert event.longitude == -118.0
        assert event.affected_radius_km == 150.0
        assert event.requires_immediate_response is True
        assert event.timestamp is not None
