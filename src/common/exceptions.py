class AppError(Exception):
    """Base application error."""


class ConfigError(AppError):
    """Configuration loading error."""


class StorageError(AppError):
    """External storage operation error."""


class MessagingError(AppError):
    """Message broker operation error."""


class DatabaseError(AppError):
    """Database operation error."""


class NotFoundError(AppError):
    """Entity not found."""
