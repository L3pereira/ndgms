"""Authentication router with OAuth2 endpoints."""

from typing import Annotated

from authx import TokenPayload
from fastapi import APIRouter, Depends, HTTPException, status

from ..exceptions import ResourceNotFoundError, ValidationError
from .dependencies import get_current_user_payload
from .models import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from .repository import UserRepository, get_user_repository
from .security import SecurityService, get_security_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserResponse:
    """Register a new user."""
    try:
        user = user_repo.create_user(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
        )
    except ValueError as e:
        raise ValidationError(str(e))


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    security: Annotated[SecurityService, Depends(get_security_service)],
) -> TokenResponse:
    """Authenticate a user and return tokens."""
    user = user_repo.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Update last login
    user_repo.update_last_login(user.id)

    # Create tokens
    access_token = security.create_access_token(
        user_id=user.id, fresh=True, email=user.email, username=user.username
    )
    refresh_token = security.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=86400,  # 24 hours
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    security: Annotated[SecurityService, Depends(get_security_service)],
) -> TokenResponse:
    """Refresh an access token using a refresh token."""
    try:
        # Verify the refresh token
        payload = security.verify_refresh_token(refresh_data.refresh_token)

        # Get the user
        user = user_repo.get_user_by_id(payload.sub)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new access token (not fresh)
        access_token = security.create_access_token(
            user_id=user.id, fresh=False, email=user.email, username=user.username
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Keep the same refresh token
            expires_in=86400,  # 24 hours
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    payload: Annotated[TokenPayload, Depends(get_current_user_payload)],
) -> UserResponse:
    """Get the current authenticated user's information."""
    user = user_repo.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise ResourceNotFoundError("User", payload.sub)

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.post(
    "/logout", dependencies=[Depends(get_security_service().auth.access_token_required)]
)
async def logout_user() -> dict:
    """Logout the current user."""
    # In a real application, you would add the token to a blacklist
    # For now, we'll just return a success message
    return {"message": "Successfully logged out"}


@router.get("/verify")
async def verify_token(
    payload: Annotated[TokenPayload, Depends(get_current_user_payload)],
) -> dict:
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": payload.sub,
        "token_type": payload.type,
        "fresh": getattr(payload, "fresh", False),
    }
