from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.create_earthquake import (
    CreateEarthquakeRequest,
    CreateEarthquakeUseCase,
)

from ..dependencies import get_create_earthquake_use_case
from ..schemas import CreateEarthquakeSchema, EarthquakeResponseSchema

router = APIRouter(prefix="/earthquakes", tags=["earthquakes"])


@router.post(
    "/", response_model=EarthquakeResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_earthquake(
    earthquake_data: CreateEarthquakeSchema,
    use_case: Annotated[
        CreateEarthquakeUseCase, Depends(get_create_earthquake_use_case)
    ],
):
    try:
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

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
