"""PostgreSQL implementation of earthquake repository."""

from datetime import datetime

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

        # Create new earthquake model with PostGIS geometry
        earthquake_model = EarthquakeModel(
            id=earthquake.id,
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
            location=func.ST_SetSRID(
                func.ST_MakePoint(
                    earthquake.location.longitude, earthquake.location.latitude
                ),
                4326,
            ),
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

    async def find_by_id(self, earthquake_id: str) -> Earthquake | None:
        """Find an earthquake by its ID."""
        result = await self.session.execute(
            select(EarthquakeModel).where(EarthquakeModel.id == earthquake_id)
        )
        earthquake_model = result.scalar_one_or_none()

        if not earthquake_model:
            return None

        return self._model_to_entity(earthquake_model)

    async def find_all(self) -> list[Earthquake]:
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
        self, min_magnitude: float, max_magnitude: float | None = None
    ) -> list[Earthquake]:
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
    ) -> list[Earthquake]:
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
    ) -> list[Earthquake]:
        """Find earthquakes within a radius of a location using PostGIS ST_DWithin."""
        # Create a point geometry for the search location
        search_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # Use ST_DWithin with geography cast for accurate distance in meters
        # Convert radius from km to meters
        radius_meters = radius_km * 1000

        result = await self.session.execute(
            select(EarthquakeModel)
            .where(
                func.ST_DWithin(
                    func.ST_Transform(
                        EarthquakeModel.location, 3857
                    ),  # Transform to Web Mercator for accurate distance
                    func.ST_Transform(search_point, 3857),
                    radius_meters,
                )
            )
            .order_by(EarthquakeModel.occurred_at.desc())
        )
        earthquake_models = result.scalars().all()

        return [self._model_to_entity(model) for model in earthquake_models]

    async def find_unreviewed(self) -> list[Earthquake]:
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
        filters: dict | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Earthquake]:
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

            # Location radius filter using PostGIS
            if all(key in filters for key in ["latitude", "longitude", "radius_km"]):
                lat, lng, radius = (
                    filters["latitude"],
                    filters["longitude"],
                    filters["radius_km"],
                )
                search_point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
                radius_meters = radius * 1000

                conditions.append(
                    func.ST_DWithin(
                        func.ST_Transform(EarthquakeModel.location, 3857),
                        func.ST_Transform(search_point, 3857),
                        radius_meters,
                    )
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

    async def count_with_filters(self, filters: dict | None = None) -> int:
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

            # Location radius filter using PostGIS
            if all(key in filters for key in ["latitude", "longitude", "radius_km"]):
                lat, lng, radius = (
                    filters["latitude"],
                    filters["longitude"],
                    filters["radius_km"],
                )
                search_point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
                radius_meters = radius * 1000

                conditions.append(
                    func.ST_DWithin(
                        func.ST_Transform(EarthquakeModel.location, 3857),
                        func.ST_Transform(search_point, 3857),
                        radius_meters,
                    )
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

    async def find_nearest_earthquakes(
        self, latitude: float, longitude: float, limit: int = 10
    ) -> list[tuple[Earthquake, float]]:
        """Find nearest earthquakes with distances using PostGIS."""
        search_point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # Calculate distance in kilometers using geography
        distance_km = (
            func.ST_Distance(
                func.ST_Geography(EarthquakeModel.location),
                func.ST_Geography(search_point),
            )
            / 1000.0
        )

        result = await self.session.execute(
            select(EarthquakeModel, distance_km.label("distance_km"))
            .order_by(distance_km)
            .limit(limit)
        )

        rows = result.all()
        return [
            (self._model_to_entity(row.EarthquakeModel), float(row.distance_km))
            for row in rows
        ]
