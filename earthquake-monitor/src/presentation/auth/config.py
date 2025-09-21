"""Authentication configuration for the earthquake monitoring system."""

import os
from datetime import timedelta

from authx import AuthXConfig


def get_auth_config() -> AuthXConfig:
    """Get the authentication configuration."""
    config = AuthXConfig()

    # JWT Configuration
    config.JWT_ALGORITHM = "HS256"
    config.JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # 24 hours as timedelta
    config.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days as timedelta

    # Token Location - Keep it simple with headers only
    config.JWT_TOKEN_LOCATION = ["headers"]

    return config
