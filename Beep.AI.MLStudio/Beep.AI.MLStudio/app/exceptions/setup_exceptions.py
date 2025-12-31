"""
Setup Exceptions
"""

class SetupError(Exception):
    """Base exception for setup errors"""
    pass


class SetupValidationError(SetupError):
    """Raised when setup validation fails"""
    pass


class SetupConfigurationError(SetupError):
    """Raised when setup configuration fails"""
    pass


class SetupCompleteError(SetupError):
    """Raised when setup completion fails"""
    pass
