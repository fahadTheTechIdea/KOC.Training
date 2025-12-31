"""
Microsoft SSO Authentication Service
Handles OAuth2/OIDC authentication via Microsoft Azure AD
"""
from typing import Optional, Tuple, Dict
from datetime import datetime
from app import db
from app.models.user import User
from app.models.auth_config import AuthConfig
from app.clients.microsoft_graph_client import MicrosoftGraphClient
from app.services.user_service import UserService
from flask_jwt_extended import create_access_token
import logging

logger = logging.getLogger(__name__)


class MicrosoftSSOService:
    """Service for Microsoft Azure AD SSO authentication"""
    
    def __init__(self):
        """Initialize Microsoft SSO service"""
        try:
            auth_config = AuthConfig.get_config()
            self.client = MicrosoftGraphClient(
                tenant_id=auth_config.microsoft_tenant_id if auth_config else None,
                client_id=auth_config.microsoft_client_id if auth_config else None,
                client_secret=auth_config.get_microsoft_client_secret() if auth_config else None
            )
            self.redirect_uri = auth_config.microsoft_redirect_uri if auth_config else None
        except Exception:
            # Database might not be initialized yet, create client with None values
            self.client = MicrosoftGraphClient()
            self.redirect_uri = None
    
    def get_authorization_url(self, redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
        """
        Get Microsoft Azure AD authorization URL
        
        Args:
            redirect_uri: OAuth redirect URI (if None, uses config)
            state: Optional state parameter
            
        Returns:
            Authorization URL
        """
        redirect_uri = redirect_uri or self.redirect_uri
        if not redirect_uri:
            raise ValueError("Redirect URI must be configured")
        return self.client.get_authorization_url(redirect_uri, state)
    
    def handle_callback(self, code: str, state: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Handle OAuth callback from Microsoft
        
        Args:
            code: OAuth authorization code
            state: OAuth state parameter
            
        Returns:
            Tuple of (login_result_dict, error_message)
        """
        try:
            redirect_uri = self.redirect_uri
            if not redirect_uri:
                return None, "Redirect URI not configured"
            
            # Exchange code for access token
            token_response = self.client.get_access_token(code, redirect_uri)
            if not token_response:
                return None, "Failed to get access token"
            
            access_token = token_response.get('access_token')
            if not access_token:
                return None, "No access token in response"
            
            # Get user info
            user_info = self.client.get_user_info(access_token)
            if not user_info:
                return None, "Failed to get user information"
            
            # Get or create user
            user, created = self.get_or_create_user(user_info)
            
            # Create JWT token for our system (we use Microsoft token for external calls)
            auth_config = AuthConfig.get_config()
            expires_delta = None
            if auth_config and auth_config.jwt_token_expires:
                from datetime import timedelta
                expires_delta = timedelta(seconds=auth_config.jwt_token_expires)
            
            jwt_token = create_access_token(identity=user.id, expires_delta=expires_delta)
            
            return {
                'access_token': jwt_token,  # Our JWT token
                'microsoft_token': access_token,  # Microsoft token for Graph API calls
                'refresh_token': token_response.get('refresh_token'),
                'user': user.to_dict(),
                'created': created
            }, None
            
        except Exception as e:
            logger.error(f"Error in Microsoft SSO callback: {e}")
            return None, str(e)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Microsoft Graph
        
        Args:
            access_token: Microsoft OAuth access token
            
        Returns:
            User info dictionary or None
        """
        return self.client.get_user_info(access_token)
    
    def get_or_create_user(self, user_info: Dict) -> Tuple[User, bool]:
        """
        Get or create user from Microsoft user info
        
        Args:
            user_info: User info from Microsoft Graph
            
        Returns:
            Tuple of (user, created)
        """
        # Extract user identifier
        email = user_info.get('email') or user_info.get('userPrincipalName')
        username = user_info.get('username') or user_info.get('preferred_username') or email
        
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
            profile_data = {
                'display_name': user_info.get('name') or user_info.get('display_name') or username,
                'bio': None,
                'avatar_url': user_info.get('picture') or user_info.get('avatar_url')
            }
            
            user, error = UserService.create_user(
                username=username,
                email=email or f"{username}@microsoft.local",
                password=None,  # No password for Microsoft SSO users
                profile_data=profile_data,
                is_admin=False  # Microsoft SSO users are not admins by default
            )
            
            if error:
                raise ValueError(f"Error creating user: {error}")
            
            return user, True
