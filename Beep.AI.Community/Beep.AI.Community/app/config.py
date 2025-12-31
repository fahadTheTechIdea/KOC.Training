"""
Configuration classes for Beep.AI.Community
Supports config.json file loading with priority: config.json > Flask config > env vars > defaults
"""
import os
import json
import sys
from pathlib import Path
from typing import Any
from datetime import timedelta


def _get_app_directory() -> Path:
    """Get the application directory"""
    # If running as frozen executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # Running as script - use script's parent directory
    return Path(__file__).parent.parent


def _load_config_file() -> dict:
    """Load configuration from config.json file (if exists)"""
    config_file = _get_app_directory() / 'config.json'
    if not config_file.exists():
        return {}
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return config_data
    except Exception as e:
        print(f"Warning: Could not load config.json: {e}")
        return {}


# Load config.json once at module level
_config_file_data = _load_config_file()


def _get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get config value with priority: config.json > env vars > default
    key_path can be dot-separated (e.g., 'community.mlstudio_url')
    """
    # Priority 1: Check config.json
    if _config_file_data:
        parts = key_path.split('.')
        current = _config_file_data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = None
                break
        if current is not None:
            return current
    
    # Priority 2: Check environment variables
    env_key = key_path.upper().replace('.', '_')
    env_value = os.getenv(env_key)
    if env_value is not None:
        # Try to convert to appropriate type
        try:
            if env_value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif env_value.lower() in ('false', '0', 'no', 'off'):
                return False
            elif env_value.replace('.', '', 1).isdigit():
                return float(env_value) if '.' in env_value else int(env_value)
        except:
            pass
        return env_value
    
    # Priority 3: Return default
    return default


class Config:
    """Base configuration with config.json support"""
    SECRET_KEY = _get_config_value('secret_key', os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    JWT_SECRET_KEY = _get_config_value('jwt_secret_key', os.getenv('JWT_SECRET_KEY', SECRET_KEY))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(_get_config_value('jwt_access_token_expires', os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))))
    
    # JWT Cookie Configuration
    JWT_TOKEN_LOCATION = ['headers', 'cookies']  # Accept from both headers and cookies
    JWT_COOKIE_SECURE = _get_config_value('jwt_cookie_secure', False)  # True in production with HTTPS
    JWT_COOKIE_HTTPONLY = True  # Prevent XSS attacks
    JWT_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_COOKIE_CSRF_PROTECT = False  # Can enable for additional security if needed
    
    MAX_CONTENT_LENGTH = int(_get_config_value('max_upload_size', os.getenv('MAX_UPLOAD_SIZE', 100))) * 1024 * 1024
    UPLOAD_FOLDER = _get_config_value('upload_folder', os.getenv('UPLOAD_FOLDER', 'uploads'))
    AISERVER_URL = _get_config_value('aiserver_url', os.getenv('AISERVER_URL', 'http://127.0.0.1:5000'))
    AISERVER_API_KEY = _get_config_value('aiserver_api_key', os.getenv('AISERVER_API_KEY', ''))
    REDIS_URL = _get_config_value('redis_url', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    RATELIMIT_ENABLED = _get_config_value('ratelimit_enabled', os.getenv('RATELIMIT_ENABLED', 'true').lower() == 'true')
    
    # MLStudio Connection Settings (from config.json or env vars)
    MLSTUDIO_URL = _get_config_value('community.mlstudio_connection.url', 
                                     _get_config_value('mlstudio_url', os.getenv('MLSTUDIO_URL', 'http://127.0.0.1:5000')))
    MLSTUDIO_ENABLED = _get_config_value('community.mlstudio_connection.enabled',
                                         _get_config_value('mlstudio_enabled', os.getenv('MLSTUDIO_ENABLED', 'false').lower() == 'true'))
    MLSTUDIO_API_KEY = _get_config_value('community.mlstudio_connection.api_key',
                                        _get_config_value('mlstudio_api_key', os.getenv('MLSTUDIO_API_KEY', '')))
    MLSTUDIO_TIMEOUT = int(_get_config_value('community.mlstudio_connection.timeout',
                                            _get_config_value('mlstudio_timeout', os.getenv('MLSTUDIO_TIMEOUT', '30'))))
    
    # Microsoft SSO Settings (from config.json or env vars)
    MICROSOFT_SSO_ENABLED = _get_config_value('authentication.microsoft_sso.enabled',
                                              _get_config_value('microsoft_sso_enabled', os.getenv('MICROSOFT_SSO_ENABLED', 'false').lower() == 'true'))
    MICROSOFT_CLIENT_ID = _get_config_value('authentication.microsoft_sso.client_id',
                                           _get_config_value('microsoft_client_id', os.getenv('MICROSOFT_CLIENT_ID', '')))
    MICROSOFT_CLIENT_SECRET = _get_config_value('authentication.microsoft_sso.client_secret',
                                               _get_config_value('microsoft_client_secret', os.getenv('MICROSOFT_CLIENT_SECRET', '')))
    MICROSOFT_TENANT_ID = _get_config_value('authentication.microsoft_sso.tenant_id',
                                            _get_config_value('microsoft_tenant_id', os.getenv('MICROSOFT_TENANT_ID', '')))
    MICROSOFT_REDIRECT_URI = _get_config_value('authentication.microsoft_sso.redirect_uri_community',
                                               _get_config_value('microsoft_redirect_uri', os.getenv('MICROSOFT_REDIRECT_URI', '')))
    
    # API Key Authentication for service-to-service calls
    API_KEY_HEADER = 'X-API-Key'
    API_KEYS = _get_config_value('api_keys', os.getenv('API_KEYS', '').split(',') if os.getenv('API_KEYS') else [])


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///community.db')
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Provide default to avoid import errors - will be validated when actually used
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///community.db')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # JWT cookies should be secure in production
    JWT_COOKIE_SECURE = True  # Requires HTTPS


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Helper functions for accessing configuration
def get_mlstudio_connection() -> dict:
    """
    Get MLStudio connection configuration
    Priority: config.json > Flask config > env vars > defaults
    """
    return {
        'url': Config.MLSTUDIO_URL,
        'enabled': Config.MLSTUDIO_ENABLED,
        'api_key': Config.MLSTUDIO_API_KEY,
        'timeout': Config.MLSTUDIO_TIMEOUT
    }


def get_microsoft_sso() -> dict:
    """
    Get Microsoft SSO configuration
    Priority: config.json > Flask config > env vars > defaults
    """
    return {
        'enabled': Config.MICROSOFT_SSO_ENABLED,
        'client_id': Config.MICROSOFT_CLIENT_ID,
        'client_secret': Config.MICROSOFT_CLIENT_SECRET,
        'tenant_id': Config.MICROSOFT_TENANT_ID,
        'redirect_uri': Config.MICROSOFT_REDIRECT_URI
    }
