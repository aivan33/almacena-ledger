"""
Unit tests for AuditService security logging.

Tests cover:
- Action logging
- User audit log retrieval
- Resource audit log retrieval
- Old log cleanup
- Recent activity retrieval
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.audit_service import AuditService
from scripts.database import Base
from scripts.models.user import User
from scripts.models.audit_log import AuditLog
from scripts.exceptions import DashboardError
from scripts.auth import hash_password


@pytest.fixture
def test_db_session():
    """Create an in-memory SQLite database session for testing."""
    # Import all models to register them with Base.metadata
    from scripts.models.user import User
    from scripts.models.audit_log import AuditLog
    from scripts.models.validation_report import ValidationReport

    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    TestSessionFactory = sessionmaker(bind=engine)
    session = TestSessionFactory()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(test_db_session):
    """Create a test user."""
    user = User(
        email='test@example.com',
        password_hash=hash_password('TestPassword123!'),
        role='admin',
        active=True
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def audit_service(test_db_session):
    """Create AuditService instance with test database session."""
    return AuditService(test_db_session)


# Task 45: Test log_action method

class TestLogAction:
    """Test action logging functionality."""

    def test_log_simple_action(self, audit_service, test_user):
        """Test logging a simple action."""
        log = audit_service.log_action(
            user_id=test_user.id,
            action='login'
        )

        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.action == 'login'
        assert log.resource is None
        assert log.resource_id is None
        assert log.details is None

    def test_log_action_with_resource(self, audit_service, test_user):
        """Test logging an action with resource information."""
        log = audit_service.log_action(
            user_id=test_user.id,
            action='create_user',
            resource='user',
            resource_id=123
        )

        assert log.action == 'create_user'
        assert log.resource == 'user'
        assert log.resource_id == '123'

    def test_log_action_with_details(self, audit_service, test_user):
        """Test logging an action with additional details."""
        details = {'old_email': 'old@example.com', 'new_email': 'new@example.com'}

        log = audit_service.log_action(
            user_id=test_user.id,
            action='update_user',
            resource='user',
            resource_id=456,
            details=details
        )

        assert log.details is not None
        # Details should be stored as JSON string
        import json
        stored_details = json.loads(log.details)
        assert stored_details == details

    def test_log_action_with_ip_address(self, audit_service, test_user):
        """Test logging an action with IP address."""
        log = audit_service.log_action(
            user_id=test_user.id,
            action='login',
            ip_address='192.168.1.100'
        )

        assert log.ip_address == '192.168.1.100'

    def test_log_action_has_timestamp(self, audit_service, test_user):
        """Test that logged action has automatic timestamp."""
        before = datetime.utcnow()
        log = audit_service.log_action(user_id=test_user.id, action='test')
        after = datetime.utcnow()

        assert log.timestamp is not None
        assert before <= log.timestamp <= after


# Task 46: Test get_user_audit_logs method

class TestGetUserAuditLogs:
    """Test user audit log retrieval."""

    def test_get_user_logs_empty(self, audit_service, test_user):
        """Test retrieving logs for user with no activity."""
        logs = audit_service.get_user_audit_logs(test_user.id)

        assert len(logs) == 0

    def test_get_user_logs_single(self, audit_service, test_user):
        """Test retrieving logs for user with one action."""
        audit_service.log_action(test_user.id, 'login')

        logs = audit_service.get_user_audit_logs(test_user.id)

        assert len(logs) == 1
        assert logs[0].action == 'login'

    def test_get_user_logs_multiple(self, audit_service, test_user):
        """Test retrieving multiple logs for same user."""
        audit_service.log_action(test_user.id, 'login')
        audit_service.log_action(test_user.id, 'create_user')
        audit_service.log_action(test_user.id, 'logout')

        logs = audit_service.get_user_audit_logs(test_user.id)

        assert len(logs) == 3

    def test_get_user_logs_ordered_by_time(self, audit_service, test_user):
        """Test that logs are ordered by timestamp (most recent first)."""
        log1 = audit_service.log_action(test_user.id, 'first')
        log2 = audit_service.log_action(test_user.id, 'second')
        log3 = audit_service.log_action(test_user.id, 'third')

        logs = audit_service.get_user_audit_logs(test_user.id)

        # Should be in reverse order (most recent first)
        assert logs[0].id == log3.id
        assert logs[1].id == log2.id
        assert logs[2].id == log1.id

    def test_get_user_logs_with_limit(self, audit_service, test_user):
        """Test limiting number of returned logs."""
        for i in range(10):
            audit_service.log_action(test_user.id, f'action_{i}')

        logs = audit_service.get_user_audit_logs(test_user.id, limit=5)

        assert len(logs) == 5

    def test_get_user_logs_with_action_filter(self, audit_service, test_user):
        """Test filtering logs by action type."""
        audit_service.log_action(test_user.id, 'login')
        audit_service.log_action(test_user.id, 'create_user')
        audit_service.log_action(test_user.id, 'login')
        audit_service.log_action(test_user.id, 'logout')

        logs = audit_service.get_user_audit_logs(test_user.id, action_filter='login')

        assert len(logs) == 2
        assert all(log.action == 'login' for log in logs)

    def test_get_user_logs_different_users(self, audit_service, test_db_session):
        """Test that logs are filtered by user."""
        user1 = User(email='user1@example.com', password_hash=hash_password('Pass123!'), role='viewer')
        user2 = User(email='user2@example.com', password_hash=hash_password('Pass123!'), role='viewer')
        test_db_session.add_all([user1, user2])
        test_db_session.commit()

        audit_service.log_action(user1.id, 'action1')
        audit_service.log_action(user2.id, 'action2')
        audit_service.log_action(user1.id, 'action3')

        logs = audit_service.get_user_audit_logs(user1.id)

        assert len(logs) == 2
        assert all(log.user_id == user1.id for log in logs)


# Task 47: Test get_audit_logs_by_resource method

class TestGetAuditLogsByResource:
    """Test resource audit log retrieval."""

    def test_get_resource_logs_empty(self, audit_service):
        """Test retrieving logs for resource with no activity."""
        logs = audit_service.get_audit_logs_by_resource('user')

        assert len(logs) == 0

    def test_get_resource_logs_single_type(self, audit_service, test_user):
        """Test retrieving logs for specific resource type."""
        audit_service.log_action(test_user.id, 'create', resource='user', resource_id=1)
        audit_service.log_action(test_user.id, 'update', resource='user', resource_id=2)
        audit_service.log_action(test_user.id, 'delete', resource='report', resource_id=1)

        logs = audit_service.get_audit_logs_by_resource('user')

        assert len(logs) == 2
        assert all(log.resource == 'user' for log in logs)

    def test_get_resource_logs_specific_id(self, audit_service, test_user):
        """Test retrieving logs for specific resource ID."""
        audit_service.log_action(test_user.id, 'create', resource='user', resource_id=1)
        audit_service.log_action(test_user.id, 'update', resource='user', resource_id=1)
        audit_service.log_action(test_user.id, 'create', resource='user', resource_id=2)

        logs = audit_service.get_audit_logs_by_resource('user', resource_id='1')

        assert len(logs) == 2
        assert all(log.resource_id == '1' for log in logs)

    def test_get_resource_logs_ordered_by_time(self, audit_service, test_user):
        """Test that resource logs are ordered by timestamp."""
        log1 = audit_service.log_action(test_user.id, 'create', resource='user', resource_id=1)
        log2 = audit_service.log_action(test_user.id, 'update', resource='user', resource_id=1)
        log3 = audit_service.log_action(test_user.id, 'delete', resource='user', resource_id=1)

        logs = audit_service.get_audit_logs_by_resource('user', resource_id='1')

        # Most recent first
        assert logs[0].id == log3.id
        assert logs[1].id == log2.id
        assert logs[2].id == log1.id

    def test_get_resource_logs_with_limit(self, audit_service, test_user):
        """Test limiting resource logs."""
        for i in range(10):
            audit_service.log_action(test_user.id, f'action_{i}', resource='user')

        logs = audit_service.get_audit_logs_by_resource('user', limit=3)

        assert len(logs) == 3


# Task 48: Test cleanup_old_logs method

class TestCleanupOldLogs:
    """Test old log cleanup functionality."""

    def test_cleanup_no_old_logs(self, audit_service, test_user):
        """Test cleanup with no old logs."""
        audit_service.log_action(test_user.id, 'recent_action')

        deleted_count = audit_service.cleanup_old_logs(days_to_keep=30)

        assert deleted_count == 0

    def test_cleanup_old_logs(self, audit_service, test_user, test_db_session):
        """Test cleanup removes old logs."""
        # Create old log (100 days ago)
        old_log = AuditLog(
            user_id=test_user.id,
            action='old_action',
            timestamp=datetime.utcnow() - timedelta(days=100)
        )
        test_db_session.add(old_log)
        test_db_session.commit()

        # Create recent log
        audit_service.log_action(test_user.id, 'recent_action')

        # Cleanup logs older than 90 days
        deleted_count = audit_service.cleanup_old_logs(days_to_keep=90)

        assert deleted_count == 1

        # Verify recent log still exists
        remaining_logs = test_db_session.query(AuditLog).all()
        assert len(remaining_logs) == 1
        assert remaining_logs[0].action == 'recent_action'

    def test_cleanup_multiple_old_logs(self, audit_service, test_user, test_db_session):
        """Test cleanup with multiple old logs."""
        # Create 5 old logs
        for i in range(5):
            old_log = AuditLog(
                user_id=test_user.id,
                action=f'old_action_{i}',
                timestamp=datetime.utcnow() - timedelta(days=100 + i)
            )
            test_db_session.add(old_log)

        # Create 3 recent logs
        for i in range(3):
            audit_service.log_action(test_user.id, f'recent_action_{i}')

        test_db_session.commit()

        # Cleanup logs older than 90 days
        deleted_count = audit_service.cleanup_old_logs(days_to_keep=90)

        assert deleted_count == 5

        # Verify only recent logs remain
        remaining_logs = test_db_session.query(AuditLog).all()
        assert len(remaining_logs) == 3

    def test_cleanup_custom_retention(self, audit_service, test_user, test_db_session):
        """Test cleanup with custom retention period."""
        # Create logs at different ages
        log_60_days = AuditLog(
            user_id=test_user.id,
            action='60_days_old',
            timestamp=datetime.utcnow() - timedelta(days=60)
        )
        log_40_days = AuditLog(
            user_id=test_user.id,
            action='40_days_old',
            timestamp=datetime.utcnow() - timedelta(days=40)
        )
        log_20_days = AuditLog(
            user_id=test_user.id,
            action='20_days_old',
            timestamp=datetime.utcnow() - timedelta(days=20)
        )
        test_db_session.add_all([log_60_days, log_40_days, log_20_days])
        test_db_session.commit()

        # Cleanup logs older than 30 days
        deleted_count = audit_service.cleanup_old_logs(days_to_keep=30)

        # Should delete 2 logs (60 and 40 days old)
        assert deleted_count == 2

        remaining_logs = test_db_session.query(AuditLog).all()
        assert len(remaining_logs) == 1
        assert remaining_logs[0].action == '20_days_old'


# Test get_recent_activity method

class TestGetRecentActivity:
    """Test recent activity retrieval."""

    def test_get_recent_activity_empty(self, audit_service):
        """Test recent activity with no logs."""
        logs = audit_service.get_recent_activity()

        assert len(logs) == 0

    def test_get_recent_activity_last_24_hours(self, audit_service, test_user):
        """Test retrieving activity from last 24 hours."""
        audit_service.log_action(test_user.id, 'recent1')
        audit_service.log_action(test_user.id, 'recent2')

        logs = audit_service.get_recent_activity(hours=24)

        assert len(logs) == 2

    def test_get_recent_activity_excludes_old(self, audit_service, test_user, test_db_session):
        """Test that old activity is excluded."""
        # Create old log (48 hours ago)
        old_log = AuditLog(
            user_id=test_user.id,
            action='old_action',
            timestamp=datetime.utcnow() - timedelta(hours=48)
        )
        test_db_session.add(old_log)
        test_db_session.commit()

        # Create recent log
        audit_service.log_action(test_user.id, 'recent_action')

        # Get last 24 hours
        logs = audit_service.get_recent_activity(hours=24)

        assert len(logs) == 1
        assert logs[0].action == 'recent_action'

    def test_get_recent_activity_custom_hours(self, audit_service, test_user, test_db_session):
        """Test recent activity with custom time window."""
        # Create log 10 hours ago
        log_10h = AuditLog(
            user_id=test_user.id,
            action='10h_ago',
            timestamp=datetime.utcnow() - timedelta(hours=10)
        )
        # Create log 30 hours ago
        log_30h = AuditLog(
            user_id=test_user.id,
            action='30h_ago',
            timestamp=datetime.utcnow() - timedelta(hours=30)
        )
        test_db_session.add_all([log_10h, log_30h])
        test_db_session.commit()

        # Get last 12 hours
        logs = audit_service.get_recent_activity(hours=12)

        assert len(logs) == 1
        assert logs[0].action == '10h_ago'

    def test_get_recent_activity_with_limit(self, audit_service, test_user):
        """Test recent activity with limit."""
        for i in range(10):
            audit_service.log_action(test_user.id, f'action_{i}')

        logs = audit_service.get_recent_activity(hours=24, limit=5)

        assert len(logs) == 5

    def test_get_recent_activity_ordered_by_time(self, audit_service, test_user):
        """Test that recent activity is ordered by timestamp."""
        log1 = audit_service.log_action(test_user.id, 'first')
        log2 = audit_service.log_action(test_user.id, 'second')
        log3 = audit_service.log_action(test_user.id, 'third')

        logs = audit_service.get_recent_activity()

        # Most recent first
        assert logs[0].id == log3.id
        assert logs[1].id == log2.id
        assert logs[2].id == log1.id
