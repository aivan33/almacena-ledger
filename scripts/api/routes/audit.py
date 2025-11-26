"""
Audit log routes for security compliance and activity tracking.

Endpoints:
- GET /api/audit/logs - List audit logs (admin only)
- GET /api/audit/logs/user/<user_id> - Get logs for specific user
- GET /api/audit/logs/resource/<resource> - Get logs for specific resource
- GET /api/audit/logs/recent - Get recent activity
"""
from flask import Blueprint, request, jsonify

from scripts.database import get_session
from scripts.audit_service import AuditService
from scripts.api.app import require_auth, require_role
from scripts.logger_config import get_logger

logger = get_logger(__name__)

audit_bp = Blueprint('audit', __name__)


# Task 54: Audit routes
@audit_bp.route('/logs/user/<int:user_id>', methods=['GET'])
@require_auth
def get_user_audit_logs(user_id: int):
    """
    Get audit logs for specific user.

    Users can only view their own logs unless they are admin.

    Query parameters:
        - limit: Maximum number of logs (default: 100)
        - action: Filter by action type (optional)

    Response:
        {
            "logs": [
                {
                    "id": 1,
                    "user_id": 1,
                    "user_email": "user@example.com",
                    "action": "login",
                    "resource": null,
                    "timestamp": "2025-01-22T10:30:00Z"
                }
            ]
        }
    """
    current_user = request.current_user

    # Check permission (users can view their own logs, admins can view all)
    if current_user['user_id'] != user_id and current_user['role'] != 'admin':
        return jsonify({'error': 'Insufficient permissions'}), 403

    db_session = get_session()

    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        action_filter = request.args.get('action')

        # Get user logs
        audit_service = AuditService(db_session)
        logs = audit_service.get_user_audit_logs(
            user_id=user_id,
            limit=limit,
            action_filter=action_filter
        )

        return jsonify({
            'logs': [log.to_dict() for log in logs]
        }), 200

    finally:
        db_session.close()


@audit_bp.route('/logs/resource/<resource>', methods=['GET'])
@require_auth
@require_role('admin')
def get_resource_audit_logs(resource: str):
    """
    Get audit logs for specific resource (admin only).

    Query parameters:
        - resource_id: Filter by specific resource ID (optional)
        - limit: Maximum number of logs (default: 100)

    Response:
        {
            "logs": [
                {
                    "id": 2,
                    "user_id": 1,
                    "action": "create_user",
                    "resource": "user",
                    "resource_id": "5",
                    "timestamp": "2025-01-22T11:00:00Z"
                }
            ]
        }
    """
    db_session = get_session()

    try:
        # Get query parameters
        resource_id = request.args.get('resource_id')
        limit = request.args.get('limit', 100, type=int)

        # Get resource logs
        audit_service = AuditService(db_session)
        logs = audit_service.get_audit_logs_by_resource(
            resource=resource,
            resource_id=resource_id,
            limit=limit
        )

        return jsonify({
            'logs': [log.to_dict() for log in logs]
        }), 200

    finally:
        db_session.close()


@audit_bp.route('/logs/recent', methods=['GET'])
@require_auth
@require_role('admin')
def get_recent_activity():
    """
    Get recent activity across all users (admin only).

    Query parameters:
        - hours: Number of hours to look back (default: 24)
        - limit: Maximum number of logs (default: 100)

    Response:
        {
            "logs": [
                {
                    "id": 3,
                    "user_id": 2,
                    "user_email": "editor@example.com",
                    "action": "update_user",
                    "resource": "user",
                    "timestamp": "2025-01-22T14:30:00Z"
                }
            ]
        }
    """
    db_session = get_session()

    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Get recent activity
        audit_service = AuditService(db_session)
        logs = audit_service.get_recent_activity(hours=hours, limit=limit)

        return jsonify({
            'logs': [log.to_dict() for log in logs]
        }), 200

    finally:
        db_session.close()
