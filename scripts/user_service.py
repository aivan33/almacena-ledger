"""
User management service for CRUD operations.

Handles user creation, retrieval, updates, and soft deletion
with proper validation and error handling.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from scripts.models.user import User
from scripts.auth import hash_password
from scripts.exceptions import ValidationError, DashboardError
from scripts.logger_config import get_logger

logger = get_logger(__name__)


class UserService:
    """
    User management service for CRUD operations.

    Provides methods to create, read, update, and delete users
    with proper validation and error handling.

    Args:
        db_session: SQLAlchemy database session
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_user(
        self,
        email: str,
        password: str,
        role: str = 'viewer',
        active: bool = True
    ) -> User:
        """
        Create a new user account.

        Args:
            email: User email address (must be unique)
            password: Plain text password (will be hashed)
            role: User role (admin, editor, viewer)
            active: Whether account is active

        Returns:
            User: Created user object

        Raises:
            ValidationError: If email already exists or validation fails
            DashboardError: If database operation fails
        """
        # Validate email format
        if not email or '@' not in email:
            raise ValidationError('Invalid email format')

        # Validate password strength
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters')

        # Validate role
        valid_roles = ['admin', 'editor', 'viewer']
        if role not in valid_roles:
            raise ValidationError(f'Invalid role. Must be one of: {", ".join(valid_roles)}')

        try:
            # Hash password
            password_hash = hash_password(password)

            # Create user
            user = User(
                email=email,
                password_hash=password_hash,
                role=role,
                active=active,
                failed_login_attempts=0,
                locked_until=None
            )

            self.db_session.add(user)
            self.db_session.commit()
            self.db_session.refresh(user)

            logger.info(f"User created successfully: {email}")
            return user

        except IntegrityError as e:
            self.db_session.rollback()
            if 'UNIQUE constraint failed' in str(e) or 'email' in str(e).lower():
                raise ValidationError(f'Email already exists: {email}')
            raise DashboardError(f'Failed to create user: {str(e)}')
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create user {email}: {e}")
            raise DashboardError(f'Failed to create user: {str(e)}')

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        try:
            user = self.db_session.query(User).filter(User.id == user_id).first()
            if user:
                logger.debug(f"User retrieved by ID: {user_id}")
            return user
        except Exception as e:
            logger.error(f"Failed to retrieve user by ID {user_id}: {e}")
            raise DashboardError(f'Failed to retrieve user: {str(e)}')

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.

        Args:
            email: User email address

        Returns:
            User object or None if not found
        """
        try:
            user = self.db_session.query(User).filter(User.email == email).first()
            if user:
                logger.debug(f"User retrieved by email: {email}")
            return user
        except Exception as e:
            logger.error(f"Failed to retrieve user by email {email}: {e}")
            raise DashboardError(f'Failed to retrieve user: {str(e)}')

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
        active: Optional[bool] = None
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID to update
            email: New email address (optional)
            password: New password (optional, will be hashed)
            role: New role (optional)
            active: New active status (optional)

        Returns:
            Updated user object

        Raises:
            ValidationError: If user not found or validation fails
            DashboardError: If database operation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValidationError(f'User not found: {user_id}')

        try:
            # Update email if provided
            if email is not None:
                if not email or '@' not in email:
                    raise ValidationError('Invalid email format')
                user.email = email

            # Update password if provided
            if password is not None:
                if len(password) < 8:
                    raise ValidationError('Password must be at least 8 characters')
                user.password_hash = hash_password(password)

            # Update role if provided
            if role is not None:
                valid_roles = ['admin', 'editor', 'viewer']
                if role not in valid_roles:
                    raise ValidationError(f'Invalid role. Must be one of: {", ".join(valid_roles)}')
                user.role = role

            # Update active status if provided
            if active is not None:
                user.active = active

            self.db_session.commit()
            self.db_session.refresh(user)

            logger.info(f"User updated successfully: {user.email}")
            return user

        except IntegrityError as e:
            self.db_session.rollback()
            if 'UNIQUE constraint failed' in str(e) or 'email' in str(e).lower():
                raise ValidationError(f'Email already exists: {email}')
            raise DashboardError(f'Failed to update user: {str(e)}')
        except ValidationError:
            self.db_session.rollback()
            raise
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise DashboardError(f'Failed to update user: {str(e)}')

    def delete_user(self, user_id: int) -> User:
        """
        Soft delete user by setting active=False.

        Does not remove user from database to preserve audit trail.

        Args:
            user_id: User ID to delete

        Returns:
            Deactivated user object

        Raises:
            ValidationError: If user not found
            DashboardError: If database operation fails
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValidationError(f'User not found: {user_id}')

        try:
            user.active = False
            self.db_session.commit()
            self.db_session.refresh(user)

            logger.info(f"User soft deleted: {user.email}")
            return user

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise DashboardError(f'Failed to delete user: {str(e)}')

    def list_users(
        self,
        role: Optional[str] = None,
        active_only: bool = False
    ) -> List[User]:
        """
        List all users with optional filtering.

        Args:
            role: Filter by role (optional)
            active_only: Only return active users (default: False)

        Returns:
            List of User objects

        Raises:
            DashboardError: If database operation fails
        """
        try:
            query = self.db_session.query(User)

            # Filter by role if provided
            if role is not None:
                valid_roles = ['admin', 'editor', 'viewer']
                if role not in valid_roles:
                    raise ValidationError(f'Invalid role. Must be one of: {", ".join(valid_roles)}')
                query = query.filter(User.role == role)

            # Filter by active status if requested
            if active_only:
                query = query.filter(User.active == True)

            users = query.all()
            logger.debug(f"Listed {len(users)} users (role={role}, active_only={active_only})")
            return users

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise DashboardError(f'Failed to list users: {str(e)}')
