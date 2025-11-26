"""
Unit tests for authentication and authorization functionality.

Tests cover:
- Password hashing and verification
- JWT token creation and verification
- AuthService authentication flow
- Account lockout mechanism
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from scripts.auth import hash_password, verify_password, create_token, verify_token, AuthService
from scripts.database import Base
from scripts.models.user import User
from scripts.exceptions import (
    AuthenticationError,
    SessionExpiredError,
    AccountLockedError
)
from scripts.constants import (
    MAX_LOGIN_ATTEMPTS,
    ACCOUNT_LOCKOUT_MINUTES,
    TOKEN_EXPIRY_HOURS
)


# Task 24: Test fixtures for database and users

@pytest.fixture
def test_db_session():
    """
    Create an in-memory SQLite database session for testing.

    Creates a fresh database with all tables for each test,
    and automatically cleans up after the test completes.
    """
    # Create in-memory SQLite database
    engine = create_engine('sqlite:///:memory:', echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    TestSessionFactory = sessionmaker(bind=engine)
    session = TestSessionFactory()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(test_db_session):
    """
    Create a test user with known credentials.

    Email: test@example.com
    Password: TestPassword123!
    Role: admin
    """
    user = User(
        email='test@example.com',
        password_hash=hash_password('TestPassword123!'),
        role='admin',
        active=True,
        failed_login_attempts=0,
        locked_until=None
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def locked_user(test_db_session):
    """
    Create a locked test user (account locked until future time).
    """
    user = User(
        email='locked@example.com',
        password_hash=hash_password('LockedPassword123!'),
        role='viewer',
        active=True,
        failed_login_attempts=MAX_LOGIN_ATTEMPTS,
        locked_until=datetime.utcnow() + timedelta(minutes=10)
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def inactive_user(test_db_session):
    """
    Create an inactive test user.
    """
    user = User(
        email='inactive@example.com',
        password_hash=hash_password('InactivePassword123!'),
        role='viewer',
        active=False,
        failed_login_attempts=0,
        locked_until=None
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return user


@pytest.fixture
def mock_logger():
    """Mock logger for testing without actual log output."""
    return Mock()


@pytest.fixture
def auth_service(test_db_session, mock_logger):
    """Create AuthService instance with test database session."""
    return AuthService(test_db_session, mock_logger)


# Task 25: Unit tests for password hashing

class TestPasswordHashing:
    """Test password hashing and verification functions."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = 'TestPassword123!'
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_outputs(self):
        """Test that same password produces different hashes (due to salt)."""
        password = 'TestPassword123!'
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts produce different hashes

    def test_hash_password_contains_bcrypt_prefix(self):
        """Test that hashed password starts with bcrypt identifier."""
        password = 'TestPassword123!'
        hashed = hash_password(password)

        assert hashed.startswith('$2b$')  # Bcrypt hash identifier

    def test_verify_password_correct(self):
        """Test that correct password verification succeeds."""
        password = 'TestPassword123!'
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that incorrect password verification fails."""
        password = 'TestPassword123!'
        wrong_password = 'WrongPassword456!'
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test that empty password verification fails."""
        password = 'TestPassword123!'
        hashed = hash_password(password)

        assert verify_password('', hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test that verification with invalid hash returns False."""
        password = 'TestPassword123!'
        invalid_hash = 'not_a_valid_bcrypt_hash'

        assert verify_password(password, invalid_hash) is False

    def test_hash_password_special_characters(self):
        """Test that passwords with special characters are hashed correctly."""
        password = 'P@ssw0rd!#$%^&*()'
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Test that passwords with unicode characters are hashed correctly."""
        password = 'Пароль123!مرحبا'
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


# Task 26: Unit tests for JWT tokens

class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_token_returns_dict(self):
        """Test that create_token returns a dictionary with required keys."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')

        assert isinstance(token_data, dict)
        assert 'token' in token_data
        assert 'expires_at' in token_data

    def test_create_token_contains_jwt(self):
        """Test that token is a valid JWT string."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')
        token = token_data['token']

        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts: header.payload.signature

    def test_create_token_expiry_format(self):
        """Test that expires_at is in ISO format."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')
        expires_at = token_data['expires_at']

        # Should be parseable as ISO format
        datetime.fromisoformat(expires_at)

    def test_verify_token_valid(self):
        """Test that valid token verification succeeds."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')
        token = token_data['token']

        payload = verify_token(token)

        assert payload['user_id'] == 1
        assert payload['email'] == 'test@example.com'
        assert payload['role'] == 'admin'
        assert 'exp' in payload
        assert 'iat' in payload

    def test_verify_token_contains_all_claims(self):
        """Test that decoded payload contains all required claims."""
        token_data = create_token(user_id=42, email='user@example.com', role='viewer')
        token = token_data['token']

        payload = verify_token(token)

        assert payload['user_id'] == 42
        assert payload['email'] == 'user@example.com'
        assert payload['role'] == 'viewer'

    def test_verify_token_invalid_format(self):
        """Test that invalid token format raises AuthenticationError."""
        with pytest.raises(AuthenticationError, match='Invalid authentication token'):
            verify_token('not.a.valid.jwt.token')

    def test_verify_token_invalid_signature(self):
        """Test that token with invalid signature raises AuthenticationError."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')
        token = token_data['token']

        # Tamper with the signature
        parts = token.split('.')
        parts[2] = 'invalid_signature'
        tampered_token = '.'.join(parts)

        with pytest.raises(AuthenticationError, match='Invalid authentication token'):
            verify_token(tampered_token)

    def test_verify_token_expired(self):
        """Test that expired token raises SessionExpiredError."""
        import jwt
        from scripts.constants import JWT_SECRET_KEY, JWT_ALGORITHM

        # Create expired token (expired 1 hour ago)
        expired_payload = {
            'user_id': 1,
            'email': 'test@example.com',
            'role': 'admin',
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        with pytest.raises(SessionExpiredError, match='Your session has expired'):
            verify_token(expired_token)

    def test_token_expiry_time(self):
        """Test that token expires at the correct time (24 hours)."""
        token_data = create_token(user_id=1, email='test@example.com', role='admin')
        expires_at = datetime.fromisoformat(token_data['expires_at'])

        # Token should expire approximately TOKEN_EXPIRY_HOURS from now
        expected_expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        time_diff = abs((expires_at - expected_expiry).total_seconds())

        # Allow 5 seconds tolerance for test execution time
        assert time_diff < 5


# Tasks 19-23: AuthService authentication flow tests

class TestAuthService:
    """Test AuthService authentication methods."""

    def test_authenticate_success(self, auth_service, test_user):
        """Test successful authentication with correct credentials."""
        result = auth_service.authenticate('test@example.com', 'TestPassword123!')

        assert 'token' in result
        assert 'expires_at' in result
        assert 'user' in result
        assert result['user']['email'] == 'test@example.com'
        assert result['user']['role'] == 'admin'

    def test_authenticate_updates_last_login(self, auth_service, test_user, test_db_session):
        """Test that successful authentication updates last_login timestamp."""
        before_login = test_user.last_login

        auth_service.authenticate('test@example.com', 'TestPassword123!')

        test_db_session.refresh(test_user)
        assert test_user.last_login is not None
        assert test_user.last_login != before_login

    def test_authenticate_resets_failed_attempts(self, auth_service, test_db_session):
        """Test that successful authentication resets failed login counter."""
        # Create user with failed attempts
        user = User(
            email='faileduser@example.com',
            password_hash=hash_password('Password123!'),
            role='viewer',
            active=True,
            failed_login_attempts=3
        )
        test_db_session.add(user)
        test_db_session.commit()

        auth_service.authenticate('faileduser@example.com', 'Password123!')

        test_db_session.refresh(user)
        assert user.failed_login_attempts == 0

    def test_authenticate_invalid_email(self, auth_service):
        """Test authentication with non-existent email."""
        with pytest.raises(AuthenticationError, match='Invalid email or password'):
            auth_service.authenticate('nonexistent@example.com', 'Password123!')

    def test_authenticate_invalid_password(self, auth_service, test_user):
        """Test authentication with incorrect password."""
        with pytest.raises(AuthenticationError, match='Invalid email or password'):
            auth_service.authenticate('test@example.com', 'WrongPassword!')

    def test_authenticate_increments_failed_attempts(self, auth_service, test_user, test_db_session):
        """Test that failed authentication increments failed_login_attempts."""
        initial_attempts = test_user.failed_login_attempts

        with pytest.raises(AuthenticationError):
            auth_service.authenticate('test@example.com', 'WrongPassword!')

        test_db_session.refresh(test_user)
        assert test_user.failed_login_attempts == initial_attempts + 1

    def test_authenticate_locks_after_max_attempts(self, auth_service, test_user, test_db_session):
        """Test that account locks after MAX_LOGIN_ATTEMPTS failed attempts."""
        # Make MAX_LOGIN_ATTEMPTS - 1 failed attempts
        for i in range(MAX_LOGIN_ATTEMPTS - 1):
            with pytest.raises(AuthenticationError):
                auth_service.authenticate('test@example.com', 'WrongPassword!')

        # Next attempt should lock the account
        with pytest.raises(AccountLockedError, match='Account locked'):
            auth_service.authenticate('test@example.com', 'WrongPassword!')

        test_db_session.refresh(test_user)
        assert test_user.locked_until is not None
        assert test_user.locked_until > datetime.utcnow()

    def test_authenticate_locked_account(self, auth_service, locked_user):
        """Test authentication with locked account."""
        with pytest.raises(AccountLockedError, match='Account is locked'):
            auth_service.authenticate('locked@example.com', 'LockedPassword123!')

    def test_authenticate_expired_lockout(self, auth_service, test_db_session):
        """Test that expired lockout is automatically cleared."""
        # Create user with expired lockout
        user = User(
            email='expiredlock@example.com',
            password_hash=hash_password('Password123!'),
            role='viewer',
            active=True,
            failed_login_attempts=MAX_LOGIN_ATTEMPTS,
            locked_until=datetime.utcnow() - timedelta(minutes=1)  # Expired 1 minute ago
        )
        test_db_session.add(user)
        test_db_session.commit()

        # Should succeed and clear lockout
        result = auth_service.authenticate('expiredlock@example.com', 'Password123!')

        assert 'token' in result
        test_db_session.refresh(user)
        assert user.locked_until is None
        assert user.failed_login_attempts == 0

    def test_authenticate_inactive_account(self, auth_service, inactive_user):
        """Test authentication with inactive account."""
        with pytest.raises(AuthenticationError, match='Account is inactive'):
            auth_service.authenticate('inactive@example.com', 'InactivePassword123!')

    def test_authenticate_sql_injection_protection(self, auth_service, test_user):
        """Test that SQL injection attempts are safely handled."""
        # Try SQL injection in email field
        with pytest.raises(AuthenticationError):
            auth_service.authenticate("test@example.com' OR '1'='1", 'Password123!')

        # Try SQL injection in password field (will fail password check)
        with pytest.raises(AuthenticationError):
            auth_service.authenticate('test@example.com', "' OR '1'='1")

    def test_authenticate_logs_events(self, auth_service, test_user, mock_logger):
        """Test that authentication events are logged."""
        # Successful login
        auth_service.authenticate('test@example.com', 'TestPassword123!')

        # Check that info log was called for successful login
        mock_logger.info.assert_called()
        assert any('Successful login' in str(call) for call in mock_logger.info.call_args_list)
