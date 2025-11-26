"""
Authentication routes for login, logout, and token verification.

Endpoints:
- POST /api/auth/login - Authenticate user and get JWT token
- POST /api/auth/logout - Invalidate current session
- GET /api/auth/verify - Verify current token validity
"""
from flask import Blueprint, request, jsonify, make_response

from scripts.database import get_session
from scripts.auth import AuthService
from scripts.audit_service import AuditService
from scripts.api.app import require_auth
from scripts.logger_config import get_logger

logger = get_logger(__name__)

auth_bp = Blueprint('auth', __name__)


# Task 51: Authentication routes
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.

    Request:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Response:
        {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
            "expires_at": "2025-01-23T10:30:00Z",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "role": "admin"
            }
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db_session = get_session()

    try:
        # Authenticate user
        auth_service = AuthService(db_session, logger)
        result = auth_service.authenticate(email, password)

        # Log successful login
        audit_service = AuditService(db_session)
        audit_service.log_action(
            user_id=result['user']['id'],
            action='login',
            ip_address=request.remote_addr
        )

        # Create response with token in HTTP-only cookie
        response = make_response(jsonify({
            'token': result['token'],
            'expires_at': result['expires_at'],
            'user': result['user']
        }), 200)

        # Set HTTP-only cookie for web clients
        response.set_cookie(
            'auth_token',
            result['token'],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            max_age=24 * 60 * 60  # 24 hours
        )

        logger.info(f"User logged in: {email}")
        return response

    except Exception as e:
        # Log failed login attempt (if it's not a non-existent user)
        logger.warning(f"Login failed for {email}: {str(e)}")
        raise
    finally:
        db_session.close()


@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout user by clearing authentication cookie.

    Response:
        {
            "message": "Logged out successfully"
        }
    """
    db_session = get_session()

    try:
        user = request.current_user

        # Log logout action
        audit_service = AuditService(db_session)
        audit_service.log_action(
            user_id=user['user_id'],
            action='logout',
            ip_address=request.remote_addr
        )

        # Create response that clears the auth cookie
        response = make_response(jsonify({
            'message': 'Logged out successfully'
        }), 200)

        response.set_cookie(
            'auth_token',
            '',
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=0  # Expire immediately
        )

        logger.info(f"User logged out: {user['email']}")
        return response

    finally:
        db_session.close()


@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify():
    """
    Verify current authentication token.

    Response:
        {
            "valid": true,
            "user": {
                "user_id": 1,
                "email": "user@example.com",
                "role": "admin"
            }
        }
    """
    user = request.current_user

    return jsonify({
        'valid': True,
        'user': {
            'user_id': user['user_id'],
            'email': user['email'],
            'role': user['role']
        }
    }), 200
