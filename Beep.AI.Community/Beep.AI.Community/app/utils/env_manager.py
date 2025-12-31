"""
Environment File Manager
Centralized .env file operations with validation and safety features
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class EnvManager:
    """Manager for .env file operations"""
    
    def __init__(self, env_file_path: str = '.env'):
        """
        Initialize environment file manager
        
        Args:
            env_file_path: Path to .env file
        """
        self.env_file = Path(env_file_path)
        self.backup_dir = Path('instance/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def read_all(self) -> Dict[str, str]:
        """
        Read all environment variables from .env file
        
        Returns:
            Dictionary of key-value pairs
        """
        if not self.env_file.exists():
            return {}
        
        env_vars = {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            raise
        
        return env_vars
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value from .env file
        
        Args:
            key: Environment variable name
            default: Default value if key not found
            
        Returns:
            Value of the environment variable or default
        """
        env_vars = self.read_all()
        return env_vars.get(key, default)
    
    def set(self, key: str, value: str, create_backup: bool = True) -> bool:
        """
        Set or update environment variable in .env file
        
        Args:
            key: Environment variable name
            value: Value to set
            create_backup: Whether to create backup before modification
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create backup if requested
            if create_backup and self.env_file.exists():
                self._create_backup()
            
            # Read existing content
            lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # Update or add the key
            updated = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                # Skip comments and empty lines
                if stripped.startswith('#'):
                    continue
                
                if stripped.startswith(f'{key}='):
                    # Update existing line
                    lines[i] = f'{key}={value}\n'
                    updated = True
                    break
            
            if not updated:
                # Add new line
                lines.append(f'{key}={value}\n')
            
            # Write back to file
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.debug(f"Updated .env file: {key}={value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            return False
    
    def remove(self, key: str, create_backup: bool = True) -> bool:
        """
        Remove environment variable from .env file
        
        Args:
            key: Environment variable name to remove
            create_backup: Whether to create backup before modification
            
        Returns:
            True if successful, False otherwise
        """
        if not self.env_file.exists():
            return True
        
        try:
            # Create backup if requested
            if create_backup:
                self._create_backup()
            
            # Read and filter out the key
            lines = []
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped = line.strip()
                    # Skip lines with the key
                    if stripped.startswith(f'{key}='):
                        continue
                    lines.append(line)
            
            # Write back to file
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.debug(f"Removed from .env file: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing from .env file: {e}")
            return False
    
    def set_multiple(self, variables: Dict[str, str], create_backup: bool = True) -> bool:
        """
        Set multiple environment variables at once
        
        Args:
            variables: Dictionary of key-value pairs
            create_backup: Whether to create backup before modification
            
        Returns:
            True if all successful, False otherwise
        """
        try:
            # Create backup once for all updates
            if create_backup and self.env_file.exists():
                self._create_backup()
            
            # Read existing content
            env_vars = self.read_all()
            
            # Update with new values
            env_vars.update(variables)
            
            # Write all back to file
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f'{key}={value}\n')
            
            logger.debug(f"Updated .env file with {len(variables)} variables")
            return True
            
        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            return False
    
    def _create_backup(self) -> Optional[Path]:
        """
        Create backup of .env file
        
        Returns:
            Path to backup file or None if failed
        """
        if not self.env_file.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'.env.backup_{timestamp}'
            shutil.copy2(self.env_file, backup_file)
            
            # Keep only last 5 backups
            backups = sorted(self.backup_dir.glob('.env.backup_*'))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    old_backup.unlink()
            
            logger.debug(f"Created .env backup: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.warning(f"Failed to create .env backup: {e}")
            return None
    
    def exists(self) -> bool:
        """Check if .env file exists"""
        return self.env_file.exists()
    
    def create_from_example(self, example_file: str = '.env.example') -> bool:
        """
        Create .env file from .env.example
        
        Args:
            example_file: Path to .env.example file
            
        Returns:
            True if successful, False otherwise
        """
        example_path = Path(example_file)
        if not example_path.exists():
            return False
        
        try:
            shutil.copy2(example_path, self.env_file)
            logger.info(f"Created .env file from {example_file}")
            return True
        except Exception as e:
            logger.error(f"Error creating .env from example: {e}")
            return False
    
    def validate_key(self, key: str) -> bool:
        """
        Validate environment variable key format
        
        Args:
            key: Environment variable name
            
        Returns:
            True if valid, False otherwise
        """
        if not key:
            return False
        
        # Environment variable names should be uppercase, alphanumeric, and underscores
        return key.replace('_', '').isalnum() and key.isupper()


# Singleton instance
_env_manager_instance: Optional[EnvManager] = None


def get_env_manager() -> EnvManager:
    """
    Get singleton EnvManager instance
    
    Returns:
        EnvManager instance
    """
    global _env_manager_instance
    if _env_manager_instance is None:
        _env_manager_instance = EnvManager()
    return _env_manager_instance
