"""
User management routes for CRUD operations.

Endpoints:
- GET /api/users - List all users (admin only)
- POST /api/users - Create new user (admin only)
- GET /api/users/<id> - Get user by ID
- PUT /api/users/<id> - Update user
- DELETE /api/users/<id> - Delete user (soft delete, admin only)
"""
from flask import Blueprint, request, jsonify

from scripts.database import get_session
from scripts.user_service import UserService
from scripts.audit_service import AuditService
from scripts.api.app import require_auth, require_role
from scripts.logger_config import get_logger

logger = get_logger(__name__)

users_bp = Blueprint('users', __name__)


# Task 52: User management routes
@users_bp.route('', methods=['GET'])
@require_auth
@require_role('admin')
def list_users():
    """
    List all users (admin only).

    Query parameters:
        - role: Filter by role (optional)
        - active_only: Show only active users (optional, default: false)

    Response:
        {
            "users": [
                {
                    "id": 1,
                    "email": "user@example.com",
                    "role": "admin",
                    "active": true,
                    "created_at": "2025-01-01T00:00:00Z"
                }
            ]
        }
    """
    db_session = get_session()

    try:
        # Get query parameters
        role = request.args.get('role')
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        # List users
        user_service = UserService(db_session)
        users = user_service.list_users(role=role, active_only=active_only)

        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200

    finally:
        db_session.close()


@users_bp.route('', methods=['POST'])
@require_auth
@require_role('admin')
def create_user():
    """
    Create new user (admin only).

    Request:
        {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "role": "viewer",
            "active": true
        }

    Response:
        {
            "user": {
                "id": 2,
                "email": "newuser@example.com",
                "role": "viewer",
                "active": true
            }
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer')
    active = data.get('active', True)

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    db_session = get_session()

    try:
        # Create user
        user_service = UserService(db_session)
        user = user_service.create_user(email, password, role, active)

        # Log action
        current_user = request.current_user
        audit_service = AuditService(db_session)
        audit_service.log_action(
            user_id=current_user['user_id'],
            action='create_user',
            resource='user',
            resource_id=user.id,
            details={'email': email, 'role': role},
            ip_address=request.remote_addr
        )

        return jsonify({
            'user': user.to_dict()
        }), 201

    finally:
        db_session.close()


@users_bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id: int):
    """
    Get user by ID.

    Users can only view their own profile unless they are admin.

    Response:
        {
            "user": {
                "id": 1,
                "email": "user@example.com",
                "role": "admin",
                "active": true
            }
        }
    """
    current_user = request.current_user

    # Check permission (users can view their own profile, admins can view all)
    if current_user['user_id'] != user_id and current_user['role'] != 'admin':
        return jsonify({'error': 'Insufficient permissions'}), 403

    db_session = get_session()

    try:
        user_service = UserService(db_session)
        user = user_service.get_user_by_id(user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'user': user.to_dict()
        }), 200

    finally:
        db_session.close()


@users_bp.route('/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id: int):
    """
    Update user.

    Users can update their own profile (email, password only).
    Admins can update any user (including role, active status).

    Request:
        {
            "email": "newemail@example.com",  # optional
            "password": "newpassword123",     # optional
            "role": "editor",                  # optional (admin only)
            "active": false                    # optional (admin only)
        }

    Response:
        {
            "user": {
                "id": 1,
                "email": "newemail@example.com",
                "role": "editor",
                "active": false
            }
        }
    """
    current_user = request.current_user
    is_admin = current_user['role'] == 'admin'
    is_self = current_user['user_id'] == user_id

    # Check permission
    if not is_self and not is_admin:
        return jsonify({'error': 'Insufficient permissions'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    db_session = get_session()

    try:
        # Extract update fields
        email = data.get('email')
        password = data.get('password')
        role = data.get('role') if is_admin else None
        active = data.get('active') if is_admin else None

        # Update user
        user_service = UserService(db_session)
        user = user_service.update_user(
            user_id,
            email=email,
            password=password,
            role=role,
            active=active
        )

        # Log action
        audit_service = AuditService(db_session)
        audit_service.log_action(
            user_id=current_user['user_id'],
            action='update_user',
            resource='user',
            resource_id=user_id,
            details=data,
            ip_address=request.remote_addr
        )

        return jsonify({
            'user': user.to_dict()
        }), 200

    finally:
        db_session.close()


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_auth
@require_role('admin')
def delete_user(user_id: int):
    """
    Delete user (soft delete, admin only).

    Sets user.active = False instead of removing from database.

    Response:
        {
            "message": "User deleted successfully",
            "user": {
                "id": 1,
                "email": "deleted@example.com",
                "active": false
            }
        }
    """
    db_session = get_session()

    try:
        # Delete user (soft delete)
        user_service = UserService(db_session)
        user = user_service.delete_user(user_id)

        # Log action
        current_user = request.current_user
        audit_service = AuditService(db_session)
        audit_service.log_action(
            user_id=current_user['user_id'],
            action='delete_user',
            resource='user',
            resource_id=user_id,
            details={'email': user.email},
            ip_address=request.remote_addr
        )

        return jsonify({
            'message': 'User deleted successfully',
            'user': user.to_dict()
        }), 200

    finally:
        db_session.close()
