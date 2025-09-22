"""User repository for authentication."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.infrastructure.database.models import UserModel

from .models import User, UserCreate
from .security import get_security_service


class UserRepository:
    """PostgreSQL-based user repository."""

    def __init__(self, session: Session):
        self.session = session
        self._security = get_security_service()

    def _user_model_to_domain(self, user_model: UserModel) -> User:
        """Convert UserModel to domain User."""
        return User(
            id=str(user_model.id),
            email=user_model.email,
            username=user_model.username,
            full_name=user_model.full_name,
            hashed_password=user_model.hashed_password,
            is_active=user_model.is_active,
            created_at=user_model.created_at,
            last_login=user_model.last_login,
        )

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = (
            self.session.query(UserModel)
            .filter(
                (UserModel.email == user_data.email)
                | (UserModel.username == user_data.username)
            )
            .first()
        )

        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("User with this email already exists")
            else:
                raise ValueError("User with this username already exists")

        # Hash password
        hashed_password = self._security.hash_password(user_data.password)

        # Create user model
        user_model = UserModel(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=user_data.is_active,
            created_at=datetime.now(UTC),
            last_login=None,
        )

        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)

        return self._user_model_to_domain(user_model)

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        user_model = (
            self.session.query(UserModel)
            .filter(UserModel.id == uuid.UUID(user_id))
            .first()
        )

        if user_model:
            return self._user_model_to_domain(user_model)
        return None

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        user_model = (
            self.session.query(UserModel).filter(UserModel.email == email).first()
        )

        if user_model:
            return self._user_model_to_domain(user_model)
        return None

    def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user_model = (
            self.session.query(UserModel).filter(UserModel.email == email).first()
        )

        if not user_model or not user_model.is_active:
            return None

        if self._security.verify_password(password, user_model.hashed_password):
            # Update last login
            user_model.last_login = datetime.now(UTC)
            self.session.commit()
            return self._user_model_to_domain(user_model)

        return None

    def update_last_login(self, user_id: str) -> None:
        """Update the user's last login timestamp."""
        user_model = (
            self.session.query(UserModel)
            .filter(UserModel.id == uuid.UUID(user_id))
            .first()
        )

        if user_model:
            user_model.last_login = datetime.now(UTC)
            self.session.commit()

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        user_model = (
            self.session.query(UserModel)
            .filter(UserModel.id == uuid.UUID(user_id))
            .first()
        )

        if user_model:
            user_model.is_active = False
            self.session.commit()
            return True
        return False

    def activate_user(self, user_id: str) -> bool:
        """Activate a user."""
        user_model = (
            self.session.query(UserModel)
            .filter(UserModel.id == uuid.UUID(user_id))
            .first()
        )

        if user_model:
            user_model.is_active = True
            self.session.commit()
            return True
        return False


def get_user_repository(session: Session) -> UserRepository:
    """Get the user repository instance with dependency injection."""
    return UserRepository(session)
