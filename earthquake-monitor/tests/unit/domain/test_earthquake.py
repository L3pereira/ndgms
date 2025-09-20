import pytest
from datetime import datetime, timedelta
from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude


class TestEarthquake:
    def test_create_earthquake(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        occurred_at = datetime.utcnow() - timedelta(hours=1)

        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=occurred_at
        )

        assert earthquake.location == location
        assert earthquake.magnitude == magnitude
        assert earthquake.occurred_at == occurred_at
        assert earthquake.source == "USGS"
        assert earthquake.is_reviewed is False

    def test_mark_as_reviewed(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        occurred_at = datetime.utcnow() - timedelta(hours=1)

        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=occurred_at
        )

        earthquake.mark_as_reviewed()
        assert earthquake.is_reviewed is True

    def test_calculate_affected_radius(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=20.0)
        magnitude = Magnitude(value=6.0)
        occurred_at = datetime.utcnow() - timedelta(hours=1)

        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=occurred_at
        )

        radius = earthquake.calculate_affected_radius_km()
        assert radius > 0