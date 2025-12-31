"""
Setup Service - Business logic for setup wizard
"""
import os
import logging
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

from app.models.auth_config import AuthConfig
from app import db

logger = logging.getLogger(__name__)


class SetupService:
    """Service for setup wizard business logic"""
    
    def _get_instance_dir(self) -> Path:
        """
        Get absolute path to instance directory (project root)
        
        Returns:
            Path to instance directory
        """
        # setup_service.py is in app/services/, so go up 3 levels to get project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'instance'
    
    # ==================== Authentication Configuration ====================
    
    def configure_authentication(
        self,
        auth_mode: str,
        identity_server_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        microsoft_tenant_id: Optional[str] = None,
        microsoft_client_id: Optional[str] = None,
        microsoft_client_secret: Optional[str] = None,
        microsoft_redirect_uri: Optional[str] = None,
        jwt_secret_key: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Configure authentication mode (stored in database via AuthConfig)
        
        Args:
            auth_mode: Authentication mode ('local', 'identity_server', 'microsoft_sso')
            identity_server_url: Identity Server URL (for identity_server mode)
            client_id: OAuth client ID (for identity_server mode)
            client_secret: OAuth client secret (for identity_server mode)
            microsoft_tenant_id: Microsoft tenant ID (for microsoft_sso mode)
            microsoft_client_id: Microsoft client ID (for microsoft_sso mode)
            microsoft_client_secret: Microsoft client secret (for microsoft_sso mode)
            microsoft_redirect_uri: Microsoft redirect URI (for microsoft_sso mode)
            jwt_secret_key: JWT secret key (for local mode)
            
        Returns:
            Tuple of (success, message)
        """
        auth_mode = auth_mode.lower()
        
        if auth_mode not in ['local', 'identity_server', 'microsoft_sso']:
            return False, f"Invalid authentication mode: {auth_mode}"
        
        try:
            # Get or create AuthConfig
            auth_config = AuthConfig.get_config()
            
            # Update auth mode
            auth_config.auth_mode = auth_mode
            
            if auth_mode == 'identity_server':
                if not identity_server_url or not client_id:
                    return False, "Identity Server URL and Client ID are required"
                
                auth_config.identity_server_url = identity_server_url
                auth_config.identity_server_client_id = client_id
                if client_secret:
                    auth_config.set_identity_server_client_secret(client_secret)
                
                # Test connection
                try:
                    from app.clients.identity_server_client import IdentityServerClient
                    client = IdentityServerClient(
                        base_url=identity_server_url,
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    success, error = client.health_check()
                    if not success:
                        return False, f"Could not connect to Identity Server: {error}"
                except Exception as e:
                    logger.warning(f"Could not test Identity Server connection: {e}")
            
            elif auth_mode == 'microsoft_sso':
                if not microsoft_tenant_id or not microsoft_client_id:
                    return False, "Microsoft Tenant ID and Client ID are required"
                
                auth_config.microsoft_tenant_id = microsoft_tenant_id
                auth_config.microsoft_client_id = microsoft_client_id
                if microsoft_client_secret:
                    auth_config.set_microsoft_client_secret(microsoft_client_secret)
                if microsoft_redirect_uri:
                    auth_config.microsoft_redirect_uri = microsoft_redirect_uri
            
            # Set JWT secret key (for local mode or as fallback)
            if jwt_secret_key:
                auth_config.set_jwt_secret_key(jwt_secret_key)
            elif auth_mode == 'local' and not auth_config.get_jwt_secret_key():
                # Generate a default JWT secret if not set
                import secrets
                auth_config.set_jwt_secret_key(secrets.token_hex(32))
            
            db.session.commit()
            
            logger.info(f"Authentication configured: {auth_mode}")
            return True, f"Authentication mode '{auth_mode}' configured successfully"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error configuring authentication: {e}")
            return False, f"Failed to configure authentication: {str(e)}"
    
    def test_identity_server_connection(
        self,
        identity_server_url: str,
        client_id: str,
        client_secret: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Test Identity Server connection
        
        Args:
            identity_server_url: Identity Server URL
            client_id: OAuth client ID
            client_secret: Optional OAuth client secret
            
        Returns:
            Tuple of (success, message)
        """
        if not identity_server_url or not client_id:
            return False, "Identity Server URL and Client ID are required"
        
        try:
            from app.clients.identity_server_client import IdentityServerClient
            
            client = IdentityServerClient(
                base_url=identity_server_url,
                client_id=client_id,
                client_secret=client_secret
            )
            return client.health_check()
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    # ==================== Setup Completion ====================
    
    def complete_setup(self) -> Tuple[bool, str]:
        """
        Complete setup by creating database schema
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create all database tables
            db.create_all()
            
            # Mark setup as complete - use absolute path
            instance_dir = self._get_instance_dir()
            config_file = instance_dir / 'setup_complete.json'
            instance_dir.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(config_file, 'w') as f:
                json.dump({'setup_complete': True}, f)
            
            logger.info("Setup completed successfully")
            return True, "Setup completed successfully"
            
        except Exception as e:
            error_msg = f"Failed to complete setup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def is_setup_complete(self) -> bool:
        """
        Check if setup is complete
        
        Returns:
            True if setup is complete, False otherwise
        """
        # Use absolute path for consistency
        instance_dir = self._get_instance_dir()
        config_file = instance_dir / 'setup_complete.json'
        if not config_file.exists():
            return False
        
        try:
            import json
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('setup_complete', False)
        except Exception:
            return False
    
    def get_setup_status(self) -> Dict[str, Any]:
        """
        Get current setup status
        
        Returns:
            Dictionary with setup status information
        """
        try:
            from app.models.user import User
            
            # Check if database is initialized (models available)
            try:
                has_admin = User.query.filter_by(is_admin=True).first() is not None
            except Exception:
                has_admin = False
            
            # Get auth mode from AuthConfig
            try:
                auth_config = AuthConfig.get_config()
                auth_mode = auth_config.auth_mode if auth_config else 'local'
            except Exception:
                auth_mode = 'local'
            
            return {
                'configured': self.is_setup_complete(),
                'has_admin': has_admin,
                'auth_mode': auth_mode
            }
        except Exception as e:
            logger.error(f"Error getting setup status: {e}")
            return {
                'configured': False,
                'has_admin': False,
                'auth_mode': 'local'
            }
