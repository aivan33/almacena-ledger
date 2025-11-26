"""User account model for authentication and authorization."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from scripts.database import Base
from datetime import datetime


class User(Base):
    """User account model with authentication fields and audit trail relationship."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='viewer')
    active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationship to audit logs
    created_audit_logs = relationship('AuditLog', back_populates='user')

    def to_dict(self, include_password=False):
        """
        Convert user model to dictionary.

        Args:
            include_password (bool): If True, include password_hash in output. Default False.

        Returns:
            dict: User data excluding password_hash by default
        """
        data = {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

        if include_password:
            data['password_hash'] = self.password_hash

        return data
