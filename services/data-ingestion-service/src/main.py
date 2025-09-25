"""Data Ingestion Service - FastAPI application."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest
from starlette.responses import Response, JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor

from .application.ingestion_service import DataIngestionOrchestrator, IngestionResult

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = logging.getLogger(__name__)

# Global services
ingestion_orchestrator: DataIngestionOrchestrator | None = None
scheduler: AsyncIOScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global ingestion_orchestrator, scheduler

    # Startup
    logger.info("Starting Data Ingestion Service")

    # Initialize services
    ingestion_orchestrator = DataIngestionOrchestrator()
    await ingestion_orchestrator.start()

    # Initialize scheduler
    scheduler = AsyncIOScheduler(
        executors={"default": AsyncIOExecutor()},
        timezone="UTC"
    )

    # Schedule periodic ingestion jobs
    schedule_jobs()
    scheduler.start()

    logger.info("Data Ingestion Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Data Ingestion Service")

    if scheduler:
        scheduler.shutdown(wait=False)

    if ingestion_orchestrator:
        await ingestion_orchestrator.stop()

    logger.info("Data Ingestion Service shutdown complete")


app = FastAPI(
    title="NDGMS Data Ingestion Service",
    description="Microservice for ingesting disaster data from external sources",
    version="1.0.0",
    lifespan=lifespan
)


def schedule_jobs():
    """Schedule periodic ingestion jobs."""
    if not scheduler:
        return

    # USGS significant earthquakes every 5 minutes
    scheduler.add_job(
        func=scheduled_usgs_significant,
        trigger="interval",
        minutes=5,
        id="usgs_significant",
        name="USGS Significant Earthquakes",
        replace_existing=True
    )

    # USGS magnitude 4.5+ earthquakes every 15 minutes
    scheduler.add_job(
        func=scheduled_usgs_moderate,
        trigger="interval",
        minutes=15,
        id="usgs_moderate",
        name="USGS Moderate Earthquakes",
        replace_existing=True
    )

    # USGS all earthquakes every hour
    scheduler.add_job(
        func=scheduled_usgs_all,
        trigger="interval",
        hours=1,
        id="usgs_all",
        name="USGS All Earthquakes",
        replace_existing=True
    )

    logger.info("Scheduled ingestion jobs configured")


async def scheduled_usgs_significant():
    """Scheduled job for USGS significant earthquakes."""
    if ingestion_orchestrator:
        try:
            result = await ingestion_orchestrator.ingest_usgs_earthquakes(
                period="day", magnitude="significant"
            )
            logger.info(f"Scheduled USGS significant ingestion: {result}")
        except Exception as e:
            logger.error(f"Scheduled USGS significant ingestion failed: {e}")


async def scheduled_usgs_moderate():
    """Scheduled job for USGS moderate earthquakes."""
    if ingestion_orchestrator:
        try:
            result = await ingestion_orchestrator.ingest_usgs_earthquakes(
                period="day", magnitude="4.5"
            )
            logger.info(f"Scheduled USGS moderate ingestion: {result}")
        except Exception as e:
            logger.error(f"Scheduled USGS moderate ingestion failed: {e}")


async def scheduled_usgs_all():
    """Scheduled job for USGS all earthquakes."""
    if ingestion_orchestrator:
        try:
            result = await ingestion_orchestrator.ingest_usgs_earthquakes(
                period="hour", magnitude="all"
            )
            logger.info(f"Scheduled USGS all ingestion: {result}")
        except Exception as e:
            logger.error(f"Scheduled USGS all ingestion failed: {e}")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "service": "NDGMS Data Ingestion Service",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if not ingestion_orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    health = await ingestion_orchestrator.health_check()
    status_code = 200 if health["status"] == "healthy" else 503

    return JSONResponse(
        content=health,
        status_code=status_code
    )


@app.post("/ingest/usgs", tags=["Ingestion"], response_model=dict)
async def trigger_usgs_ingestion(
    period: str = "day",
    magnitude: str = "all"
):
    """Trigger manual USGS earthquake data ingestion."""
    if not ingestion_orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        result = await ingestion_orchestrator.ingest_usgs_earthquakes(
            period=period, magnitude=magnitude
        )

        return {
            "status": "success",
            "result": {
                "total_fetched": result.total_fetched,
                "raw_published": result.raw_published,
                "processed_published": result.processed_published,
                "errors": result.errors,
                "source": result.source,
                "disaster_type": result.disaster_type.value
            }
        }

    except Exception as e:
        logger.error(f"Manual USGS ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/feeds/usgs", tags=["Information"])
async def get_usgs_feeds():
    """Get available USGS earthquake feeds."""
    if not ingestion_orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    feeds = await ingestion_orchestrator.usgs_service.get_available_feeds()
    return feeds


@app.get("/jobs", tags=["Scheduling"])
async def list_scheduled_jobs():
    """List all scheduled ingestion jobs."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })

    return {"jobs": jobs}


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
