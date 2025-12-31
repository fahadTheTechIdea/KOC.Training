"""
Settings Manager Service
Centralized configuration management with config.json support
Priority: config.json > database settings > environment variables > defaults
"""
import os
import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional, Dict, List
from app import db
from app.models.settings import Settings

logger = logging.getLogger(__name__)


class SettingsManager:
    """Centralized settings manager with config.json support"""
    
    _instance = None
    _settings_cache = {}
    _config_file_cache = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_config_file()
            self._initialize_settings()
            SettingsManager._initialized = True
    
    def _get_app_directory(self) -> Path:
        """Get the application directory"""
        # If running as frozen executable (PyInstaller)
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        # Running as script - use script's parent directory
        return Path(__file__).parent.parent.parent
    
    def _load_config_file(self):
        """Load configuration from config.json file (if exists)"""
        config_file = self._get_app_directory() / 'config.json'
        if not config_file.exists():
            logger.debug("No config.json file found, using database settings and defaults")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self._config_file_cache = config_data
                logger.info(f"Loaded config.json from {config_file}")
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}")
            self._config_file_cache = {}
    
    def _initialize_settings(self):
        """Initialize default settings if they don't exist"""
        # Only initialize if we're in an application context
        from flask import has_app_context
        if not has_app_context():
            logger.warning("No application context, skipping settings initialization")
            return
        
        try:
            # Check if settings table exists
            from sqlalchemy import inspect
            try:
                inspector = inspect(db.engine)
                if 'settings' not in inspector.get_table_names():
                    logger.warning("Settings table does not exist yet, skipping initialization")
                    return
            except Exception as e:
                logger.warning(f"Could not check table existence: {e}")
                return
            
            default_settings = Settings.get_default_settings()
            settings_added = 0
            
            for setting_def in default_settings:
                try:
                    existing = Settings.query.filter_by(key=setting_def['key']).first()
                    if not existing:
                        setting = Settings(
                            key=setting_def['key'],
                            category=setting_def['category'],
                            value_type=setting_def['value_type'],
                            description=setting_def.get('description', ''),
                            is_encrypted=setting_def.get('is_encrypted', False)
                        )
                        setting.set_value(setting_def['value'])
                        db.session.add(setting)
                        settings_added += 1
                except Exception as e:
                    logger.warning(f"Error adding setting {setting_def.get('key', 'unknown')}: {e}")
                    continue
            
            if settings_added > 0:
                db.session.commit()
                logger.info(f"Settings initialized successfully: {settings_added} settings added")
            else:
                logger.info("Settings already initialized")
        except Exception as e:
            logger.error(f"Error initializing settings: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                db.session.rollback()
            except:
                pass
    
    def get(self, key: str, default: Any = None, category: Optional[str] = None) -> Any:
        """
        Get a setting value with priority: config.json > database > env vars > default
        
        Args:
            key: Setting key
            default: Default value if setting not found
            category: Optional category filter
            
        Returns:
            Setting value or default
        """
        # Check cache first
        cache_key = f"{category}:{key}" if category else key
        if cache_key in self._settings_cache:
            return self._settings_cache[cache_key]
        
        # Priority 1: Check config.json file
        if self._config_file_cache:
            # Try direct key access
            if key in self._config_file_cache:
                value = self._config_file_cache[key]
                self._settings_cache[cache_key] = value
                return value
            
            # Try nested access (e.g., mlstudio.community_url)
            if '.' in key:
                parts = key.split('.')
                current = self._config_file_cache
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                if current is not None:
                    self._settings_cache[cache_key] = current
                    return current
        
        # Priority 2: Check environment variables
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Try to convert to appropriate type
            try:
                if env_value.lower() in ('true', '1', 'yes', 'on'):
                    env_value = True
                elif env_value.lower() in ('false', '0', 'no', 'off'):
                    env_value = False
                elif env_value.replace('.', '', 1).isdigit():
                    env_value = float(env_value) if '.' in env_value else int(env_value)
            except:
                pass
            self._settings_cache[cache_key] = env_value
            return env_value
        
        # Priority 3: Check database (only if we're in an application context)
        from flask import has_app_context
        if has_app_context():
            try:
                query = Settings.query.filter_by(key=key)
                if category:
                    query = query.filter_by(category=category)
                
                setting = query.first()
                if setting:
                    value = setting.get_value()
                    self._settings_cache[cache_key] = value
                    return value
            except Exception as e:
                logger.error(f"Error getting setting {key} from database: {e}")
        
        # Priority 4: Return default
        return default
    
    def set(self, key: str, value: Any, category: Optional[str] = None, 
            value_type: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
            category: Setting category
            value_type: Value type (string, number, boolean, json, path)
            description: Setting description
            
        Returns:
            True if successful
        """
        try:
            setting = Settings.query.filter_by(key=key).first()
            
            if not setting:
                # Create new setting
                if not category:
                    # Try to infer category from key
                    category = self._infer_category(key)
                if not value_type:
                    value_type = self._infer_value_type(value)
                
                setting = Settings(
                    key=key,
                    category=category or 'general',
                    value_type=value_type or 'string',
                    description=description or ''
                )
                db.session.add(setting)
            else:
                # Update existing
                if category:
                    setting.category = category
                if value_type:
                    setting.value_type = value_type
                if description:
                    setting.description = description
            
            setting.set_value(value)
            db.session.commit()
            
            # Update cache
            cache_key = f"{setting.category}:{key}"
            self._settings_cache[cache_key] = setting.get_value()
            self._settings_cache[key] = setting.get_value()
            
            logger.info(f"Setting {key} updated to {value}")
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            db.session.rollback()
            return False
    
    def get_all(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all settings, optionally filtered by category
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary of settings
        """
        from flask import has_app_context
        if not has_app_context():
            logger.debug("No app context, returning empty settings")
            return {}
        
        try:
            query = Settings.query
            if category:
                query = query.filter_by(category=category)
            
            settings = query.all()
            return {s.key: s.get_value() for s in settings}
        except Exception as e:
            logger.error(f"Error getting all settings: {e}")
            return {}
    
    def get_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category"""
        return self.get_all(category=category)
    
    def get_categories(self) -> List[str]:
        """Get all setting categories"""
        from flask import has_app_context
        if not has_app_context():
            return []
        
        try:
            categories = db.session.query(Settings.category).distinct().all()
            return [cat[0] for cat in categories]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def delete(self, key: str) -> bool:
        """Delete a setting"""
        try:
            setting = Settings.query.filter_by(key=key).first()
            if setting:
                db.session.delete(setting)
                db.session.commit()
                
                # Remove from cache
                if key in self._settings_cache:
                    del self._settings_cache[key]
                
                logger.info(f"Setting {key} deleted")
                return True
        except Exception as e:
            logger.error(f"Error deleting setting {key}: {e}")
            db.session.rollback()
            return False
    
    def reset_to_defaults(self, category: Optional[str] = None) -> bool:
        """Reset settings to defaults"""
        try:
            default_settings = Settings.get_default_settings()
            
            for setting_def in default_settings:
                if category and setting_def['category'] != category:
                    continue
                
                setting = Settings.query.filter_by(key=setting_def['key']).first()
                if setting:
                    setting.set_value(setting_def['value'])
                else:
                    setting = Settings(
                        key=setting_def['key'],
                        category=setting_def['category'],
                        value_type=setting_def['value_type'],
                        description=setting_def.get('description', ''),
                        is_encrypted=setting_def.get('is_encrypted', False)
                    )
                    setting.set_value(setting_def['value'])
                    db.session.add(setting)
            
            db.session.commit()
            self._settings_cache.clear()
            logger.info("Settings reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            db.session.rollback()
            return False
    
    def _infer_category(self, key: str) -> str:
        """Infer category from key name"""
        key_lower = key.lower()
        if 'path' in key_lower or 'folder' in key_lower or 'directory' in key_lower:
            return 'paths'
        elif 'environment' in key_lower or 'env' in key_lower or 'python' in key_lower:
            return 'environment'
        elif 'model' in key_lower or 'train' in key_lower or 'ml' in key_lower:
            return 'ml'
        elif 'theme' in key_lower or 'ui' in key_lower or 'page' in key_lower:
            return 'ui'
        elif 'community' in key_lower:
            return 'community'
        elif 'microsoft' in key_lower or 'sso' in key_lower or 'azure' in key_lower:
            return 'microsoft_sso'
        else:
            return 'general'
    
    def _infer_value_type(self, value: Any) -> str:
        """Infer value type from value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, (int, float)):
            return 'number'
        elif isinstance(value, (dict, list)):
            return 'json'
        elif isinstance(value, str) and (os.path.sep in value or value.startswith('/') or ':' in value):
            return 'path'
        else:
            return 'string'
    
    # Convenience methods for common settings
    def get_projects_folder(self) -> Path:
        """Get projects folder path"""
        path = self.get('projects_folder', 'projects')
        return Path(path)
    
    def get_data_folder(self) -> Path:
        """Get data folder path"""
        path = self.get('data_folder', 'data')
        return Path(path)
    
    def get_models_folder(self) -> Path:
        """Get models folder path"""
        path = self.get('models_folder', 'models')
        return Path(path)
    
    def get_providers_folder(self) -> Path:
        """Get providers (environments) folder path"""
        path = self.get('providers_folder', 'providers')
        return Path(path)
    
    def get_python_embedded_path(self) -> Path:
        """Get embedded Python path"""
        path = self.get('python_embedded_path', 'python-embedded')
        return Path(path)
    
    def get_base_path(self) -> Path:
        """Get base application path"""
        path = self.get('base_path', '.')
        return Path(path).resolve()
    
    def get_host_admin_url(self) -> str:
        """Get Host Admin URL"""
        return self.get('host_admin_url', 'http://127.0.0.1:5000')
    
    def get_max_upload_size(self) -> int:
        """Get max upload size in bytes"""
        mb = self.get('max_upload_size_mb', 100)
        return int(mb) * 1024 * 1024
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('debug_mode', False)
    
    def get_default_framework(self) -> str:
        """Get default ML framework"""
        return self.get('default_framework', 'scikit-learn')
    
    # Community connection settings
    def get_community_connection(self) -> Dict[str, Any]:
        """
        Get Community connection configuration
        Priority: config.json > database settings > env vars > defaults
        """
        # Check config.json first
        if self._config_file_cache:
            mlstudio_config = self._config_file_cache.get('mlstudio', {})
            community_config = mlstudio_config.get('community_connection', {})
            if community_config:
                return {
                    'url': community_config.get('url', 'http://127.0.0.1:5001'),
                    'enabled': community_config.get('enabled', False),
                    'api_key': community_config.get('api_key', ''),
                    'timeout': community_config.get('timeout', 30)
                }
        
        # Check database settings
        return {
            'url': self.get('community_url', os.getenv('COMMUNITY_URL', 'http://127.0.0.1:5001'), category='community'),
            'enabled': self.get('community_enabled', os.getenv('COMMUNITY_ENABLED', 'false').lower() == 'true', category='community'),
            'api_key': self.get('community_api_key', os.getenv('COMMUNITY_API_KEY', ''), category='community'),
            'timeout': self.get('community_timeout', int(os.getenv('COMMUNITY_TIMEOUT', '30')), category='community')
        }
    
    # Microsoft SSO settings
    def get_microsoft_sso(self) -> Dict[str, Any]:
        """
        Get Microsoft SSO configuration
        Priority: config.json > database settings > env vars > defaults
        """
        # Check config.json first
        if self._config_file_cache:
            auth_config = self._config_file_cache.get('authentication', {})
            sso_config = auth_config.get('microsoft_sso', {})
            if sso_config:
                return {
                    'enabled': sso_config.get('enabled', False),
                    'client_id': sso_config.get('client_id', ''),
                    'client_secret': sso_config.get('client_secret', ''),
                    'tenant_id': sso_config.get('tenant_id', ''),
                    'redirect_uri': sso_config.get('redirect_uri_mlstudio', '')
                }
        
        # Check database settings
        return {
            'enabled': self.get('microsoft_sso_enabled', os.getenv('MICROSOFT_SSO_ENABLED', 'false').lower() == 'true', category='microsoft_sso'),
            'client_id': self.get('microsoft_client_id', os.getenv('MICROSOFT_CLIENT_ID', ''), category='microsoft_sso'),
            'client_secret': self.get('microsoft_client_secret', os.getenv('MICROSOFT_CLIENT_SECRET', ''), category='microsoft_sso'),
            'tenant_id': self.get('microsoft_tenant_id', os.getenv('MICROSOFT_TENANT_ID', ''), category='microsoft_sso'),
            'redirect_uri': self.get('microsoft_redirect_uri', os.getenv('MICROSOFT_REDIRECT_URI', ''), category='microsoft_sso')
        }
    
    def reload_config_file(self):
        """Reload config.json file (useful for testing or after file changes)"""
        self._config_file_cache = {}
        self._settings_cache = {}
        self._load_config_file()
        logger.info("Config file reloaded")


# Global instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager

