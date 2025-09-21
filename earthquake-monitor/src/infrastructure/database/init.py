"""Database initialization and setup."""

import asyncio
import logging

from src.infrastructure.database.config import async_engine, create_tables

logger = logging.getLogger(__name__)


async def initialize_database():
    """Initialize the database with tables."""
    try:
        logger.info("Creating database tables...")
        await create_tables()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def check_database_connection():
    """Check if database connection is working."""
    try:
        from sqlalchemy import text

        async with async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful!")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run database initialization
    asyncio.run(initialize_database())
