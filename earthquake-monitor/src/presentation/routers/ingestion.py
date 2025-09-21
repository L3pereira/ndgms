"""API endpoints for earthquake data ingestion."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.use_cases.ingest_earthquake_data import (
    IngestionRequest,
    ScheduledIngestionUseCase,
)
from src.infrastructure.external.usgs_service import USGSService

from ..dependencies import get_earthquake_repository, get_event_publisher

router = APIRouter(prefix="/ingestion", tags=["data-ingestion"])


class IngestionRequestSchema(BaseModel):
    """Schema for ingestion request."""

    source: str = Field(default="USGS", description="Data source")
    period: str = Field(
        default="day", description="Time period (hour, day, week, month)"
    )
    magnitude_filter: str = Field(
        default="2.5", description="Magnitude filter (all, significant, 4.5, 2.5, 1.0)"
    )
    limit: Optional[int] = Field(
        None, ge=1, le=1000, description="Maximum number of earthquakes to fetch"
    )


class IngestionResponseSchema(BaseModel):
    """Schema for ingestion response."""

    success: bool
    message: str
    total_fetched: int
    new_earthquakes: int
    updated_earthquakes: int
    errors: int
    earthquake_ids: list[str]


@router.post("/trigger", response_model=IngestionResponseSchema)
async def trigger_ingestion(
    request: IngestionRequestSchema,
    repository=Depends(get_earthquake_repository),
    event_publisher=Depends(get_event_publisher),
) -> IngestionResponseSchema:
    """Trigger manual earthquake data ingestion."""
    try:
        # Create USGS service
        usgs_service = USGSService()

        # Create use case
        use_case = ScheduledIngestionUseCase(repository, event_publisher, usgs_service)

        # Execute ingestion
        ingestion_request = IngestionRequest(
            source=request.source,
            period=request.period,
            magnitude_filter=request.magnitude_filter,
            limit=request.limit,
        )

        result = await use_case.execute(ingestion_request)

        # Close service
        await usgs_service.close()

        success = result.errors == 0 or (
            result.new_earthquakes > 0 or result.updated_earthquakes > 0
        )
        message = (
            f"Successfully ingested {result.new_earthquakes} new earthquakes"
            if success
            else f"Ingestion completed with {result.errors} errors"
        )

        return IngestionResponseSchema(
            success=success,
            message=message,
            total_fetched=result.total_fetched,
            new_earthquakes=result.new_earthquakes,
            updated_earthquakes=result.updated_earthquakes,
            errors=result.errors,
            earthquake_ids=result.earthquake_ids,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )


@router.get("/sources")
async def get_available_sources() -> dict:
    """Get available data sources and their configurations."""
    usgs_service = USGSService()
    try:
        feeds = await usgs_service.get_available_feeds()
        return {
            "sources": {
                "USGS": {
                    "description": "United States Geological Survey earthquake data",
                    "feeds": feeds,
                    "supported_periods": ["hour", "day", "week", "month"],
                    "supported_magnitudes": ["all", "significant", "4.5", "2.5", "1.0"],
                }
            }
        }
    finally:
        await usgs_service.close()


@router.get("/status")
async def get_ingestion_status() -> dict:
    """Get current ingestion system status."""
    return {
        "status": "operational",
        "supported_sources": ["USGS"],
        "last_ingestion": None,  # TODO: Implement tracking
        "next_scheduled": None,  # TODO: Implement scheduling
    }
