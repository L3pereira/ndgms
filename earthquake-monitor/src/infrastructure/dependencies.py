"""Infrastructure layer dependency injection."""

import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.earthquake_repository import EarthquakeRepository
from src.infrastructure.database.config import get_async_session
from src.infrastructure.repositories.postgresql_earthquake_repository import (
    PostgreSQLEarthquakeRepository,
)


async def get_postgresql_earthquake_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> EarthquakeRepository:
    """Get PostgreSQL earthquake repository."""
    return PostgreSQLEarthquakeRepository(session)


def get_earthquake_repository_impl() -> str:
    """Get the repository implementation type from environment."""
    return os.getenv("REPOSITORY_TYPE", "mock")  # Default to mock for development
