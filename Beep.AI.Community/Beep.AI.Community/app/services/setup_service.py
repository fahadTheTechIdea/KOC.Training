"""
Setup Service - Business logic for setup wizard
Extracted from routes to improve separation of concerns
"""
import os
import logging
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

from app.utils.database_provider import DatabaseProviderHelper
from app.utils.env_manager import get_env_manager
from app.utils.constants import (
    DB_PROVIDER_SQLITE,
    AUTH_MODE_LOCAL,
    AUTH_MODE_IDENTITY_SERVER,
    ERROR_DB_PROVIDER_UNSUPPORTED,
    ERROR_DB_CONNECTION_FAILED,
    ERROR_INVALID_AUTH_MODE,
    ERROR_IDENTITY_SERVER_REQUIRED,
    ERROR_CANNOT_CONNECT_IDENTITY_SERVER,
    MSG_DATABASE_CONFIGURED,
    MSG_IDENTITY_SERVER_CONFIGURED,
    MSG_LOCAL_AUTH_CONFIGURED
)
from app.exceptions.setup_exceptions import (
    SetupValidationError,
    SetupConfigurationError
)
from app.exceptions.database_exceptions import (
    UnsupportedDatabaseProviderError,
    DatabaseConnectionError,
    DatabaseConfigurationError
)
from app.exceptions.auth_exceptions import IdentityServerError

logger = logging.getLogger(__name__)


