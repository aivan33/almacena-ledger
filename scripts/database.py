"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from scripts.constants import DATABASE_URL
from scripts.logger_config import get_logger

logger = get_logger(__name__)

# Create declarative base for models
Base = declarative_base()

# Global engine instance (singleton)
_engine = None

# Global session factory (singleton)
_SessionFactory = None


def get_engine():
    """
    Get SQLAlchemy engine (singleton pattern).

    Creates engine with connection pooling configuration:
    - pool_size: 5 connections
    - max_overflow: 10 additional connections
    - pool_pre_ping: Test connections before use
    - echo: False (don't log SQL statements)

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine

    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False
        )
        logger.info(f"Database engine created: {DATABASE_URL}")

    return _engine


def get_session() -> Session:
    """
    Get database session for transactions.

    Uses sessionmaker bound to the engine (singleton pattern).
    Each call returns a new session instance.

    Returns:
        Session: SQLAlchemy session instance
    """
    global _SessionFactory

    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine())

    return _SessionFactory()


def init_db():
    """
    Initialize database tables from model definitions.

    Imports all models and creates corresponding tables if they don't exist.
    Uses Base.metadata.create_all() which is idempotent.
    """
    # Import all models to register them with Base
    from scripts.models.user import User
    from scripts.models.audit_log import AuditLog
    from scripts.models.validation_report import ValidationReport

    # Create all tables
    Base.metadata.create_all(get_engine())

    logger.info("Database initialized successfully")
