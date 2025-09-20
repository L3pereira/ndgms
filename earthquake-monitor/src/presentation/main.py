from fastapi import FastAPI

from src.application.events.event_handlers import EarthquakeEventHandlers
from src.application.events.event_publisher import InMemoryEventPublisher
from src.domain.events.earthquake_detected import EarthquakeDetected
from src.domain.events.high_magnitude_alert import HighMagnitudeAlert

from .routers import earthquakes, websocket

app = FastAPI(
    title="Earthquake Monitor API",
    description="A real-time earthquake monitoring system with WebSocket support",
    version="0.1.0",
)

# Set up event system
event_publisher = InMemoryEventPublisher()
websocket_manager = websocket.get_websocket_manager()
event_handlers = EarthquakeEventHandlers(websocket_manager)

# Subscribe event handlers
event_publisher.subscribe(EarthquakeDetected, event_handlers.handle_earthquake_detected)
event_publisher.subscribe(
    HighMagnitudeAlert, event_handlers.handle_high_magnitude_alert
)

# Include routers
app.include_router(earthquakes.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def get_event_publisher():
    return event_publisher
