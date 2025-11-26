"""
Audit logging service for security compliance and user action tracking.

Logs user actions, provides audit trail retrieval, and manages log retention.
"""
import json
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from scripts.models.audit_log import AuditLog
from scripts.exceptions import DashboardError
from scripts.logger_config import get_logger

logger = get_logger(__name__)


class AuditService:
    """
    Audit logging service for security compliance.

    Handles logging of user actions, audit trail retrieval,
    and cleanup of old audit logs.

    Args:
        db_session: SQLAlchemy database session
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def log_action(
        self,
        user_id: int,
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user action to the audit trail.

        Args:
            user_id: ID of user performing the action
            action: Action performed (e.g., 'login', 'create_user', 'update_data')
            resource: Resource type affected (e.g., 'user', 'validation_report')
            resource_id: ID of affected resource
            details: Additional context as dictionary (will be JSON serialized)
            ip_address: IP address of the request

        Returns:
            AuditLog: Created audit log entry

        Raises:
            DashboardError: If database operation fails
        """
        try:
            # Serialize details to JSON if provided
            details_json = json.dumps(details) if details else None

            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=str(resource_id) if resource_id is not None else None,
                details=details_json,
                ip_address=ip_address
            )

            self.db_session.add(audit_log)
            self.db_session.commit()
            self.db_session.refresh(audit_log)

            logger.debug(
                f"Audit log created: user_id={user_id}, action={action}, "
                f"resource={resource}, resource_id={resource_id}"
            )

            return audit_log

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to create audit log: {e}")
            raise DashboardError(f'Failed to create audit log: {str(e)}')

    def get_user_audit_logs(
        self,
        user_id: int,
        limit: int = 100,
        action_filter: Optional[str] = None
    ) -> List[AuditLog]:
        """
        Retrieve audit logs for a specific user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of logs to return (default: 100)
            action_filter: Optional action type filter

        Returns:
            List of AuditLog objects (most recent first)

        Raises:
            DashboardError: If database operation fails
        """
        try:
            query = self.db_session.query(AuditLog).filter(AuditLog.user_id == user_id)

            # Filter by action if provided
            if action_filter:
                query = query.filter(AuditLog.action == action_filter)

            # Order by timestamp (most recent first) and limit
            logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()

            logger.debug(f"Retrieved {len(logs)} audit logs for user {user_id}")
            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve user audit logs: {e}")
            raise DashboardError(f'Failed to retrieve user audit logs: {str(e)}')

    def get_audit_logs_by_resource(
        self,
        resource: str,
        resource_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Retrieve audit logs for a specific resource.

        Args:
            resource: Resource type (e.g., 'user', 'validation_report')
            resource_id: Optional specific resource ID
            limit: Maximum number of logs to return (default: 100)

        Returns:
            List of AuditLog objects (most recent first)

        Raises:
            DashboardError: If database operation fails
        """
        try:
            query = self.db_session.query(AuditLog).filter(AuditLog.resource == resource)

            # Filter by specific resource ID if provided
            if resource_id is not None:
                query = query.filter(AuditLog.resource_id == str(resource_id))

            # Order by timestamp (most recent first) and limit
            logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()

            logger.debug(
                f"Retrieved {len(logs)} audit logs for resource {resource}"
                + (f" (ID: {resource_id})" if resource_id else "")
            )
            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve resource audit logs: {e}")
            raise DashboardError(f'Failed to retrieve resource audit logs: {str(e)}')

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Delete audit logs older than specified number of days.

        Args:
            days_to_keep: Number of days to retain logs (default: 90)

        Returns:
            int: Number of logs deleted

        Raises:
            DashboardError: If database operation fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Query old logs
            old_logs = self.db_session.query(AuditLog).filter(
                AuditLog.timestamp < cutoff_date
            )

            # Count before deletion
            count = old_logs.count()

            # Delete old logs
            old_logs.delete(synchronize_session=False)
            self.db_session.commit()

            logger.info(f"Deleted {count} audit logs older than {days_to_keep} days")
            return count

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to cleanup old audit logs: {e}")
            raise DashboardError(f'Failed to cleanup old audit logs: {str(e)}')

    def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent activity from the last N hours.

        Args:
            hours: Number of hours to look back (default: 24)
            limit: Maximum number of logs to return (default: 100)

        Returns:
            List of AuditLog objects (most recent first)

        Raises:
            DashboardError: If database operation fails
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            logs = (
                self.db_session.query(AuditLog)
                .filter(AuditLog.timestamp >= cutoff_time)
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
                .all()
            )

            logger.debug(f"Retrieved {len(logs)} audit logs from last {hours} hours")
            return logs

        except Exception as e:
            logger.error(f"Failed to retrieve recent activity: {e}")
            raise DashboardError(f'Failed to retrieve recent activity: {str(e)}')
