import pytest

from src.domain.entities.location import Location


class TestLocation:
    def test_valid_location_creation(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        assert location.latitude == 37.7749
        assert location.longitude == -122.4194
        assert location.depth == 10.5

    def test_invalid_latitude_raises_error(self):
        with pytest.raises(
            ValueError, match="Latitude must be between -90 and 90 degrees"
        ):
            Location(latitude=95.0, longitude=-122.4194, depth=10.5)

        with pytest.raises(
            ValueError, match="Latitude must be between -90 and 90 degrees"
        ):
            Location(latitude=-95.0, longitude=-122.4194, depth=10.5)

    def test_invalid_longitude_raises_error(self):
        with pytest.raises(
            ValueError, match="Longitude must be between -180 and 180 degrees"
        ):
            Location(latitude=37.7749, longitude=185.0, depth=10.5)

        with pytest.raises(
            ValueError, match="Longitude must be between -180 and 180 degrees"
        ):
            Location(latitude=37.7749, longitude=-185.0, depth=10.5)

    def test_negative_depth_raises_error(self):
        with pytest.raises(ValueError, match="Depth must be non-negative"):
            Location(latitude=37.7749, longitude=-122.4194, depth=-5.0)

    def test_distance_calculation(self):
        san_francisco = Location(latitude=37.7749, longitude=-122.4194, depth=0)
        los_angeles = Location(latitude=34.0522, longitude=-118.2437, depth=0)

        distance = san_francisco.distance_to(los_angeles)

        # Expected distance is approximately 559 km
        assert 550 <= distance <= 570

    def test_distance_to_same_location(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)
        distance = location.distance_to(location)
        assert distance == 0.0

    def test_is_near_populated_area_true(self):
        # Location near San Francisco
        location = Location(latitude=37.8, longitude=-122.4, depth=10.0)
        assert location.is_near_populated_area() is True

    def test_is_near_populated_area_false(self):
        # Location in the middle of the ocean
        location = Location(latitude=0.0, longitude=-150.0, depth=10.0)
        assert location.is_near_populated_area() is False

    def test_location_immutability(self):
        location = Location(latitude=37.7749, longitude=-122.4194, depth=10.5)

        # Should not be able to modify the location
        with pytest.raises(AttributeError):
            location.latitude = 40.0
