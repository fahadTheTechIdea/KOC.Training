"""
Embedded Python Download and Setup
"""
import os
import sys
import subprocess
import platform
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import requests (may not be available until dependencies are installed)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def download_embedded_python(print_func=None) -> Tuple[bool, Optional[str]]:
    """
    Automatically download and install embedded Python if not found
    
    Args:
        print_func: Optional function to print messages (for colored output)
        
    Returns:
        Tuple of (success, error_message)
    """
    embedded_path = Path('python-embedded')
    system = platform.system()
    machine = platform.machine().lower()
    
    if system == 'Windows':
        python_exe = embedded_path / 'python.exe'
        zip_file = Path('python-embedded.zip')
    else:
        python_exe = embedded_path / 'bin' / 'python3'
        zip_file = Path('python-embedded.tar.gz')
    
    if python_exe.exists():
        _print("✅ Embedded Python already installed", print_func)
        return True, None
    
    _print("🐍 Embedded Python not found. Downloading automatically...", print_func)
    _print("   This may take a few minutes...", print_func)
    
    try:
        # Determine download URL
        url = _get_python_download_url(system, machine)
        if not url:
            error = f"Unsupported platform: {system} {machine}"
            _print(f"❌ {error}", print_func)
            return False, error
        
        _print(f"   Downloading from: {url}", print_func)
        
        # Download
        if not _download_file(url, zip_file, print_func):
            return False, "Download failed"
        
        # Extract
        _print("   Extracting Python...", print_func)
        if not _extract_file(zip_file, embedded_path, system, print_func):
            return False, "Extraction failed"
        
        # Clean up
        if zip_file.exists():
            zip_file.unlink()
        
        # Configure embedded Python
        if system == 'Windows':
            _configure_windows_python(embedded_path, print_func)
        
        # Install pip
        _print("   Installing pip...", print_func)
        if not _install_pip(python_exe, print_func):
            return False, "Pip installation failed"
        
        if python_exe.exists():
            _print("✅ Embedded Python installed successfully!", print_func)
            return True, None
        else:
            error = "Embedded Python installation failed!"
            _print(f"❌ {error}", print_func)
            return False, error
            
    except Exception as e:
        error = f"Error downloading/installing embedded Python: {e}"
        logger.error(error, exc_info=True)
        _print(f"❌ {error}", print_func)
        return False, error


def _get_python_download_url(system: str, machine: str) -> Optional[str]:
    """Get download URL for embedded Python based on platform"""
    from app.utils.constants import (
        PYTHON_EMBEDDED_URL_WINDOWS,
        PYTHON_EMBEDDED_URL_LINUX_X64,
        PYTHON_EMBEDDED_URL_LINUX_ARM64,
        PYTHON_EMBEDDED_URL_MACOS_X64,
        PYTHON_EMBEDDED_URL_MACOS_ARM64
    )
    
    if system == 'Windows':
        return PYTHON_EMBEDDED_URL_WINDOWS
    elif system == 'Linux':
        arch = 'aarch64' if 'arm' in machine or 'aarch' in machine else 'x86_64'
        return PYTHON_EMBEDDED_URL_LINUX_ARM64 if arch == 'aarch64' else PYTHON_EMBEDDED_URL_LINUX_X64
    elif system == 'Darwin':  # macOS
        arch = 'aarch64' if 'arm' in machine or 'aarch' in machine else 'x86_64'
        return PYTHON_EMBEDDED_URL_MACOS_ARM64 if arch == 'aarch64' else PYTHON_EMBEDDED_URL_MACOS_X64
    
    return None


def _download_file(url: str, destination: Path, print_func=None) -> bool:
    """Download file from URL with progress"""
    embedded_path = destination.parent
    embedded_path.mkdir(exist_ok=True)
    
    try:
        if HAS_REQUESTS:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            _print(f"\r   Progress: {percent:.1f}%", print_func, end='')
            _print("", print_func)  # New line
        else:
            import urllib.request
            _print("   Downloading (this may take a while)...", print_func)
            urllib.request.urlretrieve(url, destination)
        
        return True
    except Exception as e:
        logger.error(f"Download failed: {e}")
        if destination.exists():
            destination.unlink()
        return False


def _extract_file(archive: Path, destination: Path, system: str, print_func=None) -> bool:
    """Extract archive file"""
    try:
        if system == 'Windows':
            import zipfile
            with zipfile.ZipFile(archive, 'r') as zip_ref:
                zip_ref.extractall(destination)
        else:
            import tarfile
            with tarfile.open(archive, 'r:gz') as tar:
                tar.extractall(destination)
                # Move contents up one level if needed
                extracted_dirs = [d for d in destination.iterdir() if d.is_dir()]
                if extracted_dirs:
                    import shutil
                    for item in extracted_dirs[0].iterdir():
                        shutil.move(str(item), str(destination / item.name))
                    extracted_dirs[0].rmdir()
        
        return True
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False


def _configure_windows_python(embedded_path: Path, print_func=None):
    """Configure Windows embedded Python"""
    _print("   Configuring embedded Python...", print_func)
    pth_file = embedded_path / 'python311._pth'
    if pth_file.exists():
        try:
            content = pth_file.read_text(encoding='utf-8')
            content = content.replace('#import site', 'import site')
            pth_file.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to configure Python .pth file: {e}")


def _install_pip(python_exe: Path, print_func=None) -> bool:
    """Install pip in embedded Python"""
    from app.utils.constants import PIP_INSTALL_URL
    
    try:
        if platform.system() == 'Windows':
            get_pip = python_exe.parent / 'get-pip.py'
            
            if HAS_REQUESTS:
                response = requests.get(PIP_INSTALL_URL, timeout=30)
                get_pip.write_bytes(response.content)
            else:
                import urllib.request
                urllib.request.urlretrieve(PIP_INSTALL_URL, get_pip)
            
            subprocess.run([str(python_exe), str(get_pip)], check=True, capture_output=True)
            get_pip.unlink()
        else:
            subprocess.run([str(python_exe), '-m', 'ensurepip'], check=True, capture_output=True)
        
        return True
    except Exception as e:
        logger.error(f"Pip installation failed: {e}")
        return False


def _print(message: str, print_func=None, end='\n'):
    """Print message using print_func if provided, otherwise use print"""
    if print_func:
        print_func(message, end=end)
    else:
        print(message, end=end)
