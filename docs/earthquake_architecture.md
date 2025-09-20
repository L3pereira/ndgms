# Earthquake Monitoring System - Clean Architecture Design

## Project Structure
```
earthquake-monitor/
├── src/
│   ├── domain/                     # Core business logic
│   │   ├── entities/
│   │   │   ├── earthquake.py       # Rich domain model
│   │   │   ├── location.py         # Value object for coordinates
│   │   │   └── magnitude.py        # Value object for magnitude
│   │   ├── services/
│   │   │   ├── earthquake_service.py      # Domain services
│   │   │   └── alert_service.py           # Business rules for alerts
│   │   ├── repositories/
│   │   │   └── earthquake_repository.py   # Abstract interfaces
│   │   └── events/
│   │       ├── earthquake_detected.py     # Domain events
│   │       └── high_magnitude_alert.py
│   │
│   ├── application/                # Use cases/Application services
│   │   ├── use_cases/
│   │   │   ├── ingest_earthquake_data.py
│   │   │   ├── get_earthquakes.py
│   │   │   ├── get_earthquake_details.py
│   │   │   └── stream_earthquake_updates.py
│   │   ├── dto/
│   │   │   ├── earthquake_dto.py
│   │   │   └── filter_dto.py
│   │   └── events/
│   │       └── event_handlers.py
│   │
│   ├── infrastructure/             # External concerns
│   │   ├── persistence/
│   │   │   ├── models/
│   │   │   │   └── earthquake_model.py    # SQLAlchemy models
│   │   │   ├── repositories/
│   │   │   │   └── postgres_earthquake_repository.py
│   │   │   └── database.py
│   │   ├── external/
│   │   │   ├── usgs_client.py      # USGS API integration
│   │   │   └── websocket_manager.py
│   │   ├── auth/
│   │   │   └── oauth2_provider.py
│   │   └── monitoring/
│   │       └── metrics.py
│   │
│   └── presentation/               # API layer
│       ├── api/
│       │   ├── endpoints/
│       │   │   ├── earthquakes.py
│       │   │   └── websocket.py
│       │   ├── middleware/
│       │   │   ├── auth_middleware.py
│       │   │   └── error_handler.py
│       │   └── schemas/
│       │       └── earthquake_schemas.py
│       └── main.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── integration/
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
└── scripts/
    ├── ingestion/
    │   └── usgs_ingestion.py
    └── setup/
        └── init_db.py
```

## Key Architecture Decisions

### 1. Domain Layer (Core Business Logic)

**Rich Domain Models:**
```python
# domain/entities/earthquake.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    depth: float

    def distance_to(self, other: 'Location') -> float:
        # Haversine formula implementation
        pass

    def is_near_populated_area(self) -> bool:
        # Business logic for proximity checks
        pass

@dataclass(frozen=True)
class Magnitude:
    value: float
    scale: str  # Richter, Moment, etc.

    def is_significant(self) -> bool:
        return self.value >= 5.0

    def get_alert_level(self) -> str:
        if self.value >= 7.0:
            return "CRITICAL"
        elif self.value >= 5.5:
            return "HIGH"
        elif self.value >= 4.0:
            return "MEDIUM"
        return "LOW"

class Earthquake:
    def __init__(self,
                 earthquake_id: str,
                 location: Location,
                 magnitude: Magnitude,
                 occurred_at: datetime,
                 source: str = "USGS"):
        self._id = earthquake_id
        self._location = location
        self._magnitude = magnitude
        self._occurred_at = occurred_at
        self._source = source
        self._is_reviewed = False

    def mark_as_reviewed(self) -> None:
        self._is_reviewed = True

    def requires_immediate_alert(self) -> bool:
        return (self._magnitude.is_significant() and
                self._location.is_near_populated_area())

    def calculate_affected_radius_km(self) -> float:
        # Business logic for impact calculation
        base_radius = self._magnitude.value * 20
        depth_factor = max(0.1, 1 - (self._location.depth / 100))
        return base_radius * depth_factor
```

**Domain Services:**
```python
# domain/services/alert_service.py
class AlertService:
    def should_trigger_alert(self, earthquake: Earthquake) -> bool:
        return earthquake.requires_immediate_alert()

    def calculate_impact_zone(self, earthquake: Earthquake) -> List[Location]:
        # Complex business logic for determining affected areas
        pass
```

### 2. Application Layer (Use Cases)

