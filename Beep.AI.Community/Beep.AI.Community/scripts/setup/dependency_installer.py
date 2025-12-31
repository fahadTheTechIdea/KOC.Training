"""
Dependency Installer
"""
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def install_dependencies(venv_python: str, print_func=None) -> bool:
    """
    Install required packages from requirements.txt
    
    Args:
        venv_python: Path to virtual environment Python executable
        print_func: Optional function to print messages
        
    Returns:
        True if successful, False otherwise
    """
    requirements = Path('requirements.txt')
    if not requirements.exists():
        _print("❌ requirements.txt not found!", print_func)
        logger.error("requirements.txt not found")
        return False
    
    _print("📥 Installing dependencies...", print_func)
    
    # Upgrade pip first
    _print("   Upgrading pip...", print_func)
    subprocess.run(
        [venv_python, '-m', 'pip', 'install', '--upgrade', 'pip', '--quiet'],
        capture_output=True
    )
    
    # Install dependencies
    _print("   Installing packages from requirements.txt...", print_func)
    result = subprocess.run(
        [venv_python, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        _print("✅ Dependencies installed successfully", print_func)
        return True
    else:
        _print("❌ Failed to install dependencies!", print_func)
        if result.stderr:
            error_msg = result.stderr[-500:]
            _print(f"   Error: {error_msg}", print_func)
            logger.error(f"Dependency installation failed: {error_msg}")
        return False


def _print(message: str, print_func=None, end='\n'):
    """Print message using print_func if provided, otherwise use print"""
    if print_func:
        print_func(message, end=end)
    else:
        print(message, end=end)
