"""
Flask application factory and configuration.

Creates and configures the Flask application with routes,
error handlers, middleware, and CORS support.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
from typing import Callable

from scripts.database import get_session, init_db
from scripts.auth import verify_token
from scripts.exceptions import (
    DashboardError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    SessionExpiredError,
    AccountLockedError,
    PermissionDeniedError
)
from scripts.logger_config import get_logger

logger = get_logger(__name__)


# Task 56: Authentication middleware decorator
def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for routes.

    Checks for JWT token in Authorization header or cookies.
    Attaches user payload to request.current_user.

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user = request.current_user
            return {'message': f'Hello {user["email"]}'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Check Authorization header (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # Check cookies as fallback
        if not token:
            token = request.cookies.get('auth_token')

        if not token:
            logger.warning(f"Missing authentication token for {request.path}")
            return jsonify({'error': 'Authentication required'}), 401

        try:
            # Verify token and attach user to request
            payload = verify_token(token)
            request.current_user = payload

            logger.debug(f"Authenticated user: {payload['email']}")
            return f(*args, **kwargs)

        except SessionExpiredError as e:
            logger.warning(f"Expired token for {request.path}: {e}")
            return jsonify({'error': str(e)}), 401
        except AuthenticationError as e:
            logger.warning(f"Invalid token for {request.path}: {e}")
            return jsonify({'error': str(e)}), 401

    return decorated_function


# Task 57: Role-based authorization decorator
def require_role(*roles: str) -> Callable:
    """
    Decorator to require specific role(s) for routes.

    Must be used with @require_auth decorator.

    Args:
        *roles: One or more required roles (e.g., 'admin', 'editor')

    Usage:
        @app.route('/admin')
        @require_auth
        @require_role('admin')
        def admin_route():
            return {'message': 'Admin access'}
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(request, 'current_user', None)

            if not user:
                logger.error("require_role used without require_auth")
                return jsonify({'error': 'Authentication required'}), 401

            user_role = user.get('role')

            if user_role not in roles:
                logger.warning(
                    f"User {user.get('email')} with role '{user_role}' "
                    f"attempted to access route requiring {roles}"
                )
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': list(roles)
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# Task 49: Flask app factory
def create_app(config: dict = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Default configuration
    app.config.update({
        'SECRET_KEY': 'dev-secret-key-CHANGE-IN-PRODUCTION',
        'JSON_SORT_KEYS': False,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
    })

    # Apply custom configuration
    if config:
        app.config.update(config)

    # Task 59: Configure CORS
    CORS(app,
         origins=['http://localhost:5173', 'http://localhost:3000'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

    # Initialize database
    init_db()

    # Task 55: Register global error handlers
    register_error_handlers(app)

    # Task 50: Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'service': 'almacena-dashboard-api',
            'version': '1.0.0'
        }), 200

    # Task 58: Register blueprints
    from scripts.api.routes.auth import auth_bp
    from scripts.api.routes.users import users_bp
    from scripts.api.routes.validation import validation_bp
    from scripts.api.routes.audit import audit_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(validation_bp, url_prefix='/api/validation')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')

    logger.info("Flask application created successfully")

    return app


# Task 55: Global error handlers
def register_error_handlers(app: Flask) -> None:
    """Register global error handlers for the Flask application."""

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors (400 Bad Request)."""
        logger.warning(f"Validation error: {error}")
        return jsonify({'error': str(error)}), 400

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors (401 Unauthorized)."""
        logger.warning(f"Authentication error: {error}")
        return jsonify({'error': str(error)}), 401

    @app.errorhandler(SessionExpiredError)
    def handle_session_expired_error(error):
        """Handle session expired errors (401 Unauthorized)."""
        logger.warning(f"Session expired: {error}")
        return jsonify({'error': str(error)}), 401

    @app.errorhandler(AccountLockedError)
    def handle_account_locked_error(error):
        """Handle account locked errors (403 Forbidden)."""
        logger.warning(f"Account locked: {error}")
        return jsonify({'error': str(error)}), 403

    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        """Handle authorization errors (403 Forbidden)."""
        logger.warning(f"Authorization error: {error}")
        return jsonify({'error': str(error)}), 403

    @app.errorhandler(PermissionDeniedError)
    def handle_permission_denied_error(error):
        """Handle permission denied errors (403 Forbidden)."""
        logger.warning(f"Permission denied: {error}")
        return jsonify({'error': str(error)}), 403

    @app.errorhandler(DashboardError)
    def handle_dashboard_error(error):
        """Handle general dashboard errors (500 Internal Server Error)."""
        logger.error(f"Dashboard error: {error}")
        return jsonify({'error': 'An internal error occurred'}), 500

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({'error': 'Method not allowed'}), 405

    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        """Handle 413 Request Entity Too Large errors."""
        return jsonify({'error': 'Request payload too large'}), 413

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'An internal error occurred'}), 500
