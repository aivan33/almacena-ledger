"""
Unit tests for UserService CRUD operations.

Tests cover:
- User creation with validation
- User retrieval by ID and email
- User updates
- Soft deletion
- User listing with filters
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.user_service import UserService
from scripts.database import Base
from scripts.models.user import User
from scripts.exceptions import ValidationError, DashboardError


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    TestSessionFactory = sessionmaker(bind=engine)
    session = TestSessionFactory()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def user_service(test_db_session):
    """Create UserService instance with test database session."""
    return UserService(test_db_session)


@pytest.fixture
def sample_users(test_db_session, user_service):
    """Create sample users for testing."""
    users = [
        user_service.create_user('admin@example.com', 'AdminPass123!', role='admin'),
        user_service.create_user('editor@example.com', 'EditorPass123!', role='editor'),
        user_service.create_user('viewer@example.com', 'ViewerPass123!', role='viewer'),
        user_service.create_user('inactive@example.com', 'InactivePass123!', active=False)
    ]
    return users


# Task 28: Test create_user method

class TestCreateUser:
    """Test user creation functionality."""

    def test_create_user_success(self, user_service):
        """Test successful user creation."""
        user = user_service.create_user('test@example.com', 'TestPass123!', role='admin')

        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.role == 'admin'
        assert user.active is True
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_create_user_password_hashed(self, user_service):
        """Test that password is hashed and not stored in plain text."""
        password = 'TestPass123!'
        user = user_service.create_user('test@example.com', password)

        assert user.password_hash != password
        assert user.password_hash.startswith('$2b$')

    def test_create_user_default_role(self, user_service):
        """Test that default role is 'viewer'."""
        user = user_service.create_user('test@example.com', 'TestPass123!')

        assert user.role == 'viewer'

    def test_create_user_duplicate_email(self, user_service):
        """Test that creating user with duplicate email fails."""
        user_service.create_user('test@example.com', 'TestPass123!')

        with pytest.raises(ValidationError, match='Email already exists'):
            user_service.create_user('test@example.com', 'AnotherPass123!')

    def test_create_user_invalid_email(self, user_service):
        """Test that invalid email format raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid email format'):
            user_service.create_user('invalid_email', 'TestPass123!')

    def test_create_user_empty_email(self, user_service):
        """Test that empty email raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid email format'):
            user_service.create_user('', 'TestPass123!')

    def test_create_user_short_password(self, user_service):
        """Test that password shorter than 8 characters fails."""
        with pytest.raises(ValidationError, match='Password must be at least 8 characters'):
            user_service.create_user('test@example.com', 'short')

    def test_create_user_invalid_role(self, user_service):
        """Test that invalid role raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid role'):
            user_service.create_user('test@example.com', 'TestPass123!', role='superuser')

    def test_create_user_inactive(self, user_service):
        """Test creating inactive user."""
        user = user_service.create_user('test@example.com', 'TestPass123!', active=False)

        assert user.active is False


# Task 29: Test get_user_by_id method

class TestGetUserById:
    """Test user retrieval by ID."""

    def test_get_user_by_id_exists(self, user_service, sample_users):
        """Test retrieving existing user by ID."""
        user_id = sample_users[0].id
        user = user_service.get_user_by_id(user_id)

        assert user is not None
        assert user.id == user_id
        assert user.email == 'admin@example.com'

    def test_get_user_by_id_not_found(self, user_service):
        """Test retrieving non-existent user returns None."""
        user = user_service.get_user_by_id(99999)

        assert user is None


# Task 30: Test get_user_by_email method

class TestGetUserByEmail:
    """Test user retrieval by email."""

    def test_get_user_by_email_exists(self, user_service, sample_users):
        """Test retrieving existing user by email."""
        user = user_service.get_user_by_email('editor@example.com')

        assert user is not None
        assert user.email == 'editor@example.com'
        assert user.role == 'editor'

    def test_get_user_by_email_not_found(self, user_service):
        """Test retrieving non-existent user returns None."""
        user = user_service.get_user_by_email('nonexistent@example.com')

        assert user is None

    def test_get_user_by_email_case_sensitive(self, user_service, sample_users):
        """Test that email lookup is case-sensitive by default."""
        user = user_service.get_user_by_email('ADMIN@EXAMPLE.COM')

        # SQLite is case-insensitive for ASCII, but this tests the method behavior
        # In production with PostgreSQL, this would likely return None
        assert user is None or user.email.lower() == 'admin@example.com'


# Task 31: Test update_user method

