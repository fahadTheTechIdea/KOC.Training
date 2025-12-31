"""
Virtual Environment Manager
"""
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def setup_virtual_environment(print_func=None) -> Optional[str]:
    """
    Create and setup virtual environment using sys.executable (embedded Python when called from batch file)
    Same approach as ML Studio - uses sys.executable directly
    
    Args:
        print_func: Optional function to print messages
        
    Returns:
        Path to venv Python executable or None if failed
    """
    venv_path = Path('.venv')
    
    if platform.system() == 'Windows':
        venv_python = venv_path / 'Scripts' / 'python.exe'
    else:
        venv_python = venv_path / 'bin' / 'python'
    
    # Use sys.executable directly (same as ML Studio) - it's embedded Python when called from batch file
    python_executable = sys.executable
    
    # CRITICAL: Ensure pip, setuptools, and wheel are installed/upgraded first
    _print("   Ensuring pip, setuptools, and wheel are installed...", print_func)
    try:
        # Upgrade pip first
        pip_upgrade = subprocess.run(
            [python_executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel', '--quiet', '--no-warn-script-location'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if pip_upgrade.returncode == 0:
            _print("   ✅ pip, setuptools, and wheel ready", print_func)
        else:
            _print("   ⚠️  Warning: pip upgrade had issues, continuing anyway...", print_func)
            if pip_upgrade.stderr:
                logger.warning(f"Pip upgrade warning: {pip_upgrade.stderr[:200]}")
    except Exception as e:
        _print(f"   ⚠️  Warning: Could not upgrade pip: {e}", print_func)
        logger.warning(f"Pip upgrade failed: {e}")
    
    # Install virtualenv package by default (works even if standard venv module has issues)
    _print("   Ensuring virtualenv package is installed...", print_func)
    virtualenv_check = subprocess.run(
        [python_executable, '-m', 'pip', 'show', 'virtualenv'],
        capture_output=True,
        text=True
    )
    
    if virtualenv_check.returncode != 0:
        _print("   Installing virtualenv package...", print_func)
        install_result = subprocess.run(
            [python_executable, '-m', 'pip', 'install', 'virtualenv', '--quiet', '--no-warn-script-location'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if install_result.returncode == 0:
            _print("   ✅ virtualenv package installed", print_func)
        else:
            error_msg = install_result.stderr if install_result.stderr else install_result.stdout
            _print(f"   ⚠️  Failed to install virtualenv: {error_msg[:200] if error_msg else 'Unknown error'}", print_func)
            _print("   Will try standard venv module...", print_func)
            logger.warning(f"Virtualenv installation failed: {error_msg}")
    else:
        _print("   ✅ virtualenv package already installed", print_func)
    
    # Check if venv exists but is incomplete (missing python executable)
    venv_exists_but_incomplete = venv_path.exists() and not venv_python.exists()
    
    if not venv_path.exists() or venv_exists_but_incomplete:
        if venv_exists_but_incomplete:
            _print("   Cleaning up incomplete virtual environment...", print_func)
            try:
                import shutil
                shutil.rmtree(venv_path)
            except Exception as e:
                _print(f"   ⚠️  Could not clean up: {e}, continuing anyway...", print_func)
                logger.warning(f"Could not remove incomplete venv: {e}")
        
        _print("📦 Creating virtual environment...", print_func)
        # Try virtualenv package first (more reliable with embedded Python)
        virtualenv_success = False
        try:
            result = subprocess.run(
                [python_executable, '-m', 'virtualenv', '.venv'],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                if venv_python.exists():
                    _print("✅ Virtual environment created (using virtualenv package)", print_func)
                    virtualenv_success = True
                else:
                    _print("   ⚠️  virtualenv created directory but python.exe is missing", print_func)
                    if result.stderr:
                        _print(f"   virtualenv stderr: {result.stderr[:300]}", print_func)
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                _print(f"   ⚠️  virtualenv failed: {error_msg[:300] if error_msg else 'Unknown error'}", print_func)
        except subprocess.TimeoutExpired:
            _print("   ⚠️  virtualenv timed out", print_func)
        except Exception as e:
            _print(f"   ⚠️  virtualenv exception: {e}", print_func)
            logger.warning(f"Virtualenv exception: {e}")
        
        # If virtualenv failed, try standard venv module
        if not virtualenv_success:
            _print("   Trying standard venv module...", print_func)
            try:
                venv_result = subprocess.run(
                    [python_executable, '-m', 'venv', '.venv'],
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if venv_result.returncode == 0:
                    if venv_python.exists():
                        _print("✅ Virtual environment created (using standard venv module)", print_func)
                    else:
                        error = "venv created directory but python.exe is missing"
                        _print(f"❌ {error}", print_func)
                        if venv_result.stderr:
                            _print(f"   venv stderr: {venv_result.stderr[:300]}", print_func)
                        logger.error(error)
                        return None
                else:
                    error = "Failed to create virtual environment: Both virtualenv and venv failed"
                    _print(f"❌ {error}", print_func)
                    if venv_result.stderr:
                        _print(f"   venv error: {venv_result.stderr[:300]}", print_func)
                    logger.error(error)
                    return None
            except subprocess.TimeoutExpired:
                error = "venv creation timed out"
                _print(f"❌ {error}", print_func)
                logger.error(error)
                return None
            except subprocess.CalledProcessError as venv_error:
                error = "Failed to create virtual environment: Both virtualenv and venv failed"
                _print(f"❌ {error}", print_func)
                stderr_text = venv_error.stderr.decode() if isinstance(venv_error.stderr, bytes) else (venv_error.stderr if venv_error.stderr else '')
                if stderr_text:
                    _print(f"   Error: {stderr_text[:300]}", print_func)
                logger.error(error)
                return None
            except Exception as e:
                error = f"Failed to create virtual environment: {e}"
                _print(f"❌ {error}", print_func)
                logger.error(error, exc_info=True)
                return None
    
    # Final verification
    if not venv_python.exists():
        error = f"Virtual environment setup failed! Python not found at: {venv_python}"
        _print(f"❌ {error}", print_func)
        _print("   This usually means embedded Python is not properly configured.", print_func)
        _print("   Please ensure python311._pth has 'import site' uncommented.", print_func)
        logger.error(error)
        return None
    
    return str(venv_python)


def _print(message: str, print_func=None, end='\n'):
    """Print message using print_func if provided, otherwise use print"""
    if print_func:
        print_func(message, end=end)
    else:
        print(message, end=end)
