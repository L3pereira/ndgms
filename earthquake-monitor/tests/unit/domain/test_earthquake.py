from datetime import UTC, datetime, timedelta

import pytest

from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude
from src.domain.exceptions import InvalidDateTimeError


class TestEarthquake:
    def test_create_earthquake(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        occurred_at = datetime.now(UTC) - timedelta(hours=1)

        earthquake = Earthquake(
            location=location, magnitude=magnitude, occurred_at=occurred_at
        )

        assert earthquake.location == location
        assert earthquake.magnitude == magnitude
        assert earthquake.occurred_at == occurred_at
        assert earthquake.source == "USGS"
        assert earthquake.is_reviewed is False

    def test_mark_as_reviewed(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        occurred_at = datetime.now(UTC) - timedelta(hours=1)

        earthquake = Earthquake(
            location=location, magnitude=magnitude, occurred_at=occurred_at
        )

        earthquake.mark_as_reviewed()
        assert earthquake.is_reviewed is True

    def test_calculate_affected_radius(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=20.0)
        magnitude = Magnitude(value=6.0)
        occurred_at = datetime.now(UTC) - timedelta(hours=1)

        earthquake = Earthquake(
            location=location, magnitude=magnitude, occurred_at=occurred_at
        )

        radius = earthquake.calculate_affected_radius_km()
        assert radius > 0

    def test_create_earthquake_future_date_raises_error(self):
        """Test that creating an earthquake with future date raises InvalidDateTimeError."""
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        future_date = datetime.now(UTC) + timedelta(hours=1)  # 1 hour in the future

        with pytest.raises(InvalidDateTimeError) as exc_info:
            Earthquake(location=location, magnitude=magnitude, occurred_at=future_date)

        assert "Earthquake occurrence time cannot be in the future" in str(
            exc_info.value
        )

    def test_create_earthquake_current_time_succeeds(self):
        """Test that creating an earthquake with current time (edge case) succeeds."""
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        magnitude = Magnitude(value=5.5)
        current_time = datetime.now(UTC)

        # This should succeed (current time is not in the future)
        earthquake = Earthquake(
            location=location, magnitude=magnitude, occurred_at=current_time
        )

        assert earthquake.occurred_at == current_time
