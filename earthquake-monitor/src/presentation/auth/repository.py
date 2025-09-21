"""User repository for authentication."""

import uuid
from datetime import UTC, datetime

from .models import User, UserCreate
from .security import get_security_service


class UserRepository:
    """In-memory user repository for demonstration purposes."""

    def __init__(self):
        self._users: dict[str, User] = {}
        self._users_by_email: dict[str, str] = {}  # email -> user_id mapping
        self._security = get_security_service()

        # Create a default admin user for testing
        self._create_default_users()

    def _create_default_users(self):
        """Create default users for testing."""
        admin_user = UserCreate(
            email="admin@earthquake-monitor.com",
            username="admin",
            full_name="System Administrator",
            password="admin123!@#",
            is_active=True,
        )
        self.create_user(admin_user)

        test_user = UserCreate(
            email="test@earthquake-monitor.com",
            username="testuser",
            full_name="Test User",
            password="testpass123",
            is_active=True,
        )
        self.create_user(test_user)

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        if user_data.email in self._users_by_email:
            raise ValueError("User with this email already exists")

        user_id = str(uuid.uuid4())
        hashed_password = self._security.hash_password(user_data.password)

        user = User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            hashed_password=hashed_password,
            created_at=datetime.now(UTC),
            last_login=None,
        )

        self._users[user_id] = user
        self._users_by_email[user_data.email] = user_id

        return user

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        user_id = self._users_by_email.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate a user by email and password."""
        user = self.get_user_by_email(email)
        if not user or not user.is_active:
            return None

        if self._security.verify_password(password, user.hashed_password):
            # Update last login
            user.last_login = datetime.now(UTC)
            return user

        return None

    def update_last_login(self, user_id: str) -> None:
        """Update the user's last login timestamp."""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.now(UTC)

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user."""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            return True
        return False

    def activate_user(self, user_id: str) -> bool:
        """Activate a user."""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = True
            return True
        return False


# Global user repository instance (singleton pattern)
_user_repository = None


def get_user_repository() -> UserRepository:
    """Get the user repository instance."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository()
    return _user_repository
