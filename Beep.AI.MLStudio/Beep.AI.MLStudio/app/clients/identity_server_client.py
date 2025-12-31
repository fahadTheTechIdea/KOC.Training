"""
Identity Server Client
Handles communication with Beep.Foundation.IdentityServer
"""
import requests
import logging
from typing import Optional, Tuple, Dict
from app.models.auth_config import AuthConfig

logger = logging.getLogger(__name__)


class IdentityServerClient:
    """Client for Identity Server OAuth2/OIDC operations"""
    
    def __init__(self, base_url: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize Identity Server client
        
        Args:
            base_url: Identity Server base URL (if None, gets from AuthConfig)
            client_id: OAuth client ID (if None, gets from AuthConfig)
            client_secret: OAuth client secret (if None, gets from AuthConfig)
        """
        if base_url is None or client_id is None or client_secret is None:
            try:
                auth_config = AuthConfig.get_config()
                self.base_url = base_url or (auth_config.identity_server_url if auth_config else None)
                self.client_id = client_id or (auth_config.identity_server_client_id if auth_config else None)
                self.client_secret = client_secret or (auth_config.get_identity_server_client_secret() if auth_config else None)
            except Exception:
                # Database might not be initialized yet, use provided values or None
                self.base_url = base_url
                self.client_id = client_id
                self.client_secret = client_secret
        else:
            self.base_url = base_url
            self.client_id = client_id
            self.client_secret = client_secret
    
    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check Identity Server availability
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            health_url = f"{self.base_url.rstrip('/')}/.well-known/openid-configuration"
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                return True, None
            return False, f"Server returned status {response.status_code}"
        except Exception as e:
            return False, str(e)
    
    def validate_token(self, access_token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Validate OAuth access token
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Tuple of (is_valid, user_info, error_message)
        """
        try:
            # Use introspection endpoint
            introspect_url = f"{self.base_url.rstrip('/')}/connect/introspect"
            data = {
                'token': access_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            response = requests.post(introspect_url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('active'):
                    # Get user info
                    user_info_url = f"{self.base_url.rstrip('/')}/connect/userinfo"
                    headers = {'Authorization': f'Bearer {access_token}'}
                    user_response = requests.get(user_info_url, headers=headers, timeout=10)
                    
                    if user_response.status_code == 200:
                        user_info = user_response.json()
                        return True, user_info, None
                    else:
                        return True, None, f"Could not get user info: {user_response.status_code}"
                else:
                    return False, None, "Token is not active"
            else:
                return False, None, f"Token validation failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating token: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            return False, None, str(e)
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Identity Server
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User info dictionary or None
        """
        try:
            user_info_url = f"{self.base_url.rstrip('/')}/connect/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(user_info_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def check_user_access(self, user_id: str, application_id: str) -> bool:
        """
        Check if user has access to an application
        
        Args:
            user_id: User ID
            application_id: Application ID
            
        Returns:
            True if user has access
        """
        # This would depend on Identity Server's API
        # Placeholder implementation
        try:
            # Example: Check user permissions endpoint
            check_url = f"{self.base_url.rstrip('/')}/api/users/{user_id}/applications/{application_id}/access"
            response = requests.get(check_url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_user_role(self, user_id: str) -> Optional[str]:
        """
        Get user role from Identity Server
        
        Args:
            user_id: User ID
            
        Returns:
            User role or None
        """
        try:
            role_url = f"{self.base_url.rstrip('/')}/api/users/{user_id}/role"
            response = requests.get(role_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('role')
            return None
        except Exception:
            return None
