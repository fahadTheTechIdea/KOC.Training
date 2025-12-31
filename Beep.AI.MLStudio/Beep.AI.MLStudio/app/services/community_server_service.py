"""
Community Server Service
Manages global (admin-configured) and user-specific community server connections
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from app import db
from app.models.user_community_server import UserCommunityServer
from app.models.global_community_server import GlobalCommunityServer
import logging
import requests

logger = logging.getLogger(__name__)


class CommunityServerService:
    """Service for managing community server connections"""
    
    @staticmethod
    def get_global_servers() -> List[GlobalCommunityServer]:
        """Get all global community servers (admin only)"""
        return GlobalCommunityServer.query.filter_by(is_active=True).order_by(GlobalCommunityServer.is_default.desc(), GlobalCommunityServer.created_at.desc()).all()
    
    @staticmethod
    def create_global_server(server_data: Dict, created_by: int) -> Tuple[Optional[GlobalCommunityServer], Optional[str]]:
        """
        Create a global community server (admin only)
        
        Args:
            server_data: Server data (server_name, server_url, api_key, description, is_default)
            created_by: Admin user ID who created it
            
        Returns:
            Tuple of (server, error_message)
        """
        try:
            # If setting as default, unset other defaults
            if server_data.get('is_default'):
                GlobalCommunityServer.query.update({'is_default': False})
            
            server = GlobalCommunityServer(
                server_name=server_data.get('server_name'),
                server_url=server_data.get('server_url'),
                description=server_data.get('description'),
                is_active=server_data.get('is_active', True),
                is_default=server_data.get('is_default', False),
                created_by=created_by
            )
            server.set_api_key(server_data.get('api_key', ''))
            
            db.session.add(server)
            db.session.commit()
            
            logger.info(f"Global community server created: {server.server_name}")
            return server, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating global server: {e}")
            return None, str(e)
    
    @staticmethod
    def update_global_server(server_id: int, server_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Update a global community server (admin only)
        
        Args:
            server_id: Server ID
            server_data: Update data
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            server = GlobalCommunityServer.query.get(server_id)
            if not server:
                return False, "Server not found"
            
            # If setting as default, unset other defaults
            if server_data.get('is_default'):
                GlobalCommunityServer.query.filter(GlobalCommunityServer.id != server_id).update({'is_default': False})
            
            if 'server_name' in server_data:
                server.server_name = server_data['server_name']
            
            if 'server_url' in server_data:
                server.server_url = server_data['server_url']
            
            if 'description' in server_data:
                server.description = server_data['description']
            
            if 'is_active' in server_data:
                server.is_active = server_data['is_active']
            
            if 'is_default' in server_data:
                server.is_default = server_data['is_default']
            
            if 'api_key' in server_data:
                server.set_api_key(server_data['api_key'])
            
            db.session.commit()
            
            logger.info(f"Global community server updated: {server_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating global server: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_global_server(server_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a global community server (admin only)
        
        Args:
            server_id: Server ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            server = GlobalCommunityServer.query.get(server_id)
            if not server:
                return False, "Server not found"
            
            db.session.delete(server)
            db.session.commit()
            
            logger.info(f"Global community server deleted: {server_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting global server: {e}")
            return False, str(e)
    
    @staticmethod
    def get_user_servers(user_id: int) -> List[UserCommunityServer]:
        """Get user's community servers"""
        return UserCommunityServer.query.filter_by(user_id=user_id, is_active=True).order_by(UserCommunityServer.is_default.desc(), UserCommunityServer.created_at.desc()).all()
    
    @staticmethod
    def create_user_server(user_id: int, server_data: Dict) -> Tuple[Optional[UserCommunityServer], Optional[str]]:
        """
        Create a user-specific community server
        
        Args:
            user_id: User ID
            server_data: Server data (server_name, server_url, api_key, is_default)
            
        Returns:
            Tuple of (server, error_message)
        """
        try:
            # If setting as default, unset other defaults for this user
            if server_data.get('is_default'):
                UserCommunityServer.query.filter_by(user_id=user_id).update({'is_default': False})
            
            server = UserCommunityServer(
                user_id=user_id,
                server_name=server_data.get('server_name'),
                server_url=server_data.get('server_url'),
                is_active=server_data.get('is_active', True),
                is_default=server_data.get('is_default', False)
            )
            server.set_api_key(server_data.get('api_key', ''))
            
            db.session.add(server)
            db.session.commit()
            
            logger.info(f"User community server created: {server.server_name} for user {user_id}")
            return server, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user server: {e}")
            return None, str(e)
    
    @staticmethod
    def update_user_server(server_id: int, user_id: int, server_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Update a user-specific community server
        
        Args:
            server_id: Server ID
            user_id: User ID (for ownership verification)
            server_data: Update data
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            server = UserCommunityServer.query.filter_by(id=server_id, user_id=user_id).first()
            if not server:
                return False, "Server not found or access denied"
            
            # If setting as default, unset other defaults for this user
            if server_data.get('is_default'):
                UserCommunityServer.query.filter(
                    UserCommunityServer.user_id == user_id,
                    UserCommunityServer.id != server_id
                ).update({'is_default': False})
            
            if 'server_name' in server_data:
                server.server_name = server_data['server_name']
            
            if 'server_url' in server_data:
                server.server_url = server_data['server_url']
            
            if 'is_active' in server_data:
                server.is_active = server_data['is_active']
            
            if 'is_default' in server_data:
                server.is_default = server_data['is_default']
            
            if 'api_key' in server_data:
                server.set_api_key(server_data['api_key'])
            
            db.session.commit()
            
            logger.info(f"User community server updated: {server_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user server: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_user_server(server_id: int, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Delete a user-specific community server
        
        Args:
            server_id: Server ID
            user_id: User ID (for ownership verification)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            server = UserCommunityServer.query.filter_by(id=server_id, user_id=user_id).first()
            if not server:
                return False, "Server not found or access denied"
            
            db.session.delete(server)
            db.session.commit()
            
            logger.info(f"User community server deleted: {server_id}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user server: {e}")
            return False, str(e)
    
    @staticmethod
    def get_available_servers(user_id: int) -> Dict:
        """
        Get all available servers for a user (global + user-specific)
        Priority: user default > user servers > global default > global servers
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with available servers and default server
        """
        # Get user's servers
        user_servers = UserCommunityServer.query.filter_by(user_id=user_id, is_active=True).all()
        
        # Get global servers
        global_servers = GlobalCommunityServer.query.filter_by(is_active=True).all()
        
        # Find default server (priority: user default > global default)
        default_server = None
        
        # Check for user default
        user_default = next((s for s in user_servers if s.is_default), None)
        if user_default:
            default_server = {
                'id': user_default.id,
                'server_name': user_default.server_name,
                'server_url': user_default.server_url,
                'api_key': user_default.get_api_key(),
                'type': 'user'
            }
        else:
            # Check for global default
            global_default = next((s for s in global_servers if s.is_default), None)
            if global_default:
                default_server = {
                    'id': global_default.id,
                    'server_name': global_default.server_name,
                    'server_url': global_default.server_url,
                    'api_key': global_default.get_api_key(),
                    'type': 'global'
                }
        
        return {
            'user_servers': [s.to_dict() for s in user_servers],
            'global_servers': [s.to_dict() for s in global_servers],
            'default_server': default_server
        }
    
    @staticmethod
    def set_default_server(user_id: int, server_id: int, server_type: str = 'user') -> Tuple[bool, Optional[str]]:
        """
        Set default server for a user
        
        Args:
            user_id: User ID
            server_id: Server ID
            server_type: 'user' or 'global'
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Unset all user defaults first
            UserCommunityServer.query.filter_by(user_id=user_id).update({'is_default': False})
            
            if server_type == 'user':
                server = UserCommunityServer.query.filter_by(id=server_id, user_id=user_id).first()
                if not server:
                    return False, "Server not found or access denied"
                server.is_default = True
            elif server_type == 'global':
                # For global servers, we can't set them as user defaults
                # Instead, we'll create a reference or just return the global server info
                global_server = GlobalCommunityServer.query.get(server_id)
                if not global_server:
                    return False, "Global server not found"
                # User can't set global as their default, but they can use it
                return True, None
            else:
                return False, "Invalid server type"
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting default server: {e}")
            return False, str(e)
    
    @staticmethod
    def test_connection(server_url: str, api_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Test connection to a community server
        
        Args:
            server_url: Server URL
            api_key: Optional API key
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Try to hit health check or API endpoint
            health_url = f"{server_url.rstrip('/')}/api/v1/health"
            response = requests.get(health_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, None
            else:
                return False, f"Server returned status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