class SetupService:
    """Service for setup wizard business logic"""
    
    def __init__(self):
        self.env_manager = get_env_manager()
        self.db_helper = DatabaseProviderHelper
    
    def _get_instance_dir(self) -> Path:
        """
        Get absolute path to instance directory (project root)
        
        Returns:
            Path to instance directory
        """
        # setup_service.py is in app/services/, so go up 3 levels to get project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'instance'
    
    # ==================== Database Configuration ====================
    
    def configure_database(
        self, 
        provider: str, 
        connection_string: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Configure database provider and connection string
        
        Args:
            provider: Database provider name
            connection_string: Optional connection string
            
        Returns:
            Tuple of (success, message)
        """
        provider = provider.lower()
        
        # Validate provider
        supported_providers = self.db_helper.get_supported_providers()
        if provider not in supported_providers:
            raise UnsupportedDatabaseProviderError(
                provider, 
                list(supported_providers.keys())
            )
        
        # Generate connection string for SQLite if not provided
        if not connection_string:
            if provider == DB_PROVIDER_SQLITE:
                connection_string = 'sqlite:///community.db'
            else:
                raise SetupValidationError(
                    f'Connection string is required for {supported_providers[provider]["name"]}'
                )
        
        # Validate connection string format
        is_valid, error = self.db_helper.validate_connection_string(
            provider, 
            connection_string
        )
        if not is_valid:
            raise DatabaseConfigurationError(error, provider)
        
        # Test connection
        success, error = self.db_helper.test_connection(connection_string)
        if not success:
            raise DatabaseConnectionError(
                f'{ERROR_DB_CONNECTION_FAILED}: {error}',
                connection_string
            )
        
        # Store in .env file
        self.env_manager.set('DATABASE_URL', connection_string)
        self.env_manager.set('DATABASE_PROVIDER', provider)
        
        provider_name = supported_providers[provider]["name"]
        message = f'{provider_name} {MSG_DATABASE_CONFIGURED}'
        
        logger.info(f"Database configured: {provider}")
        return True, message
    
    def test_database_connection(
        self, 
        provider: str, 
        connection_string: str
    ) -> Tuple[bool, str]:
        """
        Test database connection
        
        Args:
            provider: Database provider name
            connection_string: Connection string to test
            
        Returns:
            Tuple of (success, error_message)
        """
        if not connection_string:
            return False, "Connection string is required"
        
        # Validate format
        is_valid, error = self.db_helper.validate_connection_string(
            provider, 
            connection_string
        )
        if not is_valid:
            return False, error
        
        # Test connection
        success, error = self.db_helper.test_connection(connection_string)
        return success, error or ""
    
    # ==================== Authentication Configuration ====================
    
    def configure_authentication(
        self,
        auth_mode: str,
        identity_server_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uris: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Configure authentication mode
        
        Args:
            auth_mode: Authentication mode ('local' or 'identity_server')
            identity_server_url: Identity Server URL (required for identity_server mode)
            client_id: OAuth client ID (required for identity_server mode)
            client_secret: OAuth client secret
            redirect_uris: OAuth redirect URIs
            
        Returns:
            Tuple of (success, message)
        """
        auth_mode = auth_mode.lower()
        
        if auth_mode not in [AUTH_MODE_LOCAL, AUTH_MODE_IDENTITY_SERVER]:
            raise SetupValidationError(ERROR_INVALID_AUTH_MODE)
        
        # Store authentication mode
        self.env_manager.set('AUTH_MODE', auth_mode)
        
        if auth_mode == AUTH_MODE_IDENTITY_SERVER:
            return self._configure_identity_server(
                identity_server_url,
                client_id,
                client_secret,
                redirect_uris
            )
        else:
            return self._configure_local_auth()
    
    def _configure_identity_server(
        self,
        identity_server_url: Optional[str],
        client_id: Optional[str],
        client_secret: Optional[str],
        redirect_uris: Optional[str]
    ) -> Tuple[bool, str]:
        """Configure Identity Server authentication"""
        if not identity_server_url or not client_id:
            raise SetupValidationError(ERROR_IDENTITY_SERVER_REQUIRED)
        
        # Test connection
        try:
            from app.clients.identity_server_client import IdentityServerClient
            
            client = IdentityServerClient(
                base_url=identity_server_url,
                client_id=client_id,
                client_secret=client_secret
            )
            success, message = client.test_connection(identity_server_url)
            
            if not success:
                raise IdentityServerError(
                    f'{ERROR_CANNOT_CONNECT_IDENTITY_SERVER}: {message}'
                )
        except ImportError:
            raise IdentityServerError("Identity Server client not available")
        except Exception as e:
            raise IdentityServerError(f"Failed to connect to Identity Server: {str(e)}")
        
        # Store configuration
        self.env_manager.set('IDENTITY_SERVER_URL', identity_server_url)
        self.env_manager.set('IDENTITY_SERVER_CLIENT_ID', client_id)
        
        if client_secret:
            self.env_manager.set('IDENTITY_SERVER_CLIENT_SECRET', client_secret)
        if redirect_uris:
            self.env_manager.set('IDENTITY_SERVER_REDIRECT_URIS', redirect_uris)
        
        logger.info("Identity Server authentication configured")
        return True, MSG_IDENTITY_SERVER_CONFIGURED
    
    def _configure_local_auth(self) -> Tuple[bool, str]:
        """Configure local JWT authentication"""
        # Clear Identity Server settings
        self.env_manager.remove('IDENTITY_SERVER_URL', create_backup=False)
        self.env_manager.remove('IDENTITY_SERVER_CLIENT_ID', create_backup=False)
        self.env_manager.remove('IDENTITY_SERVER_CLIENT_SECRET', create_backup=False)
        self.env_manager.remove('IDENTITY_SERVER_REDIRECT_URIS', create_backup=False)
        
        logger.info("Local JWT authentication configured")
        return True, MSG_LOCAL_AUTH_CONFIGURED
    
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
            return False, ERROR_IDENTITY_SERVER_REQUIRED
        
        try:
            from app.clients.identity_server_client import IdentityServerClient
            
            client = IdentityServerClient(
                base_url=identity_server_url,
                client_id=client_id,
                client_secret=client_secret
            )
            return client.test_connection(identity_server_url)
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
            # Reload environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            # Get database URL from environment
            db_url = os.getenv('DATABASE_URL', 'sqlite:///community.db')
            
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
            from app.services.branding_service import BrandingService
            
            # Check if database is initialized (models available)
            try:
                has_admin = User.query.filter_by(is_admin=True).first() is not None
            except Exception:
                has_admin = False
            
            return {
                'configured': self.is_setup_complete(),
                'has_admin': has_admin,
                'has_branding': BrandingService.is_configured(),
                'database_provider': self.env_manager.get('DATABASE_PROVIDER', DB_PROVIDER_SQLITE),
                'auth_mode': self.env_manager.get('AUTH_MODE', AUTH_MODE_LOCAL)
            }
        except Exception as e:
            logger.error(f"Error getting setup status: {e}")
            return {
                'configured': False,
                'has_admin': False,
                'has_branding': False,
                'database_provider': DB_PROVIDER_SQLITE,
                'auth_mode': AUTH_MODE_LOCAL
            }
