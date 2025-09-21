"""Authentication dependencies for protecting endpoints."""

from typing import Annotated, Optional

from authx import TokenPayload
from fastapi import Depends, HTTPException, Request, status

from .models import User
from .repository import UserRepository, get_user_repository
from .security import SecurityService, get_security_service


async def get_current_user_payload(
    request: Request, security: SecurityService = Depends(get_security_service)
) -> TokenPayload:
    """Get the current user's token payload (requires valid access token)."""
    # Use the dependency injected security service
    return await security.auth.access_token_required(request)


def get_optional_current_user_payload() -> Optional[TokenPayload]:
    """Get the current user's token payload (optional - can be None)."""
    # For optional tokens, we'll handle this in the route itself
    # This is a placeholder that returns None - actual implementation
    # should use try/catch in the route
    return None


def get_current_user(
    payload: Annotated[TokenPayload, Depends(get_current_user_payload)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """Get the current authenticated user."""
    user = user_repo.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def get_optional_current_user(
    payload: Annotated[
        Optional[TokenPayload], Depends(get_optional_current_user_payload)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise."""
    if payload is None:
        return None

    user = user_repo.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        return None

    return user


async def require_fresh_token(
    request: Request, security: SecurityService = Depends(get_security_service)
) -> TokenPayload:
    """Require a fresh access token (recently authenticated)."""
    return await security.auth.fresh_token_required(request)


def require_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require the current user to be an admin."""
    # For this demo, we'll consider the admin@earthquake-monitor.com user as admin
    if current_user.email != "admin@earthquake-monitor.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user
