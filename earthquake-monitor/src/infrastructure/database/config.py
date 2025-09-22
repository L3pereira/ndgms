"""Database configuration and connection setup."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def create_async_engine(database_url: str, **kwargs):
    """Create async engine with consistent configuration."""
    import os

    # Default configuration for Docker/CI compatibility
    default_kwargs = {
        "echo": True,
        "pool_recycle": 300,
        "connect_args": {
            "server_settings": {
                "jit": "off",
            },
            "command_timeout": 60,
        },
    }

    # Only enable pool_pre_ping in production, not in tests
    if (
        os.getenv("REPOSITORY_TYPE") == "postgresql"
        and "test" not in database_url.lower()
    ):
        default_kwargs["pool_pre_ping"] = True

    default_kwargs.update(kwargs)

    return _create_async_engine(database_url, **default_kwargs)


# Database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/earthquake_monitor"
)

# For async operations
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create engines with better connection handling for Docker/CI environments
engine = create_engine(DATABASE_URL)
async_engine = create_async_engine(ASYNC_DATABASE_URL)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_session():
    """Get synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables (for testing)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
