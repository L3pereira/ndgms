from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.application.dto.create_earthquake_request import CreateEarthquakeRequest
from src.application.dto.earthquake_dto import EarthquakeFilters, PaginationParams
from src.application.use_cases.create_earthquake import CreateEarthquakeUseCase
from src.application.use_cases.get_earthquake_details import GetEarthquakeDetailsUseCase
from src.application.use_cases.get_earthquakes import GetEarthquakesUseCase

from ..dependencies import (
    get_create_earthquake_use_case,
    get_get_earthquake_details_use_case,
    get_get_earthquakes_use_case,
)
from ..exceptions import ResourceNotFoundError
from ..schemas import (
    CreateEarthquakeSchema,
    EarthquakeDetailSchema,
    EarthquakeListItemSchema,
    EarthquakeListResponseSchema,
    EarthquakeResponseSchema,
    LocationSchema,
    MagnitudeSchema,
    PaginationSchema,
)

router = APIRouter(prefix="/earthquakes", tags=["earthquakes"])


@router.post(
    "/",
    response_model=EarthquakeResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new earthquake record",
    description="""
    Create a new earthquake record in the system.

    This endpoint allows manual entry of earthquake data, typically used for:
    - Testing purposes
    - Manual data entry from alternative sources
    - Data migration from legacy systems

    **Note**: This endpoint requires authentication.
    """,
    responses={
        201: {
            "description": "Earthquake created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "message": "Earthquake created successfully",
                    }
                }
            },
        },
        400: {"description": "Invalid earthquake data"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    },
)
async def create_earthquake(
    earthquake_data: CreateEarthquakeSchema,
    use_case: Annotated[
        CreateEarthquakeUseCase, Depends(get_create_earthquake_use_case)
    ],
):
    request = CreateEarthquakeRequest(
        latitude=earthquake_data.latitude,
        longitude=earthquake_data.longitude,
        depth=earthquake_data.depth,
        magnitude_value=earthquake_data.magnitude_value,
        magnitude_scale=earthquake_data.magnitude_scale,
        occurred_at=earthquake_data.occurred_at,
        source=earthquake_data.source,
    )

    earthquake_id = await use_case.execute(request)

    return EarthquakeResponseSchema(
        id=earthquake_id, message="Earthquake created successfully"
    )


@router.get(
    "/",
    response_model=EarthquakeListResponseSchema,
    summary="List earthquakes with filtering and pagination",
    description="""
    Retrieve a paginated list of earthquakes with comprehensive filtering options.

    ## 🔍 Available Filters:
    - **Magnitude Range**: Filter by minimum and maximum magnitude
    - **Time Range**: Filter by date/time range when earthquakes occurred
    - **Geographic Location**: Filter by radius around a specific location
    - **Data Source**: Filter by earthquake data source (e.g., USGS)
    - **Review Status**: Filter by review status

    ## 📄 Pagination:
    - Use `limit` and `offset` for pagination
    - Default limit is 50, maximum is 1000

    **Example**: Get recent high-magnitude earthquakes:
    `GET /earthquakes?min_magnitude=6.0&limit=10&start_time=2024-01-01T00:00:00Z`
    """,
    responses={
        200: {
            "description": "List of earthquakes with pagination metadata",
            "content": {
                "application/json": {
                    "example": {
                        "earthquakes": [
                            {
                                "id": "us6000abcd",
                                "magnitude": {"value": 7.2, "scale": "moment"},
                                "location": {
                                    "latitude": 35.5,
                                    "longitude": -120.5,
                                    "depth": 10.5,
                                },
                                "occurred_at": "2024-01-15T14:30:00Z",
                                "source": "USGS",
                            }
                        ],
                        "pagination": {
                            "total": 150,
                            "limit": 50,
                            "offset": 0,
                            "has_next": True,
                        },
                    }
                }
            },
        },
        401: {"description": "Authentication required"},
        422: {"description": "Invalid filter parameters"},
    },
)
async def get_earthquakes(
    use_case: Annotated[GetEarthquakesUseCase, Depends(get_get_earthquakes_use_case)],
    min_magnitude: Annotated[
        float, Query(ge=0, le=12, description="Minimum earthquake magnitude (0-12)")
    ] = None,
    max_magnitude: Annotated[float, Query(ge=0, le=12)] = None,
    start_time: Annotated[str, Query()] = None,
    end_time: Annotated[str, Query()] = None,
    latitude: Annotated[float, Query(ge=-90, le=90)] = None,
    longitude: Annotated[float, Query(ge=-180, le=180)] = None,
    radius_km: Annotated[float, Query(ge=0, le=20000)] = None,
    is_reviewed: Annotated[bool, Query()] = None,
    source: Annotated[str, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=1000)] = 50,
):
    from datetime import datetime

    # Parse datetime strings if provided
    start_datetime = (
        datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        if start_time
        else None
    )
    end_datetime = (
        datetime.fromisoformat(end_time.replace("Z", "+00:00")) if end_time else None
    )

    filters = EarthquakeFilters(
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        start_time=start_datetime,
        end_time=end_datetime,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        is_reviewed=is_reviewed,
        source=source,
    )

    pagination = PaginationParams(page=page, size=size)

    result = await use_case.execute(filters, pagination)

    # Convert earthquake entities to response schemas
    earthquake_items = []
    for eq in result.items:
        earthquake_items.append(
            EarthquakeListItemSchema(
                id=eq.id,
                latitude=eq.location.latitude,
                longitude=eq.location.longitude,
                depth=eq.location.depth,
                magnitude_value=eq.magnitude.value,
                magnitude_scale=eq.magnitude.scale.value,
                alert_level=eq.magnitude.get_alert_level(),
                occurred_at=eq.occurred_at,
                source=eq.source,
                is_reviewed=eq.is_reviewed,
            )
        )

    return EarthquakeListResponseSchema(
        earthquakes=earthquake_items,
        pagination=PaginationSchema(
            total=result.total,
            page=result.page,
            size=result.size,
            pages=result.pages,
        ),
    )


@router.get("/{earthquake_id}", response_model=EarthquakeDetailSchema)
async def get_earthquake_details(
    earthquake_id: str,
    use_case: Annotated[
        GetEarthquakeDetailsUseCase, Depends(get_get_earthquake_details_use_case)
    ],
):
    earthquake = await use_case.execute(earthquake_id)

    if not earthquake:
        raise ResourceNotFoundError("Earthquake", earthquake_id)

    # Convert earthquake entity to response schema
    return EarthquakeDetailSchema(
        id=earthquake.id,
        location=LocationSchema(
            latitude=earthquake.location.latitude,
            longitude=earthquake.location.longitude,
            depth=earthquake.location.depth,
        ),
        magnitude=MagnitudeSchema(
            value=earthquake.magnitude.value,
            scale=earthquake.magnitude.scale.value,
            alert_level=earthquake.magnitude.get_alert_level(),
            description=earthquake.magnitude.get_description(),
            is_significant=earthquake.magnitude.is_significant(),
        ),
        occurred_at=earthquake.occurred_at,
        source=earthquake.source,
        is_reviewed=earthquake.is_reviewed,
        affected_radius_km=earthquake.calculate_affected_radius_km(),
        requires_immediate_alert=earthquake.requires_immediate_alert(),
        impact_assessment=earthquake.get_impact_assessment(),
    )
