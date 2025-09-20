import pytest

from src.domain.entities.magnitude import Magnitude, MagnitudeScale


class TestMagnitude:
    def test_valid_magnitude_creation(self):
        magnitude = Magnitude(value=5.5, scale=MagnitudeScale.MOMENT)
        assert magnitude.value == 5.5
        assert magnitude.scale == MagnitudeScale.MOMENT

    def test_default_scale_is_moment(self):
        magnitude = Magnitude(value=4.0)
        assert magnitude.scale == MagnitudeScale.MOMENT

    def test_negative_value_raises_error(self):
        with pytest.raises(ValueError, match="Magnitude value must be non-negative"):
            Magnitude(value=-1.0)

    def test_value_exceeding_maximum_raises_error(self):
        with pytest.raises(ValueError, match="Magnitude value cannot exceed 12"):
            Magnitude(value=13.0)

    def test_is_significant_true(self):
        magnitude = Magnitude(value=5.0)
        assert magnitude.is_significant() is True

        magnitude = Magnitude(value=7.5)
        assert magnitude.is_significant() is True

    def test_is_significant_false(self):
        magnitude = Magnitude(value=4.9)
        assert magnitude.is_significant() is False

        magnitude = Magnitude(value=2.0)
        assert magnitude.is_significant() is False

    def test_get_alert_level_critical(self):
        magnitude = Magnitude(value=7.0)
        assert magnitude.get_alert_level() == "CRITICAL"

        magnitude = Magnitude(value=8.5)
        assert magnitude.get_alert_level() == "CRITICAL"

    def test_get_alert_level_high(self):
        magnitude = Magnitude(value=5.5)
        assert magnitude.get_alert_level() == "HIGH"

        magnitude = Magnitude(value=6.9)
        assert magnitude.get_alert_level() == "HIGH"

    def test_get_alert_level_medium(self):
        magnitude = Magnitude(value=4.0)
        assert magnitude.get_alert_level() == "MEDIUM"

        magnitude = Magnitude(value=5.4)
        assert magnitude.get_alert_level() == "MEDIUM"

    def test_get_alert_level_low(self):
        magnitude = Magnitude(value=3.9)
        assert magnitude.get_alert_level() == "LOW"

        magnitude = Magnitude(value=1.0)
        assert magnitude.get_alert_level() == "LOW"

    def test_get_description_micro(self):
        magnitude = Magnitude(value=1.5)
        assert "Micro" in magnitude.get_description()

    def test_get_description_minor(self):
        magnitude = Magnitude(value=2.5)
        assert "Minor" in magnitude.get_description()

    def test_get_description_light(self):
        magnitude = Magnitude(value=3.5)
        assert "Light" in magnitude.get_description()

    def test_get_description_moderate(self):
        magnitude = Magnitude(value=4.5)
        assert "Moderate" in magnitude.get_description()

    def test_get_description_strong(self):
        magnitude = Magnitude(value=5.5)
        assert "Strong" in magnitude.get_description()

    def test_get_description_major(self):
        magnitude = Magnitude(value=6.5)
        assert "Major" in magnitude.get_description()

    def test_get_description_great(self):
        magnitude = Magnitude(value=7.5)
        assert "Great" in magnitude.get_description()

    def test_get_description_extreme(self):
        magnitude = Magnitude(value=8.5)
        assert "Extreme" in magnitude.get_description()

    def test_magnitude_immutability(self):
        magnitude = Magnitude(value=5.5)

        # Should not be able to modify the magnitude
        with pytest.raises(AttributeError):
            magnitude.value = 6.0
