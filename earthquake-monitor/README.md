# 🌍 Earthquake Monitor API

A comprehensive real-time earthquake monitoring system built with Clean Architecture principles, featuring USGS data ingestion, secure API access, and WebSocket real-time updates.

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117.1-009688.svg)](https://fastapi.tiangolo.com)


## 🚀 Features

### **Core Capabilities**
- **🌐 Real-time Data Ingestion** - Automated USGS earthquake data collection
- **⏰ Intelligent Scheduler** - Configurable interval-based data ingestion with dependency injection architecture
- **🔒 Secure RESTful API** - OAuth2 JWT authentication with role-based access
- **📡 WebSocket Support** - Live earthquake notifications and updates
- **🔍 Advanced Filtering** - Search by magnitude, location, time, and source with PostGIS spatial queries
- **📄 Pagination** - Efficient handling of large datasets
- **⚡ High Performance** - Async/await throughout with connection pooling

### **Architecture Highlights**
- **🏗️ Clean Architecture** - Domain-driven design with proper separation of concerns
- **🧪 Comprehensive Testing** - 95%+ test coverage with unit and integration tests
- **🐳 Containerized** - Docker support with multi-stage builds
- **📊 Monitoring Ready** - Structured logging and health checks
- **🔧 Developer Experience** - Pre-commit hooks, linting, and type checking
- **🌍 Geospatial Database** - PostGIS integration for accurate spatial queries and indexing

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## ⚡ Quick Start

You can find the detailed Quick Start guide [here](./QUICK_START.md).

## 🛠️ Installation

### **System Requirements**
- Python 3.12+
- PostgreSQL 15+ with PostGIS 3.3+ extension
- Docker & Docker Compose (optional)

### **Local Development Setup**

1. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
vim .env
```

2. **Install Dependencies**
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

3. **Database Migration**
```bash
# Run database migrations
alembic upgrade head

# Create test data (optional)
python scripts/ingestion/usgs_ingestion.py
```

### **Docker Setup**

```bash
# Development environment
docker-compose -f docker/docker-compose.dev.yml up --build

# Production environment
docker-compose -f docker/docker-compose.yml up --build
```

## 📚 API Documentation

### **Interactive Documentation**
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### **Authentication Flow**

1. **Register a new user**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

2. **Login to get access token**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

3. **Use token for API requests**:
```bash
curl -X GET "http://localhost:8000/api/v1/earthquakes" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### **Complete API Reference**

#### **🔐 Authentication Endpoints** (`/api/v1/auth`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Register new user account | ❌ |
| `POST` | `/login` | User authentication (returns JWT tokens) | ❌ |
| `POST` | `/refresh` | Refresh access token using refresh token | ❌ |
| `GET` | `/me` | Get current authenticated user info | ✅ |
| `POST` | `/logout` | Logout current user | ✅ |
| `GET` | `/verify` | Verify if current token is valid | ✅ |

#### **🌍 Earthquake Data Endpoints** (`/api/v1/earthquakes`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | List earthquakes with advanced filtering & pagination | ✅ |
| `GET` | `/{earthquake_id}` | Get detailed earthquake information | ✅ |
| `POST` | `/` | Create earthquake record manually | ✅ |

#### **📥 Data Ingestion Endpoints** (`/api/v1/ingestion`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/trigger` | Manually trigger USGS data ingestion | ✅ |
| `GET` | `/sources` | Get available data sources (USGS feeds info) | ✅ |
| `GET` | `/status` | Get current ingestion system status | ✅ |

#### **📡 Real-time Communication**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `WS` | `/api/v1/ws` | WebSocket endpoint for real-time updates | ✅ |

#### **🏥 System Health & Monitoring**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/health` | System health check | ❌ |
| `POST` | `/api/v1/scheduler/start` | Start earthquake data scheduler (required for real-time ingestion) | ✅ |
| `GET` | `/test-scheduler` | Check scheduler status and job details | ❌ |

### **Filtering Examples**

```bash
# Get earthquakes by magnitude range
GET /api/v1/earthquakes?min_magnitude=5.0&max_magnitude=7.0

# Filter by time range
GET /api/v1/earthquakes?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z

# Geographic filtering using PostGIS (accurate distance within 100km)
GET /api/v1/earthquakes?latitude=34.0522&longitude=-118.2437&radius_km=100

# Pagination
GET /api/v1/earthquakes?limit=50&offset=100

# Combined filters
GET /api/v1/earthquakes?min_magnitude=6.0&source=USGS&limit=10
```

## 🏗️ Architecture

### **System Architecture**

```mermaid
graph TB
    %% External Systems
    USGS["🌍 USGS API<br/>GeoJSON Feeds & FDSNWS"]
    Client["💻 Frontend Client<br/>Web/Mobile App"]

    %% Presentation Layer
    subgraph "🌐 Presentation Layer"
        API["🔌 FastAPI<br/>REST Endpoints"]
        WS["📡 WebSocket<br/>Real-time Updates"]
        Auth["🔐 OAuth2/JWT<br/>Authentication"]
    end

    %% Application Layer
    subgraph "🔄 Application Layer"
        UC["⚙️ Use Cases<br/>Business Logic"]
        Events["📨 Event System<br/>Publisher/Handlers"]
        DTO["📦 DTOs<br/>Data Transfer"]
    end

    %% Domain Layer
    subgraph "🎯 Domain Layer"
        Entities["🏢 Entities<br/>Earthquake, Location, Magnitude"]
        DomainEvents["📢 Domain Events<br/>EarthquakeDetected, HighMagnitudeAlert"]
        Repository["📋 Repository Interfaces<br/>Abstract Data Access"]
    end

    %% Infrastructure Layer
    subgraph "🔌 Infrastructure Layer"
        PostgreSQL["🗄️ PostgreSQL + PostGIS<br/>Spatial Database"]
        USGSService["🌐 USGS Service<br/>External API Client"]
        RepoImpl["📊 Repository Implementation<br/>SQL Alchemy"]
    end

    %% Connections
    Client -.->|HTTP/WS| API
    Client -.->|WebSocket| WS
    API --> Auth
    API --> DTO
    DTO --> UC
    WS --> Events
    UC --> Entities
    UC --> Events
    Events --> DomainEvents
    Entities --> Repository
    Repository --> RepoImpl
    RepoImpl --> PostgreSQL
    UC --> USGSService
    USGSService -.->|REST API| USGS
    Events --> WS

    %% Styling
    classDef external fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef presentation fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef application fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef domain fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef infrastructure fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class USGS,Client external
    class API,WS,Auth presentation
    class UC,Events,DTO application
    class Entities,DomainEvents,Repository domain
    class PostgreSQL,USGSService,RepoImpl infrastructure
```

### **Data Flow Architecture**

#### **Real-time Data Ingestion Flow**

```mermaid
sequenceDiagram
    participant USGS as 🌍 USGS API<br/>earthquake.usgs.gov
    participant Scheduler as ⏰ Scheduler/Trigger<br/>ingestion.router<br/>Manual Start Required
    participant USGSService as 🔌 USGS Service<br/>USGSService<br/>httpx.AsyncClient
    participant UseCase as ⚙️ Ingestion Use Case<br/>IngestEarthquakeDataUseCase<br/>ScheduledIngestionUseCase
    participant Repository as 📊 Repository<br/>EarthquakeRepository<br/>PostgreSQLEarthquakeRepository
    participant PostgreSQL as 🗄️ PostgreSQL<br/>earthquakes table<br/>PostGIS functions
    participant Events as 📨 Event Publisher<br/>InMemoryEventPublisher<br/>EarthquakeEventHandlers
    participant WebSocket as 📡 WebSocket Manager<br/>WebSocketManager + FilterService<br/>filtered broadcasts with delays
    participant Client as 💻 Frontend Client<br/>WebSocket connection<br/>Real-time UI

    Note over USGS,Client: Real-time Earthquake Data Ingestion Flow

    %% Data Ingestion
    Scheduler->>+USGSService: fetch_recent_earthquakes()
    USGSService->>+USGS: GET /summary/all_day.geojson
    USGS-->>-USGSService: GeoJSON earthquake data
    USGSService-->>-Scheduler: List[Earthquake entities]

    Scheduler->>+UseCase: execute(earthquakes)
    loop For each earthquake
        UseCase->>+Repository: save(earthquake)
        Repository->>+PostgreSQL: INSERT INTO earthquakes
        PostgreSQL-->>-Repository: earthquake_id
        Repository-->>-UseCase: earthquake_id

        %% Domain Events
        UseCase->>+Events: publish(EarthquakeDetected)
        alt If magnitude >= 5.0
            UseCase->>Events: publish(HighMagnitudeAlert)
        end

        Events->>+WebSocket: broadcast_earthquake_update()
        Note over Events,WebSocket: WebSocket filtering applied<br/>(magnitude, age, rate limiting)
        WebSocket->>Client: Real-time notification (with title)
        Note over WebSocket: 150ms delay between broadcasts<br/>to prevent message dropping
        WebSocket-->>-Events: sent
        Events-->>-UseCase: events published
    end
    UseCase-->>-Scheduler: IngestionResult

    Note over Client: Client receives real-time earthquake updates via WebSocket
```

### **REST API Request Flow**

```mermaid
sequenceDiagram
    participant Client as 💻 Frontend Client<br/>React/Vue/Mobile App
    participant API as 🔌 FastAPI<br/>earthquakes.router<br/>auth.router
    participant Auth as 🔐 Auth Service<br/>SecurityService<br/>UserRepository
    participant DTO as 📦 DTO Layer<br/>EarthquakeFilters<br/>PaginationParams
    participant UseCase as ⚙️ Use Case<br/>GetEarthquakesUseCase<br/>GetEarthquakeDetailsUseCase
    participant Repository as 📊 Repository<br/>EarthquakeRepository<br/>PostgreSQLEarthquakeRepository
    participant PostgreSQL as 🗄️ PostgreSQL<br/>earthquakes table<br/>users table

    Note over Client,PostgreSQL: Typical REST API Request Flow

    %% Authentication
    Client->>+API: POST /api/v1/auth/login
    API->>+Auth: validate_credentials()
    Auth->>+Repository: find_user_by_email()
    Repository->>+PostgreSQL: SELECT * FROM users
    PostgreSQL-->>-Repository: user_data
    Repository-->>-Auth: User entity
    Auth-->>-API: JWT tokens
    API-->>-Client: {access_token, refresh_token}

    %% REST API Request
    Client->>+API: GET /api/v1/earthquakes?magnitude=5.0
    API->>+Auth: verify_token()
    Auth-->>-API: token_valid

    API->>+DTO: create_filter_dto(request)
    DTO-->>-API: EarthquakeFilters

    API->>+UseCase: get_earthquakes(filters, pagination)
    UseCase->>+Repository: find_with_filters()
    Repository->>+PostgreSQL: SELECT * FROM earthquakes WHERE...
    PostgreSQL-->>-Repository: earthquake_records
    Repository-->>-UseCase: List[Earthquake entities]
    UseCase-->>-API: PaginatedResult

    API-->>-Client: {earthquakes: [...], pagination: {...}}

    Note over Client: Client receives filtered earthquake data via REST API
```

### **Clean Architecture Layers**

```
📦 earthquake-monitor/
├── 🎯 src/domain/              # Core Business Logic (innermost layer)
│   ├── entities/               # Domain entities (Earthquake, Location, Magnitude)
│   ├── repositories/           # Repository interfaces
│   ├── services/               # Domain services
│   ├── events/                 # Domain events
│   └── exceptions.py           # Domain-specific exceptions
├── 🔄 src/application/         # Application Layer
│   ├── use_cases/              # Application use cases
│   ├── dto/                    # Data transfer objects
│   └── events/                 # Event handlers and publishers
├── 🔌 src/infrastructure/      # Infrastructure Layer (outermost)
│   ├── database/               # Database models and config
│   ├── repositories/           # Repository implementations
│   └── external/               # External API clients (USGS)
└── 🌐 src/presentation/        # Presentation Layer
    ├── routers/                # FastAPI route handlers
    ├── schemas/                # Pydantic models for API
    ├── auth/                   # Authentication logic
    └── main.py                 # FastAPI application
```

### **Domain-Driven Design**

- **🏢 Entities**: `Earthquake`, `Location`, `Magnitude` with rich business logic
- **📋 Value Objects**: Immutable objects like `Location` and `Magnitude`
- **🗂️ Repositories**: Abstract interfaces for data persistence
- **⚙️ Services**: Domain services for complex business operations
- **📨 Events**: Domain events for decoupled communication

### **Business Logic Separation** (Interview Showcase)

This project demonstrates **proper separation of business logic** across Clean Architecture layers, showing different types of business rules:

#### **🎯 Domain Layer Business Logic** (Core Business Rules)
**What earthquakes ARE** - Universal truths independent of any application

```python
# src/domain/entities/magnitude.py
class Magnitude:
    def is_significant(self) -> bool:
        """Seismological fact: magnitude ≥5.0 is significant."""
        return self.value >= 5.0

    def get_alert_level(self) -> str:
        """Scientific classification - universal truth."""
        if self.value >= 7.0: return "CRITICAL"     # Great earthquakes
        elif self.value >= 5.5: return "HIGH"       # Major earthquakes
        elif self.value >= 4.0: return "MEDIUM"     # Light earthquakes
        return "LOW"                                # Micro earthquakes

# src/domain/entities/earthquake.py
class Earthquake:
    def requires_immediate_alert(self) -> bool:
        """Core business rule: significant earthquakes near populated areas need alerts."""
        return (
            self.magnitude.is_significant() and
            self.location.is_near_populated_area()
        )

    def calculate_affected_radius_km(self) -> float:
        """Physics-based calculation - always true regardless of application."""
        base_radius = self.magnitude.value * 20  # Seismological formula
        depth_factor = max(0.1, 1 - (self.location.depth / 100))  # Depth impact
        return base_radius * depth_factor
```

#### **🔄 Application Layer Business Logic** (Workflow Orchestration)
**What to DO with earthquakes** - Application-specific processes and coordination

```python
# src/application/use_cases/ingest_earthquake_data.py
class IngestEarthquakeDataUseCase:
    async def execute(self, earthquakes: list[Earthquake]) -> IngestionResult:
        """Application workflow: how to process earthquake data in THIS system."""
        new_earthquakes = 0

        for earthquake in earthquakes:
            # Application logic: duplicate prevention (system-specific)
            existing = await self.repository.find_by_id(earthquake.id)
            if existing:
                continue  # Skip duplicates - application policy

            # Application workflow: persist earthquake
            earthquake_id = await self.repository.save(earthquake)
            new_earthquakes += 1

            # Application coordination: publish events based on domain rules
            await self._publish_events(earthquake)

        return IngestionResult(new_earthquakes=new_earthquakes)

    async def _publish_events(self, earthquake: Earthquake) -> None:
        """Application workflow: when and how to publish events."""
        # Always publish earthquake detected (application policy)
        earthquake_detected = EarthquakeDetected(...)
        await self.event_publisher.publish(earthquake_detected)

        # Use domain logic to decide, but publishing is application concern
        if earthquake.magnitude.is_significant():  # Domain rule
            high_magnitude_alert = HighMagnitudeAlert(...)
            await self.event_publisher.publish(high_magnitude_alert)  # App workflow

# src/application/use_cases/get_earthquakes.py
class GetEarthquakesUseCase:
    async def execute(self, filters: EarthquakeFilters, pagination: PaginationParams):
        """Application logic: how to retrieve and present earthquake data."""
        # Application workflow: coordinate filtering with repository
        earthquakes = await self.repository.find_with_filters(
            filters, pagination.offset, pagination.limit
        )

        # Application logic: calculate pagination metadata
        total = await self.repository.count_with_filters(filters)

        return PaginatedResult(
            items=earthquakes,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=(total + pagination.size - 1) // pagination.size  # App calculation
        )
```

#### **📊 Comparison Table**

| **Domain Logic** | **Application Logic** |
|------------------|----------------------|
| `magnitude.is_significant()` | "When to publish events" |
| `earthquake.requires_immediate_alert()` | "How to handle duplicates" |
| `calculate_affected_radius_km()` | "Pagination and filtering workflows" |
| **Pure business rules** | **Coordination and orchestration** |
| **Technology-independent** | **Uses repositories, events, external services** |
| **Always true (physics/science)** | **Application-specific policies** |
| **What earthquakes ARE** | **What to DO with earthquakes** |

This separation ensures:
- **Domain rules** can be tested in isolation
- **Business logic** is technology-independent
- **Application workflows** can change without affecting core business rules
- **Clean boundaries** between what the business does vs. how the system does it

### **Key Design Patterns**

- **🔄 Repository Pattern**: Abstract data access
- **🎯 Use Case Pattern**: Application-specific business workflows
- **🏭 Factory Pattern**: Object creation abstraction
- **📢 Observer Pattern**: Event-driven architecture
- **🛡️ Dependency Injection**: Loose coupling between layers

## ⚙️ Configuration

### **Environment Variables**

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/earthquake_monitor
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# USGS API Configuration
USGS_API_BASE_URL=https://earthquake.usgs.gov/fdsnws/event/1
USGS_GEOJSON_BASE_URL=https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary
USGS_API_TIMEOUT=30
USGS_POLLING_INTERVAL=300

# Automated Scheduler Configuration
SCHEDULER_ENABLED=true
USGS_INGESTION_INTERVAL_MINUTES=30
USGS_INGESTION_MIN_MAGNITUDE=2.5
USGS_INGESTION_PERIOD=hour

# Security
ALLOWED_ORIGINS=http://localhost:3000,https://app.ndgms.org
ALLOWED_HOSTS=localhost,127.0.0.1,api.ndgms.org

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
```

### **Database Configuration**

The system uses PostgreSQL with the following optimizations:
- **Connection Pooling**: SQLAlchemy async connection pool
- **Migrations**: Alembic for database versioning
- **Indexing**: Optimized indexes for query performance
- **PostGIS Integration**: Full spatial database capabilities with ST_DWithin, ST_Distance, and geometry indexing

## 🛠️ Development

### **Development Setup**

```bash
# Install development dependencies
poetry install --with dev

# Setup pre-commit hooks
pre-commit install

# Run in development mode
uvicorn src.presentation.main:app --reload --log-level debug
```

### **Code Quality Tools**

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all quality checks
make lint

# Auto-fix common issues
make format
```

### **Database Operations**

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations (includes PostGIS setup)
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
```

### **⏰ Automated Scheduler System**

The system features a robust automated data ingestion scheduler built with dependency injection for clean testing and production reliability:

#### **Scheduler Features**
- **🔄 Automatic USGS Data Ingestion** - Configurable interval-based earthquake data collection
- **🧪 Clean Architecture** - Dependency injection pattern for testable, isolated scheduler instances
- **⚡ Event Loop Compatibility** - Handles both production and test environments seamlessly
- **🛡️ Error Resilience** - Graceful handling of API failures and network interruptions
- **📊 Job Monitoring** - Real-time status tracking and job management capabilities
- **🔧 Environment Configuration** - Flexible scheduling intervals and data filtering

#### **Scheduler Configuration**
```bash
# Scheduler Settings
SCHEDULER_ENABLED=true                          # Enable/disable scheduled ingestion
USGS_INGESTION_INTERVAL_MINUTES=30             # Ingestion frequency (default: 30 minutes)
USGS_INGESTION_MIN_MAGNITUDE=2.5               # Minimum magnitude filter (default: 2.5)
USGS_INGESTION_PERIOD=hour                     # Time period for data fetch (hour/day/week)
```

#### **Scheduler Architecture**
```mermaid
flowchart TD
    A[🔧 Application Startup] --> B[🏭 SchedulerService Factory]
    B --> C[⏰ BackgroundScheduler Instance]
    C --> D[📅 USGS Ingestion Job]
    D --> E[🌐 USGS API Client]
    E --> F[📊 Data Processing Pipeline]
    F --> G[🗄️ Database Storage]
    F --> H[📨 Event Broadcasting]

    I[🧪 Test Environment] --> J[🏗️ Clean Scheduler Instance]
    J --> K[🔀 Isolated Job Testing]

    L[🛑 Application Shutdown] --> M[⏹️ Graceful Scheduler Stop]
    M --> N[🔄 Job State Reset]
```

#### **Scheduler Management API**
```bash
# Check scheduler status
GET /test-scheduler

# Response example
{
  "scheduler": {
    "enabled": true,
    "running": true,
    "jobs": 1,
    "job_list": ["usgs_ingestion"],
    "job_details": {
      "usgs_ingestion": {
        "id": "usgs_ingestion",
        "name": "usgs_ingestion",
        "next_run": "2024-01-15T15:00:00+00:00",
        "trigger": "interval[0:30:00]"
      }
    }
  }
}
```

#### **Dependency Injection Benefits**
- **🧪 Clean Testing**: Each test creates isolated scheduler instances
- **🔄 No Global State**: Eliminates test interference and race conditions
- **🏗️ Flexible Architecture**: Easy mocking and dependency substitution
- **📈 Better Coverage**: Comprehensive testing of scheduler lifecycle and error scenarios

### **🌍 USGS Data Integration**

The system integrates with USGS (United States Geological Survey) earthquake data through two complementary methods:

#### **1. GeoJSON Feed Service** (Primary - Real-time)
- **Endpoint**: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{magnitude}_{period}.geojson`
- **Usage**: Real-time monitoring with scheduled ingestion
- **Data**: Pre-built feeds with different magnitude thresholds and time periods
- **Examples**:
  - `all_day.geojson` - All earthquakes in the past 24 hours
  - `4.5_week.geojson` - Magnitude 4.5+ earthquakes in the past week
  - `significant_month.geojson` - Significant earthquakes in the past month

#### **2. FDSNWS Query API** (Historical Data)
- **Endpoint**: `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **Usage**: Flexible historical data retrieval and bulk imports
- **Features**: Custom date ranges, precise magnitude filtering, multiple output formats
- **Parameters**: `starttime`, `endtime`, `minmagnitude`, `format=geojson`

#### **Data Processing Pipeline**
```mermaid
flowchart LR
    A[🌍 USGS API] --> B[🔌 USGS Service]
    B --> C[📊 Data Validation]
    C --> D[🏢 Domain Entities]
    D --> E[📥 Repository Layer]
    E --> F[🗄️ PostgreSQL + PostGIS]
    D --> G[📨 Domain Events]
    G --> H[📡 WebSocket Broadcast]
    H --> I[💻 Real-time Clients]
```

### **🚨 High-Magnitude Alert System**

The system implements an intelligent alert system based on earthquake significance:

#### **Magnitude Classification**
- **Significant Earthquakes**: Magnitude ≥ 5.0
- **Alert Levels**:
  - 🟢 **LOW**: < 4.0 (Minor impact)
  - 🟡 **MEDIUM**: 4.0 - 5.4 (Moderate impact)
  - 🟠 **HIGH**: 5.5 - 6.9 (Major impact)
  - 🔴 **CRITICAL**: ≥ 7.0 (Extreme impact)

#### **Alert Triggers**
- **High-Magnitude Alert**: Automatically triggered for earthquakes ≥ 5.0
- **Immediate Response Required**: Earthquakes ≥ 5.0 near populated areas
- **Impact Radius**: Calculated as `magnitude × 20km × depth_factor`

#### **Real-time Notifications**
```json
{
  "type": "high_magnitude_alert",
  "data": {
    "earthquake_id": "us6000abcd",
    "magnitude": 7.2,
    "alert_level": "CRITICAL",
    "affected_radius_km": 144.0,
    "requires_immediate_response": true,
    "latitude": 35.5,
    "longitude": -120.5
  }
}
```

### **📡 WebSocket Real-time Features**

#### **Connection & Authentication**
- **Endpoint**: `ws://localhost:8000/api/v1/ws`
- **Authentication**: JWT token required for connection
- **Auto-reconnection**: Client-side reconnection handling recommended

#### **Subscription Types**
```json
// Subscribe to all new earthquake notifications
{"action": "subscribe_earthquakes"}

// Subscribe to high-magnitude alerts only (≥5.0)
{"action": "subscribe_alerts"}
```

#### **Real-time Message Types**

**1. Earthquake Detection** (All new earthquakes)
```json
{
  "type": "earthquake_detected",
  "data": {
    "id": "us6000abcd",
    "magnitude": 4.2,
    "latitude": 35.5,
    "longitude": -120.5,
    "depth": 10.5,
    "occurred_at": "2024-01-15T14:30:00Z",
    "source": "USGS",
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

**2. High-Magnitude Alert** (Significant earthquakes ≥5.0)
```json
{
  "type": "high_magnitude_alert",
  "data": {
    "earthquake_id": "us6000abcd",
    "magnitude": 6.8,
    "alert_level": "HIGH",
    "affected_radius_km": 95.2,
    "requires_immediate_response": true,
    "timestamp": "2024-01-15T14:32:15Z"
  }
}
```

**Note**: Currently, WebSocket subscriptions do not support severity filtering. Clients receive all events for their subscription type and should filter client-side based on alert levels.

#### **Manual Data Ingestion**
```bash
# Using the standalone script (FDSNWS API)
python scripts/ingestion/usgs_ingestion.py

# Using the API endpoint (GeoJSON feeds)
curl -X POST "http://localhost:8000/api/v1/ingestion/trigger" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "USGS",
    "period": "day",
    "magnitude_filter": "2.5",
    "limit": 100
  }'
