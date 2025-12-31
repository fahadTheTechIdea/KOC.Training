"""
Authentication Service - Local JWT Authentication
Identity Server authentication is handled by IdentityServerAuthService
"""
from flask import request
from flask_jwt_extended import (
    create_access_token, 
    get_jwt_identity,
    verify_jwt_in_request
)
from app import db
from app.models.user import User, APIKey, ROLE_USER, ROLE_ADMIN
from datetime import datetime
import os
import logging
from typing import Optional, Tuple, Dict

from app.services.identity_server_auth_service import IdentityServerAuthService
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
        
        Returns:
            'local' for local JWT or 'identity_server' for OAuth2/OIDC
        """
        return os.getenv(ENV_AUTH_MODE, AUTH_MODE_LOCAL).lower()
    
    @staticmethod
    def is_identity_server_mode() -> bool:
        """Check if Identity Server mode is enabled"""
        return AuthService.get_auth_mode() == AUTH_MODE_IDENTITY_SERVER
    
    @staticmethod
    def _get_identity_server_service() -> Optional[IdentityServerAuthService]:
        """Get Identity Server auth service instance"""
        if not AuthService.is_identity_server_mode():
            return None
        
        try:
            return IdentityServerAuthService()
        except Exception as e:
            logger.error(f"Failed to initialize Identity Server auth service: {e}")
            return None
    
    @staticmethod
    def register_user(username, email, password, role=None):
        """
        Register a new user
        
        Args:
            username: Username
            email: Email address
            password: User password
            role: User role (defaults to 'user' if not provided)
        
        Returns:
            Tuple of (user, error_message)
        """
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        # Default role to 'user' if not provided
        if role is None:
            role = ROLE_USER
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Flush to get user.id before creating profile
        
        from app.models.user import UserProfile
        profile = UserProfile(
            user_id=user.id,
            display_name=username
        )
        db.session.add(profile)
        
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
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
        
        # JWT identity must be a string, not an integer
        access_token = create_access_token(identity=str(user.id))
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
    def get_current_user() -> Optional[User]:
        """
        Get current authenticated user
        Works with both local JWT, Identity Server OAuth tokens, and API keys
        
        Returns:
            User object if authenticated, None otherwise
        """
        try:
            # Check for API key first (for ML Studio integration)
            auth_header = request.headers.get('Authorization', '')
            
            # Try API key authentication (from X-API-Key header or Bearer)
            api_key = request.headers.get('X-API-Key')
            if not api_key and auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
            
            if api_key:
                # Try API key validation
                api_user = AuthService.validate_api_key(api_key)
                if api_user:
                    return api_user
                # If validate_api_key returns None, it could be a valid service key
                # but we need user from JWT or request body - continue to JWT check
            
            if AuthService.is_identity_server_mode():
                # Check for OAuth token in Authorization header
                if auth_header.startswith('Bearer '):
                    oauth_token = auth_header[7:]
                    client_id = os.getenv(ENV_IDENTITY_SERVER_CLIENT_ID)
                    
                    # Use Identity Server auth service
                    service = AuthService._get_identity_server_service()
                    if service:
                        is_valid, user_info, error = service.validate_token(oauth_token, client_id)
                        if is_valid and user_info:
                            user, _ = service.get_or_create_user(user_info)
                            return user
            
            # Fall back to local JWT from cookies
            # Use Flask-JWT-Extended's optional verification pattern
            try:
                # Verify JWT token if present (optional=True means don't fail if no token)
                verify_jwt_in_request(optional=True)
                
                # get_jwt_identity() returns None if no valid token is present
                # According to Flask-JWT-Extended docs, this should work with optional=True
                user_id_str = get_jwt_identity()
                if user_id_str:
                    # Convert string ID back to integer for database query
                    try:
                        user_id = int(user_id_str)
                        user = User.query.get(user_id)
                        if user:
                            return user
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid user_id in JWT: {user_id_str}")
                        pass
            except RuntimeError:
                # RuntimeError is raised when no JWT token is present
                # This is expected for unauthenticated users when using optional verification
                pass
            except Exception as e:
                # Log other errors for debugging
                logger.debug(f"Error in JWT verification: {e}", exc_info=True)
                pass
        except Exception as e:
            logger.debug(f"Error getting current user: {e}")
        
        return None
    
    @staticmethod
    def create_api_key(user_id, key_name):
        """Create API key for MLStudio client"""
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
            return None, str(e)
    
    @staticmethod
    def validate_api_key(api_key_str):
        """
        Validate API key and return user
        
        Supports both:
        1. User API keys from APIKey table (returns User)
        2. Service API keys from config (for service-to-service, returns None but key is valid)
        """
        # First check user API keys
        key_obj = APIKey.query.filter_by(api_key=api_key_str, is_active=True).first()
        if key_obj:
            key_obj.last_used_at = datetime.utcnow()
            db.session.commit()
            return key_obj.user
        
        # Check service API keys from config
        from flask import current_app
        valid_keys = current_app.config.get('API_KEYS', [])
        if api_key_str in valid_keys:
            # Valid service API key - authorized but no specific user
            # Caller should provide user_id in request body for service-to-service calls
            return None
        
        return None
    
    @staticmethod
    def validate_api_key_for_service(api_key_str):
        """
        Validate API key for service-to-service calls
        
        Returns:
            True if API key is valid (user key or service key), False otherwise
        """
        # Check user API keys
        key_obj = APIKey.query.filter_by(api_key=api_key_str, is_active=True).first()
        if key_obj:
            return True
        
        # Check service API keys from config
        from flask import current_app
        valid_keys = current_app.config.get('API_KEYS', [])
        if api_key_str in valid_keys:
            return True
        
        return False
    
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
