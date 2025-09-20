# Earthquake Monitor API

A robust earthquake monitoring system built with FastAPI following Clean Architecture principles.

## Features

- Real-time earthquake data ingestion from USGS
- RESTful API for earthquake data management
- Clean Architecture with domain-driven design
- Comprehensive test coverage
- Docker containerization
- CI/CD with GitHub Actions

## Tech Stack

- **Backend**: FastAPI 0.116.2
- **Database**: PostgreSQL with PostGIS
- **ORM**: SQLAlchemy 2.0.43
- **Cache**: Redis
- **Testing**: Pytest with asyncio support
- **Code Quality**: Black, Ruff, pre-commit hooks
- **Containerization**: Docker & Docker Compose

## Project Structure

```
earthquake-monitor/
├── src/
│   ├── domain/                 # Core business logic
│   │   ├── entities/          # Domain models
│   │   ├── repositories/      # Repository interfaces
│   │   └── services/          # Domain services
│   ├── application/           # Use cases
│   │   └── use_cases/        # Application services
│   ├── infrastructure/        # External concerns
│   │   ├── persistence/      # Database implementations
│   │   └── external/         # External API clients
│   └── presentation/         # API layer
│       ├── routers/         # FastAPI routers
│       └── schemas/         # Pydantic models
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docker/                  # Docker configurations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
└── scripts/                # Utility scripts
    ├── ingestion/
    │   └── usgs_ingestion.py
    └── setup/
        └── init_db.py
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (if running locally)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/L3pereira/ndgms.git
   cd ndgms/earthquake-monitor
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Running with Docker

1. **Start all services (Production)**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. **Start with development mode (Hot reload)**
   ```bash
   docker-compose -f docker/docker-compose.dev.yml up -d
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Running Locally

1. **Start the development server**
   ```bash
   source .venv/bin/activate
   uvicorn src.presentation.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Health Check
```bash
GET /health
```

### Earthquakes
```bash
POST /api/v1/earthquakes/
```

**Request Body:**
```json
{
  "latitude": 37.7749,
  "longitude": -122.4194,
  "depth": 10.5,
  "magnitude_value": 5.5,
  "magnitude_scale": "moment",
  "source": "USGS"
}
```

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/domain/test_earthquake.py -v
```

### Code Formatting
```bash
# Format code
black .
isort .

# Lint code
ruff check .

# Type checking
mypy src/
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `USGS_API_BASE_URL`: USGS earthquake API endpoint
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Architecture

This project follows Clean Architecture principles:

- **Domain Layer**: Pure business logic, no external dependencies
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: Database, external APIs, file system
- **Presentation Layer**: REST API, web controllers

### Key Principles

- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Interface Segregation**: Many specific interfaces are better than one general
- **Liskov Substitution**: Objects should be replaceable with instances of their subtypes

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Mocking**: Use dependency injection for easy mocking
- **Coverage**: Maintain >80% test coverage

## Deployment

### Docker Production Build
```bash
docker build -f docker/Dockerfile -t earthquake-monitor:latest .
docker run -p 8000:8000 earthquake-monitor:latest
```

## Scripts

### Database Initialization
```bash
# Initialize database with tables and seed data
python scripts/setup/init_db.py
```

### Data Ingestion
```bash
# Ingest earthquake data from USGS API
python scripts/ingestion/usgs_ingestion.py
```

### CI/CD
GitHub Actions workflow automatically:
- Runs tests on Python 3.11
- Checks code formatting and linting
- Builds Docker images
- Deploys to staging/production

## License

This project is part of the Natural Disaster Global Monitoring System (NDGMS).

## Support

For questions or issues, please open a GitHub issue or contact the development team.