**Use Cases as Application Services:**
```python
# application/use_cases/ingest_earthquake_data.py
class IngestEarthquakeDataUseCase:
    def __init__(self,
                 earthquake_repo: EarthquakeRepository,
                 event_publisher: EventPublisher):
        self._earthquake_repo = earthquake_repo
        self._event_publisher = event_publisher

    async def execute(self, earthquake_data: dict) -> None:
        # Convert external data to domain object
        earthquake = self._create_earthquake_from_data(earthquake_data)

        # Check if already exists
        if await self._earthquake_repo.exists(earthquake.id):
            return

        # Save to repository
        await self._earthquake_repo.save(earthquake)

        # Publish domain event
        await self._event_publisher.publish(
            EarthquakeDetected(earthquake.id, earthquake.occurred_at)
        )

        # Check for alerts
        if earthquake.requires_immediate_alert():
            await self._event_publisher.publish(
                HighMagnitudeAlert(earthquake.id, earthquake.magnitude.value)
            )
```

### 3. Infrastructure Layer

**Repository Implementation:**
```python
# infrastructure/persistence/repositories/postgres_earthquake_repository.py
class PostgresEarthquakeRepository(EarthquakeRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, earthquake: Earthquake) -> None:
        # Map domain object to ORM model
        earthquake_model = EarthquakeModel(
            id=earthquake.id,
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
            magnitude=earthquake.magnitude.value,
            magnitude_scale=earthquake.magnitude.scale,
            occurred_at=earthquake.occurred_at,
            source=earthquake.source,
            is_reviewed=earthquake.is_reviewed
        )

        self._session.add(earthquake_model)
        await self._session.commit()

    async def find_by_filters(self, filters: EarthquakeFilters) -> List[Earthquake]:
        # Complex query building with PostGIS for geospatial queries
        query = select(EarthquakeModel)

        if filters.min_magnitude:
            query = query.where(EarthquakeModel.magnitude >= filters.min_magnitude)

        if filters.location_bounds:
            # PostGIS spatial query
            query = query.where(
                func.ST_Within(
                    EarthquakeModel.location,
                    func.ST_MakeEnvelope(*filters.location_bounds, 4326)
                )
            )

        result = await self._session.execute(query)
        models = result.scalars().all()

        # Map ORM models back to domain objects
        return [self._map_to_domain(model) for model in models]
```

### 4. Event-Driven Architecture

**Domain Events:**
```python
# domain/events/earthquake_detected.py
@dataclass(frozen=True)
class EarthquakeDetected:
    earthquake_id: str
    occurred_at: datetime
    timestamp: datetime = field(default_factory=datetime.utcnow)

# application/events/event_handlers.py
class EarthquakeEventHandlers:
    def __init__(self, websocket_manager: WebSocketManager):
        self._websocket_manager = websocket_manager

    async def handle_earthquake_detected(self, event: EarthquakeDetected):
        # Notify real-time subscribers
        await self._websocket_manager.broadcast_earthquake_update(event)

    async def handle_high_magnitude_alert(self, event: HighMagnitudeAlert):
        # Send urgent notifications
        await self._websocket_manager.broadcast_alert(event)
```

## Technology Choices

### Core Stack
- **FastAPI**: Excellent for async operations, automatic OpenAPI docs, type hints
- **SQLAlchemy 2.0**: Modern async ORM with excellent PostgreSQL support
- **PostgreSQL + PostGIS**: Geospatial capabilities essential for earthquake data
- **Pydantic**: Data validation and serialization
- **Redis**: Caching and session storage for real-time features

### Authentication & Security
- **OAuth2 with JWT**: Standard, secure, scalable
- **python-jose**: JWT handling
- **passlib**: Password hashing

### Real-time Features
- **WebSockets**: For real-time earthquake updates
- **Server-Sent Events (SSE)**: Alternative for simple real-time updates
- **asyncio**: Concurrent data ingestion and processing

### Monitoring & Logging
- **structlog**: Structured logging
- **prometheus-client**: Metrics collection
- **sentry-sdk**: Error tracking

## Why This Architecture?

1. **Separation of Concerns**: Each layer has a clear responsibility
2. **Testability**: Domain logic is completely isolated and easy to test
3. **Scalability**: Event-driven design allows for easy horizontal scaling
4. **Maintainability**: Changes to external APIs don't affect business logic
5. **Flexibility**: Can easily add new data sources, alert mechanisms, or output formats
6. **Performance**: Rich domain models with optimized database queries
7. **Real-time Capability**: Event-driven architecture naturally supports real-time features

## Implementation Priority

Given time constraints, I'd implement in this order:

1. **Core domain models and business logic** (earthquake, location, magnitude)
2. **Basic use cases** (ingest, get earthquakes, get details)
3. **Infrastructure** (database, repositories, USGS client)
4. **API endpoints** (REST endpoints with authentication)
5. **Real-time features** (WebSocket/SSE implementation)
6. **Event handling** (domain events and handlers)
7. **Monitoring and testing** (logging, metrics, comprehensive tests)

This architecture provides a solid foundation that can evolve with changing requirements while maintaining clean separation of concerns.
