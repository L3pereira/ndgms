import logging
import os
import time
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.application.events.event_handlers import EarthquakeEventHandlers
from src.application.events.event_publisher import InMemoryEventPublisher
from src.application.services.websocket_filter_service import WebSocketFilterService
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert
from src.domain.exceptions import DomainException

from .auth.router import router as auth_router
from .auth.security import get_security_service
from .exceptions import ResourceNotFoundError, ValidationError
from .routers import earthquakes, ingestion, websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Handle application startup and shutdown."""
    # Startup
    print("🔥 LIFESPAN STARTUP")
    logger.info("Starting earthquake monitor application...")

    # Initialize scheduler service but don't start it automatically
    # Scheduler will only start when explicitly called via /scheduler/start endpoint
    scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    logger.info(f"Scheduler enabled: {scheduler_enabled}")

    if scheduler_enabled:
        logger.info(
            "Scheduler is available but not started automatically - use /scheduler/start endpoint"
        )
    else:
        logger.info("Scheduler disabled via SCHEDULER_ENABLED=false")

    # Initialize app state for scheduler service (will be set when started via endpoint)
    app.state.scheduler_service = None

    logger.info("Application startup completed")

    yield

    # Shutdown
    print("🔥 LIFESPAN SHUTDOWN")
    logger.info("Shutting down earthquake monitor application...")

    if hasattr(app.state, "scheduler_service") and app.state.scheduler_service:
        try:
            await app.state.scheduler_service.stop()  # Note: stop() is now async again
            logger.info("Background scheduler service stopped successfully")
        except Exception as e:
            logger.error(
                f"Error stopping background scheduler service: {e}", exc_info=True
            )

    logger.info("Application shutdown completed")


app = FastAPI(
    lifespan=lifespan,
    title="Earthquake Monitor API",
    description="""
    # 🌍 NDGMS Earthquake Monitoring System

    A comprehensive real-time earthquake monitoring system that ingests data from USGS,
    provides secure API access, and delivers real-time updates via WebSocket.

    ## 🚀 Features

    - **Real-time Data Ingestion** from USGS earthquake feeds
    - **Secure RESTful API** with OAuth2 JWT authentication
    - **WebSocket Support** for live earthquake updates
    - **Advanced Filtering** by magnitude, time range, location, and source
    - **Comprehensive Pagination** for large datasets
    - **Clean Architecture** with domain-driven design

    ## 🔐 Authentication

    All endpoints (except `/health` and auth endpoints) require Bearer token authentication.

    1. **Register** a new account: `POST /api/v1/auth/register`
    2. **Login** to get access token: `POST /api/v1/auth/login`
    3. **Use token** in Authorization header: `Bearer <your_token>`

    ## 📡 Real-time Updates

    Connect to WebSocket endpoint `/api/v1/ws` for real-time earthquake notifications.

    ## 🗄️ Data Sources

    - **USGS**: United States Geological Survey earthquake data
    - **Manual Input**: Direct earthquake data entry via API

    ---

    **Built with Clean Architecture • FastAPI • PostgreSQL • WebSocket**
    """,
    version="1.0.0",
    contact={
        "name": "NDGMS Team",
        "url": "https://github.com/your-org/ndgms",
        "email": "contact@ndgms.org",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.ndgms.org", "description": "Production server"},
    ],
    tags_metadata=[
        {
            "name": "earthquakes",
            "description": "Earthquake data management and retrieval operations",
        },
        {
            "name": "auth",
            "description": "Authentication and user management endpoints",
        },
        {
            "name": "ingestion",
            "description": "Data ingestion from external sources like USGS",
        },
        {
            "name": "websocket",
            "description": "Real-time WebSocket connections for live updates",
        },
    ],
)


# Add middleware
def get_allowed_origins() -> list[str]:
    """Get allowed CORS origins from environment or default to secure values."""
    # Allow all origins in test environment
    if os.getenv("TESTING") == "true" or os.getenv("PYTEST_CURRENT_TEST"):
        return ["*"]

    origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if origins_env:
        return [origin.strip() for origin in origins_env.split(",")]
    # Default secure origins for development
    return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]


def get_allowed_hosts() -> list[str]:
    """Get allowed hosts from environment or default to secure values."""
    # Allow all hosts in test environment
    if os.getenv("TESTING") == "true" or os.getenv("PYTEST_CURRENT_TEST"):
        return ["*"]

    hosts_env = os.getenv("ALLOWED_HOSTS", "")
    if hosts_env:
        return [host.strip() for host in hosts_env.split(",")]
    # Default secure hosts for development
    return ["localhost", "127.0.0.1", "0.0.0.0"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_allowed_hosts(),
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Process-Time"] = str(process_time)

    # Log response
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")

    return response


# Centralized Exception Handlers
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(
    request: Request, exc: ResourceNotFoundError
) -> JSONResponse:
    logger.info(f"Resource not found: {request.method} {request.url.path} - {exc}")
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    logger.warning(
        f"Validation error in {request.method} {request.url.path}: {exc.message}"
    )
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(DomainException)
async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    logger.warning(
        f"Domain validation error in {request.method} {request.url.path}: {exc.message}"
    )
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.error(f"ValueError in {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {type(exc).__name__}: {str(exc)}"
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Set up event system
event_publisher = InMemoryEventPublisher()
websocket_manager = websocket.get_websocket_manager()

# Set up WebSocket filtering service
websocket_filter_service = WebSocketFilterService()

# Note: Event handlers will get repository via dependency injection when needed
# This avoids sync/async issues during app startup
event_handlers = EarthquakeEventHandlers(
    websocket_manager, None, websocket_filter_service
)

# Subscribe event handlers
event_publisher.subscribe(EarthquakeDetected, event_handlers.handle_earthquake_detected)
event_publisher.subscribe(
    HighMagnitudeAlert, event_handlers.handle_high_magnitude_alert
)

# Set up authentication
security_service = get_security_service()
security_service.auth.handle_errors(app)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(earthquakes.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/test-scheduler")
async def test_scheduler(request: Request):
    """Test endpoint to manually check scheduler status."""
    scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    if (
        scheduler_enabled
        and hasattr(request.app.state, "scheduler_service")
        and request.app.state.scheduler_service
    ):
        try:
            scheduler_service = request.app.state.scheduler_service
            jobs = scheduler_service.list_jobs()
            scheduler_status = {
                "enabled": True,
                "running": scheduler_service._scheduler.scheduler.running,
                "jobs": len(jobs),
                "job_list": list(jobs.keys()),
                "job_details": jobs,
            }
            return {"scheduler": scheduler_status}
        except Exception as e:
            return {"scheduler": {"enabled": True, "error": str(e)}}
    else:
        return {"scheduler": {"enabled": False}}


@app.post("/scheduler/start")
async def start_scheduler(request: Request):
    """Start the scheduler if it's not already running."""
    scheduler_enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"

    if not scheduler_enabled:
        return {
            "status": "error",
            "message": "Scheduler is disabled via SCHEDULER_ENABLED environment variable",
        }

    try:
        # Check if scheduler already exists and is running
        if (
            hasattr(request.app.state, "scheduler_service")
            and request.app.state.scheduler_service
            and request.app.state.scheduler_service._scheduler.scheduler.running
        ):
            jobs = request.app.state.scheduler_service.list_jobs()
            return {
                "status": "already_running",
                "message": "Scheduler is already running",
                "jobs": len(jobs),
                "job_details": jobs,
            }

        # Create and configure scheduler service
        from src.infrastructure.database.config import get_async_session_for_background
        from src.infrastructure.factory import (
            create_scheduled_job_service,
            get_earthquake_repository_factory,
        )

        # Get dependencies
        async with get_async_session_for_background() as session:
            repository_factory = get_earthquake_repository_factory()
            if callable(repository_factory):
                if repository_factory.__name__ == "postgresql_repo_dependency":
                    repository = await repository_factory(session)
                else:
                    repository = repository_factory()
            else:
                repository = repository_factory

            event_publisher = get_event_publisher()

            # Create scheduler service with dependencies
            scheduler_service = await create_scheduled_job_service(
                session=session,
                earthquake_repository=repository,
                event_publisher=event_publisher,
            )

            # Setup and start the scheduler
            await scheduler_service.setup_earthquake_ingestion_job()
            scheduler_service.start_scheduler()

        # Store in app state
        request.app.state.scheduler_service = scheduler_service

        jobs = scheduler_service.list_jobs()
        return {
            "status": "started",
            "message": "Scheduler started successfully",
            "jobs": len(jobs),
            "job_details": jobs,
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to start scheduler: {str(e)}"}


def get_event_publisher():
    return event_publisher
