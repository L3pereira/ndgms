"""PostgreSQL implementation of earthquake repository."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.domain.entities.earthquake import Earthquake
from src.domain.entities.location import Location
from src.domain.entities.magnitude import Magnitude, MagnitudeScale
from src.domain.repositories.earthquake_repository import EarthquakeRepository
from src.infrastructure.database.models import EarthquakeModel


class PostgreSQLEarthquakeRepository(EarthquakeRepository):
    """PostgreSQL implementation of earthquake repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, earthquake: Earthquake) -> str:
        """Save an earthquake to the database."""
        # Check if earthquake already exists by external_id
        if hasattr(earthquake, "external_id") and earthquake.external_id:
            result = await self.session.execute(
                select(EarthquakeModel).where(
                    EarthquakeModel.external_id == earthquake.external_id
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                return str(existing.id)

        # Create new earthquake model
        earthquake_model = EarthquakeModel(
            id=earthquake.id,
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
            magnitude_value=earthquake.magnitude.value,
            magnitude_scale=earthquake.magnitude.scale.value,
            occurred_at=earthquake.occurred_at,
            source=earthquake.source,
            external_id=getattr(earthquake, "external_id", None),
            is_reviewed=getattr(earthquake, "is_reviewed", False),
            raw_data=getattr(earthquake, "raw_data", None),
        )

        self.session.add(earthquake_model)
        await self.session.commit()
        await self.session.refresh(earthquake_model)

        return str(earthquake_model.id)

    async def find_by_id(self, earthquake_id: str) -> Optional[Earthquake]:
        """Find an earthquake by its ID."""
        result = await self.session.execute(
            select(EarthquakeModel).where(EarthquakeModel.id == earthquake_id)
        )
        earthquake_model = result.scalar_one_or_none()

        if not earthquake_model:
            return None

        return self._model_to_entity(earthquake_model)

    async def find_all(self) -> List[Earthquake]:
        """Find all earthquakes."""
        result = await self.session.execute(
            select(EarthquakeModel).order_by(EarthquakeModel.occurred_at.desc())
        )
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def exists(self, earthquake_id: str) -> bool:
        """Check if an earthquake exists."""
        result = await self.session.execute(
            select(func.count(EarthquakeModel.id)).where(
                EarthquakeModel.id == earthquake_id
            )
        )
        count = result.scalar()
        return count > 0

    async def find_by_magnitude_range(
        self, min_magnitude: float, max_magnitude: Optional[float] = None
    ) -> List[Earthquake]:
        """Find earthquakes by magnitude range."""
        query = select(EarthquakeModel).where(
            EarthquakeModel.magnitude_value >= min_magnitude
        )

        if max_magnitude is not None:
            query = query.where(EarthquakeModel.magnitude_value <= max_magnitude)

        query = query.order_by(EarthquakeModel.occurred_at.desc())

        result = await self.session.execute(query)
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def find_by_time_range(
        self, start_time: datetime, end_time: datetime
    ) -> List[Earthquake]:
        """Find earthquakes by time range."""
        result = await self.session.execute(
            select(EarthquakeModel)
            .where(
                and_(
                    EarthquakeModel.occurred_at >= start_time,
                    EarthquakeModel.occurred_at <= end_time,
                )
            )
            .order_by(EarthquakeModel.occurred_at.desc())
        )
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def find_by_location_radius(
        self, latitude: float, longitude: float, radius_km: float
    ) -> List[Earthquake]:
        """Find earthquakes within a radius of a location (simple distance calculation)."""
        # Using simple bounding box calculation for now
        # In a real PostGIS implementation, we'd use ST_DWithin
        lat_range = radius_km / 111.0  # Approximate degrees per km
        lng_range = (
            radius_km / (111.0 * abs(latitude) / 90.0)
            if latitude != 0
            else radius_km / 111.0
        )

        result = await self.session.execute(
            select(EarthquakeModel)
            .where(
                and_(
                    EarthquakeModel.latitude.between(
                        latitude - lat_range, latitude + lat_range
                    ),
                    EarthquakeModel.longitude.between(
                        longitude - lng_range, longitude + lng_range
                    ),
                )
            )
            .order_by(EarthquakeModel.occurred_at.desc())
        )
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def find_unreviewed(self) -> List[Earthquake]:
        """Find all unreviewed earthquakes."""
        result = await self.session.execute(
            select(EarthquakeModel)
            .where(~EarthquakeModel.is_reviewed)
            .order_by(EarthquakeModel.occurred_at.desc())
        )
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def find_with_filters(
        self,
        filters: Optional[dict] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Earthquake]:
        """Find earthquakes with complex filters and pagination."""
        query = select(EarthquakeModel)

        if filters:
            conditions = []

            if filters.get("min_magnitude"):
                conditions.append(
                    EarthquakeModel.magnitude_value >= filters["min_magnitude"]
                )

            if filters.get("max_magnitude"):
                conditions.append(
                    EarthquakeModel.magnitude_value <= filters["max_magnitude"]
                )

            if filters.get("start_time"):
                conditions.append(EarthquakeModel.occurred_at >= filters["start_time"])

            if filters.get("end_time"):
                conditions.append(EarthquakeModel.occurred_at <= filters["end_time"])

            if filters.get("is_reviewed") is not None:
                conditions.append(EarthquakeModel.is_reviewed == filters["is_reviewed"])

            if filters.get("source"):
                conditions.append(EarthquakeModel.source == filters["source"])

            # Location radius filter
            if all(key in filters for key in ["latitude", "longitude", "radius_km"]):
                lat, lng, radius = (
                    filters["latitude"],
                    filters["longitude"],
                    filters["radius_km"],
                )
                lat_range = radius / 111.0
                lng_range = (
                    radius / (111.0 * abs(lat) / 90.0) if lat != 0 else radius / 111.0
                )

                conditions.extend(
                    [
                        EarthquakeModel.latitude.between(
                            lat - lat_range, lat + lat_range
                        ),
                        EarthquakeModel.longitude.between(
                            lng - lng_range, lng + lng_range
                        ),
                    ]
                )

            if conditions:
                query = query.where(and_(*conditions))

        # Order by occurred_at descending (newest first)
        query = query.order_by(EarthquakeModel.occurred_at.desc())

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def count_with_filters(self, filters: Optional[dict] = None) -> int:
        """Count earthquakes matching the given filters."""
        query = select(func.count(EarthquakeModel.id))

        if filters:
            conditions = []

            if filters.get("min_magnitude"):
                conditions.append(
                    EarthquakeModel.magnitude_value >= filters["min_magnitude"]
                )

            if filters.get("max_magnitude"):
                conditions.append(
                    EarthquakeModel.magnitude_value <= filters["max_magnitude"]
                )

            if filters.get("start_time"):
                conditions.append(EarthquakeModel.occurred_at >= filters["start_time"])

            if filters.get("end_time"):
                conditions.append(EarthquakeModel.occurred_at <= filters["end_time"])

            if filters.get("is_reviewed") is not None:
                conditions.append(EarthquakeModel.is_reviewed == filters["is_reviewed"])

            if filters.get("source"):
                conditions.append(EarthquakeModel.source == filters["source"])

            # Location radius filter
            if all(key in filters for key in ["latitude", "longitude", "radius_km"]):
                lat, lng, radius = (
                    filters["latitude"],
                    filters["longitude"],
                    filters["radius_km"],
                )
                lat_range = radius / 111.0
                lng_range = (
                    radius / (111.0 * abs(lat) / 90.0) if lat != 0 else radius / 111.0
                )

                conditions.extend(
                    [
                        EarthquakeModel.latitude.between(
                            lat - lat_range, lat + lat_range
                        ),
                        EarthquakeModel.longitude.between(
                            lng - lng_range, lng + lng_range
                        ),
                    ]
                )

            if conditions:
                query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()

    def _model_to_entity(self, model: EarthquakeModel) -> Earthquake:
        """Convert SQLAlchemy model to domain entity."""
        location = Location(
            latitude=model.latitude, longitude=model.longitude, depth=model.depth
        )

        magnitude = Magnitude(
            value=model.magnitude_value, scale=MagnitudeScale(model.magnitude_scale)
        )

        earthquake = Earthquake(
            location=location,
            magnitude=magnitude,
            occurred_at=model.occurred_at,
            source=model.source,
            earthquake_id=str(model.id),  # Set the earthquake_id field directly
        )

        # Set additional attributes
        earthquake._is_reviewed = model.is_reviewed
        if hasattr(model, "external_id") and model.external_id:
            earthquake.external_id = model.external_id
        if hasattr(model, "raw_data") and model.raw_data:
            earthquake.raw_data = model.raw_data

        return earthquake
