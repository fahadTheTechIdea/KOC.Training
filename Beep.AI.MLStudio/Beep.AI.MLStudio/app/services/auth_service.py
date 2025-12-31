"""
Authentication Service - Local JWT Authentication
Identity Server authentication is handled by IdentityServerAuthService
"""
from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity
from app import db
from app.models.user import User, APIKey
from datetime import datetime
import os
import logging
from typing import Optional, Tuple, Dict

from app.utils.constants import (
    AUTH_MODE_LOCAL,
    AUTH_MODE_IDENTITY_SERVER,
    ENV_AUTH_MODE,
    ENV_IDENTITY_SERVER_CLIENT_ID,
    ERROR_LOCAL_LOGIN_NOT_AVAILABLE
)

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and authorization service - Local JWT mode"""
    
    @staticmethod
    def get_auth_mode() -> str:
        """
        Get current authentication mode
        Priority: database (AuthConfig) > environment variable > default
        
        Returns:
            'local', 'identity_server', or 'microsoft_sso'
        """
        try:
            from app.models.auth_config import AuthConfig
            auth_config = AuthConfig.get_config()
            if auth_config and auth_config.auth_mode:
                return auth_config.auth_mode.lower()
        except Exception as e:
            logger.debug(f"Could not get auth mode from database: {e}")
        
        # Fallback to environment variable
        return os.getenv(ENV_AUTH_MODE, AUTH_MODE_LOCAL).lower()
    
    @staticmethod
    def is_identity_server_mode() -> bool:
        """Check if Identity Server mode is enabled"""
        return AuthService.get_auth_mode() == AUTH_MODE_IDENTITY_SERVER
    
    @staticmethod
    def is_microsoft_sso_mode() -> bool:
        """Check if Microsoft SSO mode is enabled"""
        return AuthService.get_auth_mode() == 'microsoft_sso'
    
    @staticmethod
    def _get_identity_server_service():
        """Get Identity Server auth service instance"""
        if not AuthService.is_identity_server_mode():
            return None
        
        try:
            from app.services.identity_server_auth_service import IdentityServerAuthService
            return IdentityServerAuthService()
        except Exception as e:
            logger.error(f"Failed to initialize Identity Server auth service: {e}")
            return None
    
    @staticmethod
    def register_user(username, email, password):
        """Register a new user"""
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        user = User(username=username, email=email)
        if password:
            user.set_password(password)
        db.session.add(user)
        
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            return None, str(e)
    
    @staticmethod
    def authenticate_user(username_or_email, password):
        """Authenticate user and return user object"""
        user = User.query.filter_by(username=username_or_email).first()
        if not user:
            user = User.query.filter_by(email=username_or_email).first()
        
        if not user or not user.check_password(password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    def login_user(username_or_email: str, password: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Login user and return JWT token
        Works in local mode only
        
        Args:
            username_or_email: Username or email address
            password: User password
            
        Returns:
            Tuple of (login_result_dict, error_message)
        """
        if AuthService.is_identity_server_mode():
            return None, ERROR_LOCAL_LOGIN_NOT_AVAILABLE
        
        user = AuthService.authenticate_user(username_or_email, password)
        if not user:
            return None, "Invalid username/email or password"
        
        # Update login tracking
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.session.commit()
        
        # Get JWT expiration from AuthConfig
        from app.models.auth_config import AuthConfig
        auth_config = AuthConfig.get_config()
        expires_delta = None
        if auth_config.jwt_token_expires:
            from datetime import timedelta
            expires_delta = timedelta(seconds=auth_config.jwt_token_expires)
        
        access_token = create_access_token(identity=user.id, expires_delta=expires_delta)
        return {'access_token': access_token, 'user': user.to_dict()}, None
    
    @staticmethod
    def login_with_identity_server(access_token: str, client_id: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Login using Identity Server OAuth token (delegates to IdentityServerAuthService)
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID (optional, uses env var if not provided)
            
        Returns:
            Tuple of (login_result_dict, error_message)
        """
        if not AuthService.is_identity_server_mode():
            return None, "Identity Server mode not enabled"
        
        service = AuthService._get_identity_server_service()
        if not service:
            return None, "Identity Server authentication service not available"
        
        if not client_id:
            client_id = os.getenv(ENV_IDENTITY_SERVER_CLIENT_ID)
        
        return service.login(access_token, client_id)
    
    @staticmethod
    def login_with_microsoft(code: str, state: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Login using Microsoft SSO OAuth code
        
        Args:
            code: OAuth authorization code
            state: OAuth state parameter (optional)
            
        Returns:
            Tuple of (login_result_dict, error_message)
        """
        if not AuthService.is_microsoft_sso_mode():
            return None, "Microsoft SSO mode not enabled"
        
        try:
            from app.services.microsoft_sso_service import MicrosoftSSOService
            service = MicrosoftSSOService()
            return service.handle_callback(code, state)
        except Exception as e:
            logger.error(f"Error in Microsoft SSO login: {e}")
            return None, str(e)
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """
        Get current authenticated user
        Works with local JWT, Identity Server OAuth tokens, Microsoft SSO, and API keys
        
        Returns:
            User object if authenticated, None otherwise
        """
        try:
            # Check for API key first (works in all modes)
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if api_key:
                user = AuthService.validate_api_key(api_key)
                if user:
                    return user
            
            auth_mode = AuthService.get_auth_mode()
            
            if auth_mode == 'identity_server':
                # Check for OAuth token in Authorization header
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    oauth_token = auth_header[7:]
                    
                    # Get client_id from AuthConfig
                    from app.models.auth_config import AuthConfig
                    auth_config = AuthConfig.get_config()
                    client_id = auth_config.identity_server_client_id if auth_config else os.getenv(ENV_IDENTITY_SERVER_CLIENT_ID)
                    
                    # Use Identity Server auth service
                    service = AuthService._get_identity_server_service()
                    if service:
                        is_valid, user_info, error = service.validate_token(oauth_token, client_id)
                        if is_valid and user_info:
                            user, _ = service.get_or_create_user(user_info)
                            return user
            
            elif auth_mode == 'microsoft_sso':
                # Check for OAuth token in Authorization header
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    oauth_token = auth_header[7:]
                    try:
                        from app.services.microsoft_sso_service import MicrosoftSSOService
                        service = MicrosoftSSOService()
                        user_info = service.get_user_info(oauth_token)
                        if user_info:
                            user, _ = service.get_or_create_user(user_info)
                            return user
                    except Exception as e:
                        logger.debug(f"Error validating Microsoft token: {e}")
            
            # Fall back to local JWT (works in local mode and as fallback)
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(user_id)
                if user and user.is_active:
                    return user
                    
        except Exception as e:
            logger.debug(f"Error getting current user: {e}")
        
        return None
    
    @staticmethod
    def is_admin(user: Optional[User] = None) -> bool:
        """
        Check if user is admin
        
        Args:
            user: User object (if None, gets current user)
            
        Returns:
            True if user is admin
        """
        if user is None:
            user = AuthService.get_current_user()
        return user is not None and user.is_admin
    
    @staticmethod
    def require_auth(func):
        """
        Decorator to require authentication
        Usage: @AuthService.require_auth
        Redirects to login page if not authenticated
        """
        from functools import wraps
        from flask import jsonify, redirect, url_for, request
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = AuthService.get_current_user()
            if not user:
                # For API requests, return JSON error
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                # For web requests, redirect to login
                return redirect(url_for('auth.login_page', next=request.url))
            return func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def require_admin(func):
        """
        Decorator to require admin role
        Usage: @AuthService.require_admin
        """
        from functools import wraps
        from flask import jsonify, redirect, url_for, request
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = AuthService.get_current_user()
            if not user:
                # For API requests, return JSON error
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                # For web requests, redirect to login
                return redirect(url_for('auth.login_page', next=request.url))
            if not user.is_admin:
                # For API requests, return JSON error
                if request.path.startswith('/api/') or request.is_json:
                    return jsonify({'error': 'Admin access required'}), 403
                # For web requests, redirect to login
                return redirect(url_for('auth.login_page', next=request.url))
            return func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def create_api_key(user_id, key_name):
        """Create API key for Community integration"""
        api_key = APIKey.generate_key()
        
        key_obj = APIKey(
            user_id=user_id,
            key_name=key_name,
            api_key=api_key
        )
        db.session.add(key_obj)
        
        try:
            db.session.commit()
            return key_obj, None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating API key: {e}")
            return None, str(e)
    
    @staticmethod
    def validate_api_key(api_key_str):
        """Validate API key and return user"""
        key_obj = APIKey.query.filter_by(api_key=api_key_str, is_active=True).first()
        if not key_obj:
            return None
        
        key_obj.last_used_at = datetime.utcnow()
        db.session.commit()
        
        return key_obj.user
    
    @staticmethod
    def revoke_api_key(user_id, key_id):
        """Revoke an API key"""
        key_obj = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
        if not key_obj:
            return False, "API key not found"
        
        key_obj.is_active = False
        db.session.commit()
        return True, None
    
    @staticmethod
    def get_user_api_keys(user_id):
        """Get all API keys for a user"""
        keys = APIKey.query.filter_by(user_id=user_id).all()
        return [key.to_dict() for key in keys]


def get_current_user():
    """Helper function to get current user"""
    return AuthService.get_current_user()
