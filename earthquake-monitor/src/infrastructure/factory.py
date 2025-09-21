"""Factory for creating repository implementations based on configuration."""

import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.earthquake_repository import EarthquakeRepository
from src.infrastructure.database.config import get_async_session
from src.infrastructure.repositories.postgresql_earthquake_repository import (
    PostgreSQLEarthquakeRepository,
)
from src.presentation.dependencies import MockEarthquakeRepository


async def create_earthquake_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)] = None,
) -> EarthquakeRepository:
    """Factory function to create the appropriate earthquake repository."""
    repository_type = os.getenv("REPOSITORY_TYPE", "mock")

    if repository_type.lower() == "postgresql" and session is not None:
        return PostgreSQLEarthquakeRepository(session)
    else:
        # Default to mock repository for development/testing
        return MockEarthquakeRepository()


# For dependency injection in FastAPI
def get_earthquake_repository_factory():
    """Get the earthquake repository factory function."""
    repository_type = os.getenv("REPOSITORY_TYPE", "mock")

    if repository_type.lower() == "postgresql":
        # Return a dependency that requires database session
        async def postgresql_repo_dependency(
            session: Annotated[AsyncSession, Depends(get_async_session)],
        ) -> EarthquakeRepository:
            return PostgreSQLEarthquakeRepository(session)

        return postgresql_repo_dependency
    else:
        # Return a dependency that uses mock repository
        def mock_repo_dependency() -> EarthquakeRepository:
            # Use singleton pattern for mock repository
            if not hasattr(mock_repo_dependency, "_instance"):
                mock_repo_dependency._instance = MockEarthquakeRepository()
            return mock_repo_dependency._instance

        return mock_repo_dependency
