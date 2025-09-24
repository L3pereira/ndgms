"""Domain service for earthquake validation business rules."""

from datetime import UTC, datetime

from ..exceptions import InvalidEarthquakeDataError


class EarthquakeValidationService:
    """Domain service responsible for earthquake validation business rules."""

    def validate_earthquake_data(
        self,
        magnitude_value: float,
        magnitude_scale: str,
        latitude: float,
        longitude: float,
        depth: float,
        occurred_at: datetime,
        source: str,
        external_id: str | None = None,
    ) -> None:
        """Validate earthquake data according to business rules."""
        self._validate_source(source)
        self._validate_magnitude_scale(magnitude_scale)
        self._validate_external_id(external_id)
        self._validate_occurrence_time(occurred_at)
        self._validate_coordinates(latitude, longitude, depth)
        self._validate_magnitude_value(magnitude_value)

    def _validate_source(self, source: str) -> None:
        """Validate earthquake source."""
        if not source or not source.strip():
            raise InvalidEarthquakeDataError("Source cannot be empty")

    def _validate_magnitude_scale(self, magnitude_scale: str) -> None:
        """Validate magnitude scale."""
        valid_scales = {"richter", "moment", "body_wave", "surface_wave"}
        if magnitude_scale not in valid_scales:
            raise InvalidEarthquakeDataError(
                f"Invalid magnitude scale: {magnitude_scale}. "
                f"Valid scales: {', '.join(valid_scales)}"
            )

    def _validate_external_id(self, external_id: str | None) -> None:
        """Validate external ID."""
        if external_id and len(external_id) > 100:
            raise InvalidEarthquakeDataError("External ID cannot exceed 100 characters")

    def _validate_occurrence_time(self, occurred_at: datetime) -> None:
        """Validate earthquake occurrence time."""
        current_time = datetime.now(UTC)

        # Ensure we have timezone info
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)

        if occurred_at > current_time:
            raise InvalidEarthquakeDataError(
                "Earthquake occurrence time cannot be in the future"
            )

    def _validate_coordinates(
        self, latitude: float, longitude: float, depth: float
    ) -> None:
        """Validate geographical coordinates."""
        if not -90 <= latitude <= 90:
            raise InvalidEarthquakeDataError(
                "Latitude must be between -90 and 90 degrees"
            )

        if not -180 <= longitude <= 180:
            raise InvalidEarthquakeDataError(
                "Longitude must be between -180 and 180 degrees"
            )

        if depth < 0:
            raise InvalidEarthquakeDataError("Depth must be non-negative")

    def _validate_magnitude_value(self, magnitude_value: float) -> None:
        """Validate magnitude value."""
        if not 0 <= magnitude_value <= 12:
            raise InvalidEarthquakeDataError("Magnitude must be between 0 and 12")
