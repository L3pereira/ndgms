from typing import Optional

from src.application.dto.earthquake_dto import (
    EarthquakeFilters,
    PaginatedResponse,
    PaginationParams,
)
from src.domain.repositories.earthquake_repository import EarthquakeRepository


class GetEarthquakesUseCase:
    def __init__(self, earthquake_repository: EarthquakeRepository):
        self._earthquake_repository = earthquake_repository

    async def execute(
        self,
        filters: Optional[EarthquakeFilters] = None,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResponse:
        if pagination is None:
            pagination = PaginationParams()

        # Convert filters to dict for repository
        filter_dict = {}
        if filters:
            if filters.min_magnitude is not None:
                filter_dict["min_magnitude"] = filters.min_magnitude
            if filters.max_magnitude is not None:
                filter_dict["max_magnitude"] = filters.max_magnitude
            if filters.start_time is not None:
                filter_dict["start_time"] = filters.start_time
            if filters.end_time is not None:
                filter_dict["end_time"] = filters.end_time
            if filters.is_reviewed is not None:
                filter_dict["is_reviewed"] = filters.is_reviewed
            if filters.source is not None:
                filter_dict["source"] = filters.source

        # Get total count for pagination
        total = await self._earthquake_repository.count_with_filters(
            filter_dict or None
        )

        # Get paginated results
        earthquakes = await self._earthquake_repository.find_with_filters(
            filters=filter_dict or None, limit=pagination.size, offset=pagination.offset
        )

        return PaginatedResponse.create(earthquakes, total, pagination)
