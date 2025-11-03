"""
Centralized logging configuration for the Almacena Dashboard project.

This module provides a consistent logging setup across all scripts with:
- Timestamped log entries
- Both console and file output
- Log rotation to manage file sizes
- Different log levels for development vs production
- Structured logging format

Usage:
    from scripts.logger_config import get_logger

    logger = get_logger(__name__)
    logger.info("Processing started")
    logger.warning("Unusual condition detected")
    logger.error("An error occurred", exc_info=True)
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ from calling module)
        log_level: Optional log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If not provided, reads from LOG_LEVEL env var or defaults to INFO

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Data processing started")
        >>> logger.error("Failed to fetch data", exc_info=True)
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Only configure if not already configured (avoid duplicate handlers)
    if logger.handlers:
        return logger

    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    logger.setLevel(getattr(logging, log_level))

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation (DEBUG and above)
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / 'dashboard.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def set_log_level(logger: logging.Logger, level: str) -> None:
    """
    Change the log level of an existing logger.

    Args:
        logger: Logger instance to modify
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Example:
        >>> logger = get_logger(__name__)
        >>> set_log_level(logger, 'DEBUG')  # Enable debug logging
    """
    logger.setLevel(getattr(logging, level.upper()))


def log_environment_info(logger: logging.Logger) -> None:
    """
    Log relevant environment information for debugging.

    Args:
        logger: Logger instance to use
    """
    logger.debug("=" * 60)
    logger.debug("Environment Information")
    logger.debug("=" * 60)
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Python path: {os.getenv('PYTHONPATH', 'Not set')}")

    # Log relevant environment variables (without exposing sensitive data)
    env_vars = [
        'GOOGLE_CREDENTIALS_FILE',
        'GOOGLE_DRIVE_FILE_ID',
        'GOOGLE_SHEET_NAME',
        'LOG_LEVEL',
        'N8N_HOST',
        'N8N_PORT',
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                masked_value = '***MASKED***'
            elif 'FILE_ID' in var:
                masked_value = value[:10] + '...' if len(value) > 10 else value
            else:
                masked_value = value
            logger.debug(f"{var}: {masked_value}")
        else:
            logger.debug(f"{var}: Not set")

    logger.debug("=" * 60)
