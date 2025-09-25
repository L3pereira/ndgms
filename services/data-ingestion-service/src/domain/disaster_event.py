"""Generic disaster event domain model."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class DisasterType(Enum):
    """Supported disaster types."""
    EARTHQUAKE = "earthquake"
    HURRICANE = "hurricane"
    FLOOD = "flood"
    VOLCANO = "volcano"
    FIRE = "fire"


class SeverityLevel(Enum):
    """Generic severity levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    EXTREME = "extreme"


@dataclass(frozen=True)
class Location:
    """Geographic location with coordinates."""
    latitude: float
    longitude: float
    depth: float = 0.0

    def __post_init__(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")


@dataclass(frozen=True)
class DisasterSeverity(ABC):
    """Abstract base for disaster severity measurements."""
    value: float
    scale: str

    @abstractmethod
    def get_level(self) -> SeverityLevel:
        """Get standardized severity level."""
        pass

    @abstractmethod
    def is_significant(self) -> bool:
        """Check if disaster is significant enough for alerts."""
        pass


@dataclass(frozen=True)
class EarthquakeMagnitude(DisasterSeverity):
    """Earthquake magnitude implementation."""
    scale: str = "MOMENT"  # Moment magnitude scale

    def get_level(self) -> SeverityLevel:
        """Map earthquake magnitude to severity level."""
        if self.value < 3.0:
            return SeverityLevel.LOW
        elif self.value < 5.0:
            return SeverityLevel.MODERATE
        elif self.value < 6.0:
            return SeverityLevel.HIGH
        elif self.value < 7.0:
            return SeverityLevel.SEVERE
        else:
            return SeverityLevel.EXTREME

    def is_significant(self) -> bool:
        """Earthquakes >= 5.0 are considered significant."""
        return self.value >= 5.0


@dataclass
class RawDisasterData:
    """Raw disaster data from external sources."""
    disaster_type: DisasterType
    external_id: str
    source: str
    raw_payload: dict[str, Any]
    ingested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    data_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ProcessedDisasterEvent:
    """Processed disaster event ready for publishing."""
    event_id: str
    disaster_type: DisasterType
    location: Location
    severity: DisasterSeverity
    occurred_at: datetime
    source: str
    external_id: str | None = None
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
