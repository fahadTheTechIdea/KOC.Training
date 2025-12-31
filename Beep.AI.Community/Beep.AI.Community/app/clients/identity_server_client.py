"""
Identity Server Client - Integration with Beep.Foundation.IdentityServer
"""
import requests
import logging
from typing import Dict, Optional, Any, List, Tuple
import os

from app.utils.constants import (
    ID_SERVER_ENDPOINT_HEALTH,
    ID_SERVER_ENDPOINT_TOKEN_VALIDATE,
    ID_SERVER_ENDPOINT_USER_ACCESS_CHECK,
    ID_SERVER_ENDPOINT_USER_ROLE,
    ID_SERVER_ENDPOINT_USER_APPLICATIONS,
    ID_SERVER_ENDPOINT_TOKEN,
    ID_SERVER_ENDPOINT_USERINFO,
    HTTP_TIMEOUT,
    HTTP_CONNECT_TIMEOUT,
    MSG_UNAUTHORIZED,
    MSG_FORBIDDEN,
    MSG_CONNECTION_ERROR,
    MSG_TIMEOUT_ERROR
)

logger = logging.getLogger(__name__)


class IdentityServerClient:
    """Client for Beep.Foundation.IdentityServer API"""
    
    def __init__(self, base_url: str = None, client_id: str = None, client_secret: str = None):
        """
        Initialize Identity Server client
        
        Args:
            base_url: Identity Server base URL (e.g., https://identityserver.com)
            client_id: OAuth client ID
            client_secret: OAuth client secret (for confidential clients)
        """
        self.base_url = (base_url or os.getenv('IDENTITY_SERVER_URL', '')).rstrip('/')
        self.client_id = client_id or os.getenv('IDENTITY_SERVER_CLIENT_ID', '')
        self.client_secret = client_secret or os.getenv('IDENTITY_SERVER_CLIENT_SECRET', '')
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, access_token: str = None, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to Identity Server
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            access_token: OAuth access token
            **kwargs: Additional request parameters
            
        Returns:
            Response JSON as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        headers = kwargs.pop('headers', {})
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        try:
            response = self.session.request(
                method, 
                url, 
                headers=headers,
                timeout=HTTP_TIMEOUT,
                **kwargs
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                return {'success': False, 'error': MSG_UNAUTHORIZED}
            elif response.status_code == 403:
                return {'success': False, 'error': MSG_FORBIDDEN}
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = error_data['error']
                    elif 'message' in error_data:
                        error_msg = error_data['message']
                except:
                    error_msg = response.text[:200]
                
                return {'success': False, 'error': error_msg}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Identity Server connection error: {e}")
            return {'success': False, 'error': MSG_CONNECTION_ERROR}
        except requests.exceptions.Timeout as e:
            logger.error(f"Identity Server timeout: {e}")
            return {'success': False, 'error': MSG_TIMEOUT_ERROR}
        except requests.exceptions.RequestException as e:
            logger.error(f"Identity Server request error: {e}")
            return {'success': False, 'error': f'Request failed: {str(e)}'}
        except Exception as e:
            logger.error(f"Identity Server request failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def health_check(self) -> bool:
        """
        Check if Identity Server is accessible
        
        Returns:
            True if accessible, False otherwise
        """
        if not self.base_url:
            return False
        
        try:
            result = self._request('GET', ID_SERVER_ENDPOINT_HEALTH)
            return result.get('status') == 'ok' or result.get('success', False)
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate OAuth access token
        
        Args:
            token: OAuth access token
            
        Returns:
            Validation result with token info
        """
        return self._request('GET', ID_SERVER_ENDPOINT_TOKEN_VALIDATE, access_token=token)
    
    def check_user_access(self, client_id: str, access_token: str) -> Dict[str, Any]:
        """
        Check if user has access to the application
        
        Args:
            client_id: OAuth application client ID
            access_token: OAuth access token
            
        Returns:
            Access check result with hasAccess, reason, etc.
        """
        endpoint = f'{ID_SERVER_ENDPOINT_USER_ACCESS_CHECK}/{client_id}'
        return self._request('GET', endpoint, access_token=access_token)
    
    def get_user_role(self, client_id: str, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user's role for the application
        
        Args:
            client_id: OAuth application client ID
            access_token: OAuth access token
            
        Returns:
            User role information or None if error
        """
        endpoint = f'{ID_SERVER_ENDPOINT_USER_ROLE}/{client_id}'
        result = self._request('GET', endpoint, access_token=access_token)
        
        if result.get('success', True) and 'error' not in result:
            return result
        return None
    
    def get_user_applications(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get list of applications user has access to
        
        Args:
            access_token: OAuth access token
            
        Returns:
            List of accessible applications
        """
        result = self._request('GET', ID_SERVER_ENDPOINT_USER_APPLICATIONS, access_token=access_token)
        
        if result.get('success', True) and 'applications' in result:
            return result['applications']
        elif isinstance(result, list):
            return result
        return []
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: OAuth refresh token
            
        Returns:
            New token information
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id
        }
        
        if self.client_secret:
            data['client_secret'] = self.client_secret
        
        return self._request('POST', ID_SERVER_ENDPOINT_TOKEN, data=data)
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Identity Server
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User information or None if error
        """
        result = self._request('GET', ID_SERVER_ENDPOINT_USERINFO, access_token=access_token)
        
        if result.get('success', True) and 'error' not in result:
            return result
        return None
    
    def test_connection(self, base_url: str = None, client_id: str = None) -> Tuple[bool, str]:
        """
        Test connection to Identity Server
        
        Args:
            base_url: Identity Server URL to test (optional, uses instance URL if not provided)
            client_id: Client ID to test (optional)
            
        Returns:
            Tuple of (success, message)
        """
        test_url = base_url or self.base_url
        if not test_url:
            return False, "Identity Server URL not configured"
        
        try:
            # Try to access a public endpoint or health check
            response = requests.get(f"{test_url.rstrip('/')}{ID_SERVER_ENDPOINT_HEALTH}", timeout=HTTP_CONNECT_TIMEOUT)
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"Server responded with status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Identity Server. Please check the URL."
        except requests.exceptions.Timeout:
            return False, "Connection timed out. Please check the URL."
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def send_branding_config(self, branding_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Send branding configuration to Identity Server
        
        Args:
            branding_config: Branding configuration dictionary matching C# BrandingConfig structure
            
        Returns:
            Tuple of (success, message)
        """
        if not self.base_url:
            return False, "Identity Server URL not configured"
        
        # Try common branding endpoints
        endpoints = [
            '/api/admin/branding',
            '/api/branding',
            '/api/config/branding',
            '/api/settings/branding'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                headers = {'Content-Type': 'application/json'}
                
                # Add client credentials if available (basic auth or client credentials grant)
                if self.client_id and self.client_secret:
                    import base64
                    credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
                    headers['Authorization'] = f'Basic {credentials}'
                
                response = requests.post(url, json=branding_config, headers=headers, timeout=HTTP_TIMEOUT)
                
                if response.status_code in [200, 201, 204]:
                    logger.info(f"Branding config sent successfully to {endpoint}")
                    return True, "Branding configuration sent successfully"
                elif response.status_code == 404:
                    # Endpoint doesn't exist, try next one
                    continue
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', error_data.get('message', error_msg))
                    except:
                        error_msg = response.text[:200] if response.text else error_msg
                    logger.debug(f"Failed to send branding to {endpoint}: {error_msg}")
                    continue
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {endpoint}: {e}")
                continue
        
        # If all endpoints fail, return error (but don't fail setup)
        logger.warning("Failed to send branding to Identity Server - all endpoints failed. Branding saved locally only.")
        return False, "Could not send branding to Identity Server, but saved locally. You can configure branding in Identity Server manually."
    
    def update_client_branding(self, client_id: str, branding: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update branding for a specific OAuth client
        
        Args:
            client_id: OAuth client ID
            branding: Branding configuration dictionary
            
        Returns:
            Tuple of (success, message)
        """
        if not self.base_url:
            return False, "Identity Server URL not configured"
        
        # Try client-specific branding endpoints
        endpoints = [
            f'/api/admin/clients/{client_id}/branding',
            f'/api/clients/{client_id}/branding',
            f'/api/config/clients/{client_id}/branding'
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                headers = {'Content-Type': 'application/json'}
                
                # Add client credentials if available
                if self.client_id and self.client_secret:
                    import base64
                    credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
                    headers['Authorization'] = f'Basic {credentials}'
                
                response = requests.put(url, json=branding, headers=headers, timeout=HTTP_TIMEOUT)
                
                if response.status_code in [200, 201, 204]:
                    logger.info(f"Client branding updated successfully for {client_id}")
                    return True, f"Branding updated for client {client_id}"
                elif response.status_code == 404:
                    continue
                else:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('error', error_data.get('message', error_msg))
                    except:
                        error_msg = response.text[:200] if response.text else error_msg
                    logger.debug(f"Failed to update client branding at {endpoint}: {error_msg}")
                    continue
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {endpoint}: {e}")
                continue
        
        return False, f"Failed to update branding for client {client_id}"


def get_identity_server_client() -> Optional[IdentityServerClient]:
    """
    Get configured Identity Server client instance
    
    Returns:
        IdentityServerClient instance if configured, None otherwise
    """
    base_url = os.getenv('IDENTITY_SERVER_URL')
    if not base_url:
        return None
    
    return IdentityServerClient(
        base_url=base_url,
        client_id=os.getenv('IDENTITY_SERVER_CLIENT_ID'),
        client_secret=os.getenv('IDENTITY_SERVER_CLIENT_SECRET')
    )
