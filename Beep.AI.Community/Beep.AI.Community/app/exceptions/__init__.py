"""
Custom Exception Classes
"""
from app.exceptions.auth_exceptions import (
    AuthenticationError,
    IdentityServerError,
    TokenValidationError,
    UserAccessDeniedError
)
from app.exceptions.database_exceptions import (
    DatabaseError,
    DatabaseConnectionError,
    DatabaseConfigurationError,
    UnsupportedDatabaseProviderError
)
from app.exceptions.setup_exceptions import (
    SetupError,
    SetupValidationError,
    SetupConfigurationError,
    SetupCompleteError
)

__all__ = [
    'AuthenticationError',
    'IdentityServerError',
    'TokenValidationError',
    'UserAccessDeniedError',
    'DatabaseError',
    'DatabaseConnectionError',
    'DatabaseConfigurationError',
    'UnsupportedDatabaseProviderError',
    'SetupError',
    'SetupValidationError',
    'SetupConfigurationError',
    'SetupCompleteError'
]
