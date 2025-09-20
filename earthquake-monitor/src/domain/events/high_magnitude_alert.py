from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class HighMagnitudeAlert:
    earthquake_id: str
    magnitude: float
    alert_level: str
    latitude: float
    longitude: float
    affected_radius_km: float
    requires_immediate_response: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
