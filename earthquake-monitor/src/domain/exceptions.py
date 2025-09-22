"""Domain layer exceptions for the earthquake monitoring system."""


class DomainException(Exception):
    """Base exception for domain layer errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InvalidEarthquakeDataError(DomainException):
    """Raised when earthquake data validation fails."""

    pass


class InvalidLocationError(DomainException):
    """Raised when location data is invalid."""

    pass


class InvalidMagnitudeError(DomainException):
    """Raised when magnitude data is invalid."""

    pass


class EarthquakeNotFoundError(DomainException):
    """Raised when an earthquake cannot be found."""

    pass


class EarthquakeAlreadyExistsError(DomainException):
    """Raised when attempting to create a duplicate earthquake."""

    pass


class InvalidDateTimeError(DomainException):
    """Raised when datetime values are invalid."""

    pass
