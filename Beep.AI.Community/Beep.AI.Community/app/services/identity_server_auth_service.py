"""
Identity Server Authentication Service
Handles OAuth2/OIDC authentication via Beep.Foundation.IdentityServer
"""
import os
import secrets
import logging
from typing import Optional, Tuple, Dict, Any

from flask_jwt_extended import create_access_token
from app import db
from app.models.user import User
from app.clients.identity_server_client import IdentityServerClient, get_identity_server_client
from app.utils.constants import (
    AUTH_MODE_IDENTITY_SERVER,
    ERROR_IDENTITY_SERVER_NOT_CONFIGURED,
    ERROR_TOKEN_VALIDATION_FAILED,
    ERROR_USER_INFO_RETRIEVAL_FAILED,
    ERROR_EMAIL_NOT_FOUND,
    ERROR_USERNAME_NOT_FOUND
)
from app.exceptions.auth_exceptions import (
    IdentityServerError,
    TokenValidationError,
    UserAccessDeniedError
)

logger = logging.getLogger(__name__)


class IdentityServerAuthService:
    """Service for Identity Server OAuth2/OIDC authentication"""
    
    def __init__(self, client: Optional[IdentityServerClient] = None):
        """
        Initialize Identity Server auth service
        
        Args:
            client: Optional Identity Server client instance
        """
        self.client = client or get_identity_server_client()
    
    def validate_token(
        self, 
        access_token: str, 
        client_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate OAuth token from Identity Server
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID (optional, uses env var if not provided)
            
        Returns:
            Tuple of (is_valid, user_info, error_message)
        """
        if not self.client:
            return False, None, ERROR_IDENTITY_SERVER_NOT_CONFIGURED
        
        try:
            # Validate token
            validation_result = self.client.validate_token(access_token)
            if not validation_result.get('success', True) or 'error' in validation_result:
                error_msg = validation_result.get('error', ERROR_TOKEN_VALIDATION_FAILED)
                return False, None, error_msg
            
            # Get user info
            user_info = self.client.get_user_info(access_token)
            if not user_info:
                return False, None, ERROR_USER_INFO_RETRIEVAL_FAILED
            
            # Check access if client_id provided
            if client_id:
                access_check = self.client.check_user_access(client_id, access_token)
                if not access_check.get('hasAccess', False):
                    reason = access_check.get('reason', 'Access denied')
                    return False, None, reason
            
            return True, user_info, None
            
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None, str(e)
    
    def get_or_create_user(self, user_info: Dict[str, Any]) -> Tuple[Optional[User], Optional[str]]:
        """
        Get or create local user from Identity Server user info
        
        Args:
            user_info: User information from Identity Server
            
        Returns:
            Tuple of (user_object, error_message)
        """
        # Extract user identifier
        email = user_info.get('email') or user_info.get('email_address')
        username = (
            user_info.get('preferred_username') or 
            user_info.get('username') or 
            (email.split('@')[0] if email else None)
        )
        
        if not email:
            return None, ERROR_EMAIL_NOT_FOUND
        
        if not username:
            return None, ERROR_USERNAME_NOT_FOUND
        
        # Try to find existing user by email or username
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User.query.filter_by(username=username).first()
        
        if not user:
            # Create new user
            user = User(username=username, email=email)
            # Set a random password (won't be used for Identity Server auth)
            user.set_password(secrets.token_urlsafe(32))
            db.session.add(user)
            
            from app.models.user import UserProfile
            profile = UserProfile(
                user_id=user.id,
                display_name=(
                    user_info.get('name') or 
                    user_info.get('display_name') or 
                    username
                )
            )
            db.session.add(profile)
            
            try:
                db.session.commit()
                logger.info(f"Created new user from Identity Server: {username}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating user: {e}")
                return None, str(e)
        else:
            # Update user info if needed
            if user.profile and user_info.get('name'):
                user.profile.display_name = user_info.get('name')
                try:
                    db.session.commit()
                except Exception as e:
                    logger.warning(f"Error updating user profile: {e}")
        
        return user, None
    
    def login(self, access_token: str, client_id: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Login using Identity Server OAuth token
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID
            
        Returns:
            Tuple of (login_result, error_message)
        """
        # Validate token and get user info
        is_valid, user_info, error = self.validate_token(access_token, client_id)
        if not is_valid:
            return None, error
        
        # Get or create local user
        user, error = self.get_or_create_user(user_info)
        if not user:
            return None, error
        
        # Create local JWT token for session management
        # JWT identity must be a string, not an integer
        local_token = create_access_token(identity=str(user.id))
        
        return {
            'access_token': local_token,
            'oauth_token': access_token,  # Also return OAuth token
            'user': user.to_dict()
        }, None
    
    def get_user_role(self, access_token: str, client_id: str) -> Optional[str]:
        """
        Get user's role from Identity Server
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID
            
        Returns:
            Role name or None
        """
        if not self.client:
            return None
        
        try:
            role_info = self.client.get_user_role(client_id, access_token)
            if role_info:
                return role_info.get('role') or role_info.get('Role')
        except Exception as e:
            logger.error(f"Error getting user role: {e}")
        
        return None
