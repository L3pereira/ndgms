# 🌍 Earthquake Monitor API

A comprehensive real-time earthquake monitoring system built with Clean Architecture principles, featuring USGS data ingestion, secure API access, and WebSocket real-time updates.

[![Tests](https://github.com/L3pereira/ndgms/workflows/Tests/badge.svg)](https://github.com/L3pereira/ndgms/actions)
[![Coverage](https://codecov.io/gh/L3pereira/ndgms/branch/main/graph/badge.svg)](https://codecov.io/gh/L3pereira/ndgms)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.2-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🚀 Features

### **Core Capabilities**
- **🌐 Real-time Data Ingestion** - Automated USGS earthquake data collection
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

### 1. **Clone and Setup**
```bash
git clone https://github.com/L3pereira/ndgms.git
cd ndgms/earthquake-monitor

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Database Setup**
```bash
# Start PostgreSQL (using Docker)
docker-compose up -d postgres

# Run migrations
alembic upgrade head
```

### 3. **Start the API**
```bash
# Development server
uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker
docker-compose up --build
```

### 4. **Access the API**
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

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

### **Core Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/health` | System health check | ❌ |
| `POST` | `/api/v1/auth/register` | Register new user | ❌ |
| `POST` | `/api/v1/auth/login` | User authentication | ❌ |
| `GET` | `/api/v1/earthquakes` | List earthquakes with filters | ✅ |
| `GET` | `/api/v1/earthquakes/{id}` | Get earthquake details | ✅ |
| `POST` | `/api/v1/earthquakes` | Create earthquake record | ✅ |
| `POST` | `/api/v1/ingestion/trigger` | Trigger USGS data ingestion | ✅ |
| `WS` | `/api/v1/ws` | WebSocket real-time updates | ✅ |

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

### **Clean Architecture Overview**

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

### **Key Design Patterns**

- **🔄 Repository Pattern**: Abstract data access
- **🎯 Use Case Pattern**: Application-specific business rules
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

# External APIs
USGS_BASE_URL=https://earthquake.usgs.gov/fdsnws/event/1
USGS_API_RATE_LIMIT=100

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

### **Data Ingestion**

```bash
# Manual USGS data ingestion
python scripts/ingestion/usgs_ingestion.py

# Scheduled ingestion (in production)
python scripts/ingestion/usgs_ingestion.py --schedule daily
```

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

- **📝 Unit Tests** (42 tests): Test individual components in isolation
- **🔗 Integration Tests** (45 tests): Test component interactions
- **🌐 API Tests**: End-to-end API functionality
- **🗄️ Database Tests**: Database operations and migrations

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
- **🧪 Testing**: In-memory database for fast tests
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

### **Monitoring & Logging**

- **📊 Structured Logging**: JSON logs with request tracing
- **📈 Metrics**: Request/response times, error rates
- **🚨 Alerting**: Health check failures and error thresholds
- **🔍 Tracing**: Request correlation IDs

## 📈 Performance

### **Optimization Features**

- **⚡ Async/Await**: Non-blocking I/O throughout
- **🏊 Connection Pooling**: Efficient database connections
- **📄 Pagination**: Memory-efficient large dataset handling
- **🗂️ Database Indexing**: Optimized query performance
- **💾 Future Caching**: Redis integration planned

### **Scalability Considerations**

- **🔄 Horizontal Scaling**: Stateless application design
- **📊 Load Balancing**: Ready for multiple instances
- **🗄️ Database Scaling**: Read replicas and sharding support
- **📡 Message Queuing**: Event-driven architecture for async processing

## 🤝 Contributing

### **Development Workflow**

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Install** development dependencies: `poetry install --with dev`
4. **Make** your changes with proper tests
5. **Run** quality checks: `make lint test`
6. **Commit** with conventional commits: `git commit -m "feat: add amazing feature"`
7. **Push** to your branch: `git push origin feature/amazing-feature`
8. **Create** a Pull Request

### **Code Standards**

- **🎯 Clean Architecture**: Follow established patterns
- **📝 Documentation**: Document all public APIs
- **🧪 Testing**: Maintain 95%+ test coverage
- **🔍 Type Hints**: Full type annotation required
- **📏 Code Style**: Black + isort + ruff compliance

### **Pull Request Process**

1. Ensure all tests pass and coverage remains high
2. Update documentation for new features
3. Add integration tests for new endpoints
4. Follow semantic versioning for changes
5. Request review from maintainers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[USGS](https://earthquake.usgs.gov/)** - Earthquake data provider
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Database ORM
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation
- **Clean Architecture** - Robert C. Martin's architectural pattern

---

## 🔗 Related Projects

- **[NDGMS](../README.md)** - Natural Disaster Global Monitoring System

---
