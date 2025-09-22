"""Configuration for population centers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PopulationCenter:
    """Represents a populated area with coordinates."""

    name: str
    latitude: float
    longitude: float
    proximity_threshold_km: float = 100.0


class PopulationCenterConfig:
    """Configuration for populated areas."""

    @staticmethod
    def get_default_population_centers() -> list[PopulationCenter]:
        """Get default list of major population centers."""
        return [
            PopulationCenter("San Francisco", 37.7749, -122.4194, 100.0),
            PopulationCenter("Los Angeles", 34.0522, -118.2437, 150.0),
            PopulationCenter("New York", 40.7128, -74.0060, 100.0),
            PopulationCenter("Tokyo", 35.6762, 139.6503, 150.0),
            PopulationCenter("Moscow", 55.7558, 37.6176, 100.0),
            PopulationCenter("London", 51.5074, -0.1278, 100.0),
            PopulationCenter("Mexico City", 19.4326, -99.1332, 100.0),
            PopulationCenter("Beijing", 39.9042, 116.4074, 100.0),
            PopulationCenter("Mumbai", 19.0760, 72.8777, 100.0),
            PopulationCenter("São Paulo", -23.5505, -46.6333, 100.0),
        ]

    @staticmethod
    def from_env_string(env_string: str) -> list[PopulationCenter]:
        """Parse population centers from environment string.

        Format: "name1,lat1,lon1,threshold1;name2,lat2,lon2,threshold2"
        """
        if not env_string.strip():
            return PopulationCenterConfig.get_default_population_centers()

        centers = []
        for center_str in env_string.split(";"):
            parts = center_str.strip().split(",")
            if len(parts) >= 3:
                name = parts[0].strip()
                latitude = float(parts[1].strip())
                longitude = float(parts[2].strip())
                threshold = float(parts[3].strip()) if len(parts) > 3 else 100.0
                centers.append(PopulationCenter(name, latitude, longitude, threshold))

        return (
            centers
            if centers
            else PopulationCenterConfig.get_default_population_centers()
        )
