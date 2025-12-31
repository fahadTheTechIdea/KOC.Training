"""
Microsoft Graph Client
Handles communication with Microsoft Azure AD / Microsoft Graph API
"""
import requests
import logging
from typing import Optional, Dict
from app.models.auth_config import AuthConfig

logger = logging.getLogger(__name__)


class MicrosoftGraphClient:
    """Client for Microsoft Graph API operations"""
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize Microsoft Graph client
        
        Args:
            tenant_id: Azure AD tenant ID (if None, gets from AuthConfig)
            client_id: Azure AD client ID (if None, gets from AuthConfig)
            client_secret: Azure AD client secret (if None, gets from AuthConfig)
        """
        if tenant_id is None or client_id is None or client_secret is None:
            try:
                auth_config = AuthConfig.get_config()
                self.tenant_id = tenant_id or (auth_config.microsoft_tenant_id if auth_config else None)
                self.client_id = client_id or (auth_config.microsoft_client_id if auth_config else None)
                self.client_secret = client_secret or (auth_config.get_microsoft_client_secret() if auth_config else None)
            except Exception:
                # Database might not be initialized yet, use provided values or None
                self.tenant_id = tenant_id
                self.client_id = client_id
                self.client_secret = client_secret
        else:
            self.tenant_id = tenant_id
            self.client_id = client_id
            self.client_secret = client_secret
        
        self.token_endpoint = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token" if self.tenant_id else None
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
    
    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Get Microsoft Azure AD authorization URL
        
        Args:
            redirect_uri: OAuth redirect URI
            state: Optional state parameter
            
        Returns:
            Authorization URL
        """
        from urllib.parse import urlencode
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'response_mode': 'query',
            'scope': 'openid profile email User.Read',
            'state': state or ''
        }
        
        auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        return f"{auth_url}?{urlencode(params)}"
    
    def get_access_token(self, code: str, redirect_uri: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token
        
        Args:
            code: OAuth authorization code
            redirect_uri: OAuth redirect URI
            
        Returns:
            Token response dictionary or None
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            response = requests.post(self.token_endpoint, data=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting access token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_access_token: {e}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Microsoft Graph
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User info dictionary or None
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(f"{self.graph_endpoint}/me", headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                # Normalize user data to match our format
                return {
                    'id': user_data.get('id'),
                    'sub': user_data.get('id'),  # Use id as sub
                    'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                    'username': user_data.get('userPrincipalName') or user_data.get('mail'),
                    'preferred_username': user_data.get('userPrincipalName'),
                    'name': user_data.get('displayName'),
                    'display_name': user_data.get('displayName'),
                    'given_name': user_data.get('givenName'),
                    'surname': user_data.get('surname'),
                    'picture': None,  # Microsoft Graph doesn't return picture in /me endpoint
                    'avatar_url': None
                }
            else:
                logger.error(f"Error getting user info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in get_user_info: {e}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: OAuth refresh token
            
        Returns:
            Token response dictionary or None
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_endpoint, data=data, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error refreshing token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error in refresh_token: {e}")
            return None
