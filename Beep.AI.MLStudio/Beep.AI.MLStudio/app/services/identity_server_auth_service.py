"""
Identity Server Authentication Service
Handles OAuth2/OIDC authentication via Beep.Foundation.IdentityServer
"""
from typing import Optional, Tuple, Dict
from datetime import datetime
from app import db
from app.models.user import User, UserProfile
from app.models.auth_config import AuthConfig
from app.clients.identity_server_client import IdentityServerClient
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)


class IdentityServerAuthService:
    """Service for Identity Server OAuth2/OIDC authentication"""
    
    def __init__(self):
        """Initialize Identity Server auth service"""
        try:
            auth_config = AuthConfig.get_config()
            self.client = IdentityServerClient(
                base_url=auth_config.identity_server_url if auth_config else None,
                client_id=auth_config.identity_server_client_id if auth_config else None,
                client_secret=auth_config.get_identity_server_client_secret() if auth_config else None
            )
        except Exception:
            # Database might not be initialized yet, create client with None values
            self.client = IdentityServerClient()
    
    def validate_token(self, access_token: str, client_id: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate OAuth token and get user info
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID (optional, uses config if not provided)
            
        Returns:
            Tuple of (is_valid, user_info, error_message)
        """
        return self.client.validate_token(access_token)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Identity Server
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User info dictionary or None
        """
        return self.client.get_user_info(access_token)
    
    def get_or_create_user(self, user_info: Dict) -> Tuple[User, bool]:
        """
        Get or create user from Identity Server user info
        
        Args:
            user_info: User info from Identity Server
            
        Returns:
            Tuple of (user, created)
        """
        # Extract user identifier (could be sub, email, or username)
        user_id_from_server = user_info.get('sub') or user_info.get('id')
        email = user_info.get('email')
        username = user_info.get('preferred_username') or user_info.get('username') or email
        
        if not email and not username:
            raise ValueError("User info must contain email or username")
        
        # Try to find existing user by email or username
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        if not user and username:
            user = User.query.filter_by(username=username).first()
        
        if user:
            # Update user info
            if email and user.email != email:
                user.email = email
            if username and user.username != username:
                # Check if username is available
                existing = User.query.filter_by(username=username).first()
                if not existing or existing.id == user.id:
                    user.username = username
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()
            
            return user, False
        else:
            # Create new user
            user_data = {
                'username': username,
                'email': email or f"{username}@identityserver.local",
                'password': None,  # No password for Identity Server users
                'is_admin': user_info.get('role') == 'admin' or user_info.get('is_admin', False),
                'is_active': True
            }
            
            profile_data = {
                'display_name': user_info.get('name') or user_info.get('display_name') or username,
                'bio': user_info.get('bio'),
                'avatar_url': user_info.get('picture') or user_info.get('avatar_url')
            }
            
            user, error = UserService.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=None,  # No password for Identity Server users
                profile_data=profile_data,
                is_admin=user_data['is_admin']
            )
            
            if error:
                raise ValueError(f"Error creating user: {error}")
            
            return user, True
    
    def login(self, access_token: str, client_id: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Login with Identity Server OAuth token
        
        Args:
            access_token: OAuth access token
            client_id: OAuth client ID (optional)
            
        Returns:
            Tuple of (login_result_dict, error_message)
        """
        is_valid, user_info, error = self.validate_token(access_token, client_id)
        
        if not is_valid or not user_info:
            return None, error or "Invalid token"
        
        try:
            user, created = self.get_or_create_user(user_info)
            
            # Return user info (no JWT token needed, using OAuth token)
            return {
                'access_token': access_token,  # Return the OAuth token
                'user': user.to_dict(),
                'created': created
            }, None
            
        except Exception as e:
            logger.error(f"Error in Identity Server login: {e}")
            return None, str(e)
