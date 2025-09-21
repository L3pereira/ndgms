from dataclasses import dataclass
from datetime import datetime


@dataclass
class EarthquakeFilters:
    min_magnitude: float | None = None
    max_magnitude: float | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None
    is_reviewed: bool | None = None
    source: str | None = None


@dataclass
class PaginationParams:
    page: int = 1
    size: int = 50

    def __post_init__(self):
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 1
        if self.size > 1000:
            self.size = 1000

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass
class PaginatedResponse:
    items: list
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list, total: int, pagination: PaginationParams):
        pages = (total + pagination.size - 1) // pagination.size
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=pages,
        )
