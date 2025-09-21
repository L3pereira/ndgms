"""Authentication models and schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """User login model."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model."""

    id: str
    created_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""

    refresh_token: str


class User(UserBase):
    """Complete user model for internal use."""

    id: str
    hashed_password: str
    created_at: datetime
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
