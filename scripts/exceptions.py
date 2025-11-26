"""
Custom exceptions for the Almacena Dashboard project.

This module defines specific exception types to replace broad exception handling
and provide better error messages and debugging information.
"""


class DashboardError(Exception):
    """Base exception class for all dashboard-related errors."""
    pass


class CredentialsError(DashboardError):
    """Raised when there are issues with Google API credentials."""
    pass


class DataFetchError(DashboardError):
    """Raised when data cannot be fetched from external sources."""
    pass


class DataProcessingError(DashboardError):
    """Raised when data processing or transformation fails."""
    pass


class ConfigurationError(DashboardError):
    """Raised when configuration is invalid or missing."""
    pass


class ExportError(DashboardError):
    """Raised when data export fails."""
    pass


class ValidationError(DashboardError):
    """Raised when data validation fails."""
    pass


class AuthenticationError(DashboardError):
    """Raised when authentication fails (invalid credentials, etc.)."""
    pass


class AuthorizationError(DashboardError):
    """Raised when user lacks permission for an action."""
    pass


class SessionExpiredError(AuthenticationError):
    """Raised when session token has expired."""
    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to failed login attempts."""
    pass


class PermissionDeniedError(AuthorizationError):
    """Raised when user attempts unauthorized action."""
    pass
