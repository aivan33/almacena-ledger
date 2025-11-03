"""
Unit tests for scripts/logger_config.py

Tests cover:
- Logger initialization
- Log level configuration
- File and console handlers
- Log rotation
- Environment variable masking
"""
import pytest
import logging
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.logger_config import get_logger, set_log_level, log_environment_info


class TestLoggerInitialization:
    """Tests for logger initialization."""

    @pytest.mark.unit
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger('test_logger')

        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_logger'

    @pytest.mark.unit
    def test_get_logger_default_level_info(self, monkeypatch):
        """Test that default log level is INFO."""
        # Remove LOG_LEVEL env var if it exists
        monkeypatch.delenv('LOG_LEVEL', raising=False)

        logger = get_logger('test_default_level')

        assert logger.level == logging.INFO

    @pytest.mark.unit
    def test_get_logger_respects_env_var(self, monkeypatch):
        """Test that LOG_LEVEL environment variable is respected."""
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')

        logger = get_logger('test_env_level')

        assert logger.level == logging.DEBUG

    @pytest.mark.unit
    def test_get_logger_with_explicit_level(self):
        """Test logger with explicitly provided log level."""
        logger = get_logger('test_explicit_level', log_level='WARNING')

        assert logger.level == logging.WARNING

    @pytest.mark.unit
    def test_get_logger_is_idempotent(self):
        """Test that calling get_logger twice for same name doesn't duplicate handlers."""
        logger1 = get_logger('test_idempotent')
        initial_handler_count = len(logger1.handlers)

        logger2 = get_logger('test_idempotent')

        # Should be the same logger instance
        assert logger1 is logger2

        # Handler count should not increase
        assert len(logger2.handlers) == initial_handler_count


class TestLogHandlers:
    """Tests for log handlers configuration."""

    @pytest.mark.unit
    def test_logger_has_console_handler(self):
        """Test that logger has console (StreamHandler) configured."""
        logger = get_logger('test_console_handler')

        # Find console handler
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                          and not isinstance(h, logging.FileHandler)]

        assert len(console_handlers) > 0

    @pytest.mark.unit
    def test_logger_has_file_handler(self):
        """Test that logger has file (RotatingFileHandler) configured."""
        logger = get_logger('test_file_handler')

        # Find file handler
        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]

        assert len(file_handlers) > 0

    @pytest.mark.unit
    def test_file_handler_creates_log_directory(self):
        """Test that log directory is created automatically."""
        logger = get_logger('test_log_dir')

        # Log directory should exist
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        assert log_dir.exists()

    @pytest.mark.unit
    def test_console_handler_level_info(self):
        """Test that console handler is set to INFO level."""
        logger = get_logger('test_console_level')

        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                          and not isinstance(h, logging.FileHandler)]

        if console_handlers:
            assert console_handlers[0].level == logging.INFO

    @pytest.mark.unit
    def test_file_handler_level_debug(self):
        """Test that file handler is set to DEBUG level."""
        logger = get_logger('test_file_level')

        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]

        if file_handlers:
            assert file_handlers[0].level == logging.DEBUG


class TestLogFormatting:
    """Tests for log message formatting."""

    @pytest.mark.unit
    def test_console_formatter_has_timestamp(self):
        """Test that console formatter includes timestamp."""
        logger = get_logger('test_console_format')

        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                          and not isinstance(h, logging.FileHandler)]

        if console_handlers:
            formatter = console_handlers[0].formatter
            assert '%(asctime)s' in formatter._fmt

    @pytest.mark.unit
    def test_file_formatter_has_detailed_info(self):
        """Test that file formatter includes detailed information."""
        logger = get_logger('test_file_format')

        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]

        if file_handlers:
            formatter = file_handlers[0].formatter
            # Should have function name and line number
            assert '%(funcName)s' in formatter._fmt
            assert '%(lineno)d' in formatter._fmt


class TestSetLogLevel:
    """Tests for set_log_level function."""

    @pytest.mark.unit
    def test_set_log_level_changes_level(self):
        """Test that set_log_level changes the logger level."""
        logger = get_logger('test_set_level')
        initial_level = logger.level

        set_log_level(logger, 'ERROR')

        assert logger.level == logging.ERROR
        assert logger.level != initial_level

    @pytest.mark.unit
    def test_set_log_level_case_insensitive(self):
        """Test that set_log_level handles case-insensitive input."""
        logger = get_logger('test_set_level_case')

        set_log_level(logger, 'debug')

        assert logger.level == logging.DEBUG

        set_log_level(logger, 'WARNING')

        assert logger.level == logging.WARNING


class TestEnvironmentInfoLogging:
    """Tests for log_environment_info function."""

    @pytest.mark.unit
    def test_log_environment_info_runs_without_error(self, caplog):
        """Test that log_environment_info executes without errors."""
        logger = get_logger('test_env_info')
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            log_environment_info(logger)

        # Should have logged something
        assert len(caplog.records) > 0

    @pytest.mark.unit
    def test_log_environment_info_logs_working_directory(self, caplog):
        """Test that working directory is logged."""
        logger = get_logger('test_env_wd')
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            log_environment_info(logger)

        # Check that working directory was logged
        messages = [record.message for record in caplog.records]
        assert any('Working directory' in msg for msg in messages)

    @pytest.mark.unit
    def test_log_environment_info_masks_passwords(self, caplog, monkeypatch):
        """Test that password environment variables are masked."""
        logger = get_logger('test_env_mask')
        logger.setLevel(logging.DEBUG)

        # Set a password environment variable
        monkeypatch.setenv('TEST_PASSWORD', 'secret123')

        with caplog.at_level(logging.DEBUG):
            log_environment_info(logger)

        messages = [record.message for record in caplog.records]
        message_text = ' '.join(messages)

        # Password should be masked, not visible
        assert 'secret123' not in message_text

    @pytest.mark.unit
    def test_log_environment_info_masks_file_ids(self, caplog, monkeypatch):
        """Test that file IDs are partially masked."""
        logger = get_logger('test_env_file_id')
        logger.setLevel(logging.DEBUG)

        # Set file ID
        monkeypatch.setenv('GOOGLE_DRIVE_FILE_ID', '1234567890abcdefghij')

        with caplog.at_level(logging.DEBUG):
            log_environment_info(logger)

        messages = [record.message for record in caplog.records]
        message_text = ' '.join(messages)

        # Full file ID should not be visible
        assert '1234567890abcdefghij' not in message_text
        # But first part might be (masked as "1234567890...")
        assert '...' in message_text or 'GOOGLE_DRIVE_FILE_ID' in message_text


class TestLoggerPropagation:
    """Tests for logger propagation settings."""

    @pytest.mark.unit
    def test_logger_does_not_propagate(self):
        """Test that logger propagation is disabled to avoid duplicates."""
        logger = get_logger('test_propagation')

        assert logger.propagate is False


class TestLogRotation:
    """Tests for log file rotation configuration."""

    @pytest.mark.unit
    def test_file_handler_has_rotation(self):
        """Test that file handler is configured for rotation."""
        logger = get_logger('test_rotation')

        from logging.handlers import RotatingFileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, RotatingFileHandler)]

        assert len(file_handlers) > 0

        # Check rotation settings
        handler = file_handlers[0]
        assert handler.maxBytes > 0  # Should have max bytes set
        assert handler.backupCount > 0  # Should keep backups
