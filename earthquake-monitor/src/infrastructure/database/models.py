"""SQLAlchemy database models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EarthquakeModel(Base):
    """SQLAlchemy model for earthquake data."""

    __tablename__ = "earthquakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Location data
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    depth = Column(Float, nullable=False)

    # Magnitude data
    magnitude_value = Column(Float, nullable=False, index=True)
    magnitude_scale = Column(String(20), nullable=False, default="moment")

    # Temporal data
    occurred_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Metadata
    source = Column(String(50), nullable=False, default="USGS", index=True)
    external_id = Column(String(100), unique=True, index=True)  # USGS event ID
    is_reviewed = Column(Boolean, nullable=False, default=False, index=True)

    # Additional data as JSON
    raw_data = Column(Text)  # Store original USGS JSON data

    def __repr__(self):
        return f"<EarthquakeModel(id={self.id}, magnitude={self.magnitude_value}, location=({self.latitude}, {self.longitude}))>"


class UserModel(Base):
    """SQLAlchemy model for user authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<UserModel(id={self.id}, email={self.email}, username={self.username})>"
        )