```

#### **Ingestion Configuration**
```bash
# Environment variables for USGS integration
USGS_API_BASE_URL=https://earthquake.usgs.gov/fdsnws/event/1
USGS_GEOJSON_BASE_URL=https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary
USGS_API_TIMEOUT=30
USGS_POLLING_INTERVAL=300
```

#### **Available USGS Feed Options**
- **Time Periods**: `hour`, `day`, `week`, `month`
- **Magnitude Filters**: `all`, `significant`, `4.5`, `2.5`, `1.0`
- **Data Sources**: Real-time GeoJSON feeds updated every 5 minutes

## 🧪 Testing

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v
```

### **Test Categories**

- **📝 Unit Tests** (54+ tests): Test individual components in isolation
- **🔗 Integration Tests** (55+ tests): Test component interactions
- **🌐 API Tests**: End-to-end API functionality
- **🗄️ Database Tests**: Database operations and migrations
- **⏰ Scheduler Tests**: Automated ingestion and job management testing

### **Test Coverage**

Current test coverage: **95%+**

```bash
# Generate coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## 🚀 Deployment

### **Docker Deployment**

```bash
# Build production image
docker build -f docker/Dockerfile -t earthquake-monitor:latest .

# Run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Check service status
docker-compose ps
docker-compose logs earthquake-monitor
```

### **Environment-Specific Configurations**

- **🔧 Development**: `docker-compose.dev.yml` with hot reload
- **🚀 Production**: Optimized with proper security and monitoring

### **Health Checks**

The application includes comprehensive health checks:

```bash
# Application health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/health/db

# External service status
curl http://localhost:8000/health/external
```

---

## 🔗 Related Projects

- **[NDGMS](../README.md)** - Natural Disaster Global Monitoring System

---
