import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from src.application.events.event_handlers import EarthquakeEventHandlers
from src.application.events.event_publisher import InMemoryEventPublisher
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert

from .auth.router import router as auth_router
from .auth.security import get_security_service
from .exceptions import ResourceNotFoundError, ValidationError
from .routers import earthquakes, websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Earthquake Monitor API",
    description="A real-time earthquake monitoring system with WebSocket support",
    version="0.1.0",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure for specific hosts in production
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
event_handlers = EarthquakeEventHandlers(websocket_manager)

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
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def get_event_publisher():
    return event_publisher