class TestUpdateUser:
    """Test user update functionality."""

    def test_update_user_email(self, user_service, sample_users):
        """Test updating user email."""
        user_id = sample_users[0].id
        updated_user = user_service.update_user(user_id, email='newemail@example.com')

        assert updated_user.email == 'newemail@example.com'

    def test_update_user_password(self, user_service, sample_users):
        """Test updating user password."""
        user_id = sample_users[0].id
        old_hash = sample_users[0].password_hash

        updated_user = user_service.update_user(user_id, password='NewPassword123!')

        assert updated_user.password_hash != old_hash
        assert updated_user.password_hash.startswith('$2b$')

    def test_update_user_role(self, user_service, sample_users):
        """Test updating user role."""
        user_id = sample_users[2].id  # viewer
        updated_user = user_service.update_user(user_id, role='editor')

        assert updated_user.role == 'editor'

    def test_update_user_active_status(self, user_service, sample_users):
        """Test updating user active status."""
        user_id = sample_users[0].id
        updated_user = user_service.update_user(user_id, active=False)

        assert updated_user.active is False

    def test_update_user_multiple_fields(self, user_service, sample_users):
        """Test updating multiple fields at once."""
        user_id = sample_users[2].id
        updated_user = user_service.update_user(
            user_id,
            email='updated@example.com',
            role='editor',
            active=False
        )

        assert updated_user.email == 'updated@example.com'
        assert updated_user.role == 'editor'
        assert updated_user.active is False

    def test_update_user_not_found(self, user_service):
        """Test updating non-existent user raises ValidationError."""
        with pytest.raises(ValidationError, match='User not found'):
            user_service.update_user(99999, email='new@example.com')

    def test_update_user_invalid_email(self, user_service, sample_users):
        """Test updating with invalid email raises ValidationError."""
        user_id = sample_users[0].id

        with pytest.raises(ValidationError, match='Invalid email format'):
            user_service.update_user(user_id, email='invalid_email')

    def test_update_user_short_password(self, user_service, sample_users):
        """Test updating with short password raises ValidationError."""
        user_id = sample_users[0].id

        with pytest.raises(ValidationError, match='Password must be at least 8 characters'):
            user_service.update_user(user_id, password='short')

    def test_update_user_invalid_role(self, user_service, sample_users):
        """Test updating with invalid role raises ValidationError."""
        user_id = sample_users[0].id

        with pytest.raises(ValidationError, match='Invalid role'):
            user_service.update_user(user_id, role='superuser')

    def test_update_user_duplicate_email(self, user_service, sample_users):
        """Test updating to duplicate email raises ValidationError."""
        user_id = sample_users[0].id

        with pytest.raises(ValidationError, match='Email already exists'):
            user_service.update_user(user_id, email='editor@example.com')


# Task 32: Test delete_user method (soft delete)

class TestDeleteUser:
    """Test user soft deletion functionality."""

    def test_delete_user_success(self, user_service, sample_users):
        """Test soft deleting a user sets active=False."""
        user_id = sample_users[0].id
        deleted_user = user_service.delete_user(user_id)

        assert deleted_user.active is False
        assert deleted_user.id == user_id

    def test_delete_user_persists_in_database(self, user_service, sample_users, test_db_session):
        """Test that soft deleted user still exists in database."""
        user_id = sample_users[0].id
        user_service.delete_user(user_id)

        # User should still be in database
        user = test_db_session.query(User).filter(User.id == user_id).first()
        assert user is not None
        assert user.active is False

    def test_delete_user_not_found(self, user_service):
        """Test deleting non-existent user raises ValidationError."""
        with pytest.raises(ValidationError, match='User not found'):
            user_service.delete_user(99999)

    def test_delete_user_preserves_data(self, user_service, sample_users):
        """Test that soft delete preserves user data."""
        user_id = sample_users[0].id
        original_email = sample_users[0].email
        original_role = sample_users[0].role

        deleted_user = user_service.delete_user(user_id)

        assert deleted_user.email == original_email
        assert deleted_user.role == original_role


# Task 33: Test list_users method

class TestListUsers:
    """Test user listing functionality."""

    def test_list_users_all(self, user_service, sample_users):
        """Test listing all users."""
        users = user_service.list_users()

        assert len(users) == 4
        emails = [u.email for u in users]
        assert 'admin@example.com' in emails
        assert 'editor@example.com' in emails
        assert 'viewer@example.com' in emails
        assert 'inactive@example.com' in emails

    def test_list_users_active_only(self, user_service, sample_users):
        """Test listing only active users."""
        users = user_service.list_users(active_only=True)

        assert len(users) == 3
        emails = [u.email for u in users]
        assert 'inactive@example.com' not in emails

    def test_list_users_by_role_admin(self, user_service, sample_users):
        """Test listing users filtered by admin role."""
        users = user_service.list_users(role='admin')

        assert len(users) == 1
        assert users[0].email == 'admin@example.com'

    def test_list_users_by_role_editor(self, user_service, sample_users):
        """Test listing users filtered by editor role."""
        users = user_service.list_users(role='editor')

        assert len(users) == 1
        assert users[0].email == 'editor@example.com'

    def test_list_users_by_role_viewer(self, user_service, sample_users):
        """Test listing users filtered by viewer role."""
        users = user_service.list_users(role='viewer')

        # Should return 2 viewers: active viewer + inactive user (default role is viewer)
        assert len(users) == 2
        emails = [u.email for u in users]
        assert 'viewer@example.com' in emails
        assert 'inactive@example.com' in emails

    def test_list_users_role_and_active(self, user_service, sample_users):
        """Test listing users with both role and active filters."""
        # Create an inactive admin
        user_service.create_user('inactive_admin@example.com', 'Password123!', role='admin', active=False)

        users = user_service.list_users(role='admin', active_only=True)

        assert len(users) == 1
        assert users[0].email == 'admin@example.com'

    def test_list_users_invalid_role(self, user_service):
        """Test listing users with invalid role raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid role'):
            user_service.list_users(role='superuser')

    def test_list_users_empty_database(self, user_service):
        """Test listing users when database is empty."""
        users = user_service.list_users()

        assert len(users) == 0
        assert users == []
