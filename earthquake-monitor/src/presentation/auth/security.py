"""Security utilities for authentication."""

import bcrypt
from authx import AuthX, TokenPayload

from .config import get_auth_config


class SecurityService:
    """Security service for password hashing and user authentication."""

    def __init__(self, auth: AuthX):
        self.auth = auth

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def create_access_token(
        self, user_id: str, fresh: bool = True, **additional_claims
    ) -> str:
        """Create an access token for a user."""
        return self.auth.create_access_token(
            uid=user_id, fresh=fresh, **additional_claims
        )

    def create_refresh_token(self, user_id: str) -> str:
        """Create a refresh token for a user."""
        return self.auth.create_refresh_token(uid=user_id)

    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify and decode an access token."""
        from authx import RequestToken

        request_token = RequestToken(token=token, type="access", location="headers")
        return self.auth.verify_token(request_token)

    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify and decode a refresh token."""
        from authx import RequestToken

        request_token = RequestToken(token=token, type="refresh", location="headers")
        return self.auth.verify_token(request_token)


# Global instances - use singleton pattern properly
_security_instance = None
_auth_instance = None


def get_auth_instance() -> AuthX:
    """Get the AuthX instance using proper singleton pattern."""
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AuthX(config=get_auth_config())
    return _auth_instance


def get_security_service() -> SecurityService:
    """Get the security service instance using proper singleton pattern."""
    global _security_instance
    if _security_instance is None:
        _security_instance = SecurityService(auth=get_auth_instance())
    return _security_instance


def reset_security_service():
    """Reset the security service for testing purposes."""
    global _security_instance, _auth_instance
    _security_instance = None
    _auth_instance = None
