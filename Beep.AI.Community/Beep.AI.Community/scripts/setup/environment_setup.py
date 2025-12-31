"""
Environment Setup - File and directory creation
"""
import shutil
import logging
from pathlib import Path
from typing import Optional

from app.utils.constants import (
    ENV_FILE,
    ENV_EXAMPLE_FILE,
    DIR_UPLOADS,
    DIR_UPLOADS_DATASETS,
    DIR_UPLOADS_NOTEBOOKS,
    DIR_UPLOADS_SUBMISSIONS,
    DIR_INSTANCE,
    DEFAULT_SECRET_KEY,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_DATABASE_URL,
    DEFAULT_DATABASE_PROVIDER,
    DEFAULT_AUTH_MODE,
    DEFAULT_MAX_UPLOAD_SIZE_MB,
    DEFAULT_UPLOAD_FOLDER,
    DEFAULT_REDIS_URL,
    DEFAULT_AISERVER_URL,
    DEFAULT_MLSTUDIO_URL
)

logger = logging.getLogger(__name__)


def setup_environment_file(print_func=None) -> bool:
    """
    Create .env file if it doesn't exist
    
    Args:
        print_func: Optional function to print messages
        
    Returns:
        True if successful, False otherwise
    """
    env_file = Path(ENV_FILE)
    env_example = Path(ENV_EXAMPLE_FILE)
    
    if not env_file.exists():
        _print("⚙️  Creating .env file...", print_func)
        if env_example.exists():
            try:
                shutil.copy(env_example, env_file)
                _print(f"✅ .env file created from {ENV_EXAMPLE_FILE}", print_func)
                return True
            except Exception as e:
                logger.error(f"Failed to copy .env.example: {e}")
                return False
        else:
            # Create default .env
            default_env = _get_default_env_content()
            try:
                env_file.write_text(default_env)
                _print("✅ Default .env file created", print_func)
                return True
            except Exception as e:
                logger.error(f"Failed to create default .env: {e}")
                return False
    
    return True


def create_directories(print_func=None) -> bool:
    """
    Create necessary directories
    
    Args:
        print_func: Optional function to print messages
        
    Returns:
        True if successful, False otherwise
    """
    dirs = [
        DIR_UPLOADS,
        DIR_UPLOADS_DATASETS,
        DIR_UPLOADS_NOTEBOOKS,
        DIR_UPLOADS_SUBMISSIONS,
        DIR_INSTANCE
    ]
    
    try:
        for dir_name in dirs:
            Path(dir_name).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        _print(f"❌ Failed to create directories: {e}", print_func)
        return False


def _get_default_env_content() -> str:
    """Get default .env file content"""
    return f"""# Flask Configuration
SECRET_KEY={DEFAULT_SECRET_KEY}
DEBUG=true
FLASK_ENV=development
HOST={DEFAULT_HOST}
PORT={DEFAULT_PORT}

# Database (configured via Setup Wizard)
DATABASE_URL={DEFAULT_DATABASE_URL}
DATABASE_PROVIDER={DEFAULT_DATABASE_PROVIDER}

# Authentication Mode (configured via Setup Wizard)
# Options: local, identity_server
AUTH_MODE={DEFAULT_AUTH_MODE}

# Identity Server (if AUTH_MODE=identity_server)
# IDENTITY_SERVER_URL=https://identityserver.com
# IDENTITY_SERVER_CLIENT_ID=your_client_id
# IDENTITY_SERVER_CLIENT_SECRET=your_client_secret

# File Upload
MAX_UPLOAD_SIZE={DEFAULT_MAX_UPLOAD_SIZE_MB}
UPLOAD_FOLDER={DEFAULT_UPLOAD_FOLDER}

# Redis (optional)
REDIS_URL={DEFAULT_REDIS_URL}

# Beep.AI.Server Integration
AISERVER_URL={DEFAULT_AISERVER_URL}
AISERVER_API_KEY=

# MLStudio Integration
MLSTUDIO_URL={DEFAULT_MLSTUDIO_URL}
"""


def _print(message: str, print_func=None, end='\n'):
    """Print message using print_func if provided, otherwise use print"""
    if print_func:
        print_func(message, end=end)
    else:
        print(message, end=end)
