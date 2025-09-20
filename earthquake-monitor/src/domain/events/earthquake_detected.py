from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class EarthquakeDetected:
    earthquake_id: str
    occurred_at: datetime
    magnitude: float
    latitude: float
    longitude: float
    depth: float
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
