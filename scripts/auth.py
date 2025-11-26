"""Authentication and authorization utilities."""

import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from scripts.logger_config import get_logger
from scripts.constants import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    TOKEN_EXPIRY_HOURS,
    MAX_LOGIN_ATTEMPTS,
    ACCOUNT_LOCKOUT_MINUTES
)
from scripts.exceptions import (
    AuthenticationError,
    SessionExpiredError,
    AccountLockedError
)

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with 12 rounds.

    Args:
        password: Plain text password

    Returns:
        str: Bcrypt hash as UTF-8 string

    Example:
        >>> hashed = hash_password('mypassword123')
        >>> len(hashed) > 50
        True
    """
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify password against bcrypt hash.

    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to compare against

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_token(user_id: int, email: str, role: str) -> dict:
    """
    Generate JWT token for user.

    Args:
        user_id: User ID
        email: User email
        role: User role

    Returns:
        dict: {'token': str, 'expires_at': str (ISO format)}
    """
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': expires_at,
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    logger.info(f"Token created for user {email} (expires: {expires_at})")

    return {
        'token': token,
        'expires_at': expires_at.isoformat()
    }


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload (user_id, email, role, exp, iat)

    Raises:
        SessionExpiredError: If token expired
        AuthenticationError: If token invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise SessionExpiredError('Your session has expired. Please log in again.')
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f'Invalid authentication token: {str(e)}')


class AuthService:
    """
    Authentication and session management service.

    Handles user authentication, account lockout enforcement,
    password verification, and JWT token generation.

    Args:
        db_session: SQLAlchemy database session
        logger: Logger instance for audit trail
    """

    def __init__(self, db_session: Session, logger):
        self.db_session = db_session
        self.logger = logger

    def authenticate(self, email: str, password: str) -> dict:
        """
        Authenticate user with email and password.

        Performs the following checks:
        1. Lookup user by email (SQL injection protected)
        2. Check account lockout status
        3. Verify password
        4. Track failed login attempts
        5. Generate JWT token on success

        Args:
            email: User email address
            password: Plain text password

        Returns:
            dict: {'token': str, 'expires_at': str, 'user': dict}

        Raises:
            AuthenticationError: If credentials are invalid
            AccountLockedError: If account is locked due to failed attempts
        """
        from scripts.models.user import User

        # Task 20: User lookup with SQL injection protection (parameterized query)
        user = self.db_session.query(User).filter(User.email == email).first()

        if not user:
            self.logger.warning(f"Login attempt for non-existent user: {email}")
            raise AuthenticationError('Invalid email or password')

        if not user.active:
            self.logger.warning(f"Login attempt for inactive user: {email}")
            raise AuthenticationError('Account is inactive')

        # Task 21: Check account lockout status
        if user.locked_until:
            if datetime.utcnow() < user.locked_until:
                remaining_minutes = (user.locked_until - datetime.utcnow()).seconds // 60
                self.logger.warning(f"Login attempt for locked account: {email}")
                raise AccountLockedError(
                    f'Account is locked. Try again in {remaining_minutes} minutes.'
                )
            else:
                # Lockout period expired, reset lockout
                user.locked_until = None
                user.failed_login_attempts = 0
                self.db_session.commit()
                self.logger.info(f"Account lockout expired for user: {email}")

        # Task 22: Verify password and track failed attempts
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1

            # Lock account after MAX_LOGIN_ATTEMPTS failures
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCKOUT_MINUTES)
                self.db_session.commit()
                self.logger.warning(
                    f"Account locked due to {MAX_LOGIN_ATTEMPTS} failed attempts: {email}"
                )
                raise AccountLockedError(
                    f'Account locked after {MAX_LOGIN_ATTEMPTS} failed attempts. '
                    f'Try again in {ACCOUNT_LOCKOUT_MINUTES} minutes.'
                )

            self.db_session.commit()
            self.logger.warning(
                f"Failed login attempt {user.failed_login_attempts}/{MAX_LOGIN_ATTEMPTS} for: {email}"
            )
            raise AuthenticationError('Invalid email or password')

        # Task 23: Successful login - reset counters and generate token
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        self.db_session.commit()

        # Generate JWT token
        token_data = create_token(user.id, user.email, user.role)

        self.logger.info(f"Successful login for user: {email}")

        return {
            'token': token_data['token'],
            'expires_at': token_data['expires_at'],
            'user': user.to_dict()
        }
