#!/usr/bin/env python3
"""
Beep.AI.Community - Cross-Platform Launcher
Automatically sets up and runs Beep.AI.Community Platform
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

# Import setup modules
try:
    from scripts.setup import embedded_python
    from scripts.setup import venv_manager
    from scripts.setup import dependency_installer
    from scripts.setup import environment_setup
except ImportError:
    # If scripts package not available, fall back to inline functions
    embedded_python = None
    venv_manager = None
    dependency_installer = None
    environment_setup = None

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.RESET, end='\n'):
    """Print colored message (works on Unix, plain text on Windows)"""
    try:
        if platform.system() == 'Windows':
            print(message, end=end)
        else:
            print(f"{color}{message}{Colors.RESET}", end=end)
    except UnicodeEncodeError:
        # Fallback: replace emoji with ASCII equivalents
        message = message.replace('✅', '[OK]')
        message = message.replace('❌', '[ERROR]')
        message = message.replace('⚠️', '[WARN]')
        message = message.replace('📦', '[INFO]')
        message = message.replace('📥', '[INFO]')
        message = message.replace('⚙️', '[INFO]')
        message = message.replace('🗄️', '[INFO]')
        message = message.replace('🔍', '[INFO]')
        message = message.replace('📁', '[INFO]')
        message = message.replace('🚀', '[INFO]')
        message = message.replace('👋', '[INFO]')
        message = message.replace('📋', '[INFO]')
        print(message, end=end)

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print_colored("❌ Python 3.8 or higher is required!", Colors.RED)
        print_colored(f"   Current version: {sys.version}", Colors.YELLOW)
        sys.exit(1)
    print_colored(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", Colors.GREEN)

def setup_virtual_environment():
    """Create and setup virtual environment using modular script"""
    if venv_manager:
        return venv_manager.setup_virtual_environment(print_colored)
    else:
        # Fallback to inline implementation
        return _setup_virtual_environment_inline()

def install_dependencies(venv_python):
    """Install required packages using modular script"""
    if dependency_installer:
        success = dependency_installer.install_dependencies(venv_python, print_colored)
        if not success:
            sys.exit(1)
    else:
        # Fallback to inline implementation
        _install_dependencies_inline(venv_python)

def download_embedded_python():
    """Download embedded Python using modular script"""
    if embedded_python:
        success, error = embedded_python.download_embedded_python(print_colored)
        return success
    else:
        # Fallback to inline implementation
        return _download_embedded_python_inline()

def setup_environment_file():
    """Create .env file using modular script"""
    if environment_setup:
        environment_setup.setup_environment_file(print_colored)
    else:
        # Fallback to inline implementation
        _setup_environment_file_inline()

def create_directories():
    """Create directories using modular script"""
    if environment_setup:
        environment_setup.create_directories(print_colored)
    else:
        # Fallback to inline implementation
        _create_directories_inline()

# Fallback inline implementations (kept for compatibility)
def _setup_virtual_environment_inline():
    """Fallback inline implementation - uses sys.executable (embedded Python when called from batch file)"""
    venv_path = Path('.venv')
    
    if platform.system() == 'Windows':
        venv_python = venv_path / 'Scripts' / 'python.exe'
    else:
        venv_python = venv_path / 'bin' / 'python'
    
    # CRITICAL: Ensure pip, setuptools, and wheel are installed/upgraded first (same as ML Studio)
    print_colored("   Ensuring pip, setuptools, and wheel are installed...", Colors.CYAN)
    try:
        pip_upgrade = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel', '--quiet', '--no-warn-script-location'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if pip_upgrade.returncode == 0:
            print_colored("   ✅ pip, setuptools, and wheel ready", Colors.GREEN)
    except Exception as e:
        print_colored(f"   ⚠️  Warning: Could not upgrade pip: {e}", Colors.YELLOW)
    
    # Install virtualenv package by default (works even if standard venv module has issues)
    print_colored("   Ensuring virtualenv package is installed...", Colors.CYAN)
    virtualenv_check = subprocess.run(
        [sys.executable, '-m', 'pip', 'show', 'virtualenv'],
        capture_output=True,
        text=True
    )
    
    if virtualenv_check.returncode != 0:
        print_colored("   Installing virtualenv package...", Colors.CYAN)
        install_result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'virtualenv', '--quiet', '--no-warn-script-location'],
            capture_output=True,
            text=True
        )
        if install_result.returncode == 0:
            print_colored("   ✅ virtualenv package installed", Colors.GREEN)
        else:
            print_colored("   ⚠️  Failed to install virtualenv, trying standard venv...", Colors.YELLOW)
    else:
        print_colored("   ✅ virtualenv package already installed", Colors.GREEN)
    
    # Check if venv exists but is incomplete (missing python executable)
    venv_exists_but_incomplete = venv_path.exists() and not venv_python.exists()
    
    if not venv_path.exists() or venv_exists_but_incomplete:
        if venv_exists_but_incomplete:
            print_colored("   Cleaning up incomplete virtual environment...", Colors.CYAN)
            try:
                import shutil
                shutil.rmtree(venv_path)
            except Exception as e:
                print_colored(f"   ⚠️  Could not clean up: {e}, continuing anyway...", Colors.YELLOW)
        
        print_colored("📦 Creating virtual environment...", Colors.CYAN)
        # Try virtualenv package first (more reliable with embedded Python)
        virtualenv_success = False
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'virtualenv', '.venv'],
                capture_output=True,
                text=True,
                timeout=180
            )
            if result.returncode == 0:
                if venv_python.exists():
                    print_colored("✅ Virtual environment created (using virtualenv package)", Colors.GREEN)
                    virtualenv_success = True
                else:
                    print_colored("   ⚠️  virtualenv created directory but python.exe is missing", Colors.YELLOW)
        except subprocess.TimeoutExpired:
            print_colored("   ⚠️  virtualenv timed out", Colors.YELLOW)
        except Exception as e:
            print_colored(f"   ⚠️  virtualenv exception: {e}", Colors.YELLOW)
        
        # If virtualenv failed, try standard venv module
        if not virtualenv_success:
            print_colored("   Trying standard venv module...", Colors.CYAN)
            try:
                venv_result = subprocess.run(
                    [sys.executable, '-m', 'venv', '.venv'],
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if venv_result.returncode == 0:
                    if venv_python.exists():
                        print_colored("✅ Virtual environment created (using standard venv module)", Colors.GREEN)
                    else:
                        print_colored("❌ venv created directory but python.exe is missing", Colors.RED)
                        sys.exit(1)
                else:
                    print_colored("❌ Failed to create virtual environment: Both virtualenv and venv failed", Colors.RED)
                    if venv_result.stderr:
                        print_colored(f"   Error: {venv_result.stderr[:300]}", Colors.RED)
                    sys.exit(1)
            except subprocess.TimeoutExpired:
                print_colored("❌ venv creation timed out", Colors.RED)
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print_colored(f"❌ Failed to create virtual environment: {e}", Colors.RED)
                stderr_text = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr if e.stderr else '')
                if stderr_text:
                    print_colored(f"   Error: {stderr_text[:300]}", Colors.RED)
                print_colored("   Both virtualenv package and standard venv module failed.", Colors.YELLOW)
                sys.exit(1)
    
    # Final verification
    if not venv_python.exists():
        print_colored(f"❌ Virtual environment setup failed! Python not found at: {venv_python}", Colors.RED)
        print_colored("   This usually means embedded Python is not properly configured.", Colors.YELLOW)
        sys.exit(1)
    
    return str(venv_python)

def _install_dependencies_inline(venv_python):
    """Fallback inline implementation"""
    requirements = Path('requirements.txt')
    if not requirements.exists():
        print_colored("❌ requirements.txt not found!", Colors.RED)
        sys.exit(1)
    
    print_colored("📥 Installing dependencies...", Colors.CYAN)
    result = subprocess.run(
        [venv_python, '-m', 'pip', 'install', '-r', 'requirements.txt'],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print_colored("❌ Failed to install dependencies!", Colors.RED)
        sys.exit(1)
    
    print_colored("✅ Dependencies installed successfully", Colors.GREEN)

def _download_embedded_python_inline():
    """Fallback inline implementation"""
    print_colored("🐍 Embedded Python download not available (scripts package not found)", Colors.YELLOW)
    return True  # Continue anyway

def _setup_environment_file_inline():
    """Fallback inline implementation"""
    env_file = Path('.env')
    if not env_file.exists():
        print_colored("⚙️  Creating .env file...", Colors.CYAN)
        env_file.write_text("SECRET_KEY=community-dev-secret-key\n")
        print_colored("✅ Default .env file created", Colors.GREEN)

def _create_directories_inline():
    """Fallback inline implementation"""
    dirs = ['uploads', 'uploads/datasets', 'uploads/notebooks', 'uploads/submissions', 'instance']
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)

def verify_dependencies(venv_python):
    """Verify critical dependencies are installed"""
    print_colored("   Verifying critical dependencies...", Colors.CYAN)
    critical_packages = ['flask', 'flask-sqlalchemy', 'flask-cors']
    missing = []
    
    for pkg in critical_packages:
        check_result = subprocess.run(
            [str(venv_python), '-m', 'pip', 'show', pkg],
            capture_output=True,
            text=True
        )
        if check_result.returncode != 0:
            missing.append(pkg)
    
    if missing:
        print_colored(f"   Installing missing packages: {', '.join(missing)}...", Colors.YELLOW)
        for pkg in missing:
            subprocess.run(
                [str(venv_python), '-m', 'pip', 'install', pkg],
                capture_output=True,
                text=True
            )
        print_colored("✅ All dependencies verified", Colors.GREEN)
    else:
        print_colored("✅ All dependencies verified", Colors.GREEN)

def run_community(venv_python, extra_args=None):
    """Run Beep.AI.Community application"""
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("🚀 Starting Beep.AI.Community", Colors.BOLD + Colors.GREEN)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("", Colors.RESET)
    
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    cmd = [str(venv_python), 'run.py']
    if extra_args:
        cmd.extend(extra_args)
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(script_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        
    except KeyboardInterrupt:
        print_colored("\n\n👋 Beep.AI.Community stopped by user", Colors.CYAN)
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print_colored(f"\n❌ Error running Beep.AI.Community: {e}", Colors.RED)
        import traceback
        traceback.print_exc()

def main():
    """Main launcher function"""
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Beep.AI.Community - Setup & Launcher')
    parser.add_argument('--port', type=int, default=5001, help='Port number (default: 5001)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    # Parse known args (ignore unknown for now, pass them to run.py)
    args, unknown_args = parser.parse_known_args()
    
    # Build extra args list for run.py
    extra_args = []
    extra_args.append(f'--port={args.port}')
    if args.host:
        extra_args.append(f'--host={args.host}')
    if args.debug:
        extra_args.append('--debug')
    if args.no_browser:
        extra_args.append('--no-browser')
    
    # Add any unknown args (for future compatibility)
    extra_args.extend(unknown_args)
    
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.BLUE)
    print_colored("  Beep.AI.Community - Setup & Launcher", Colors.BOLD)
    print_colored("=" * 60, Colors.BLUE)
    print_colored("", Colors.RESET)
    
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Setup steps
    check_python_version()
    
    # Setup embedded Python FIRST (optional, can use system Python)
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("🐍 Embedded Python Setup", Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    download_embedded_python()  # Try to download, continue even if fails (can use system Python)
    
    # Setup virtual environment
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("📦 Virtual Environment Setup", Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    venv_python = setup_virtual_environment()
    if not venv_python:
        print_colored("❌ Failed to create virtual environment!", Colors.RED)
        sys.exit(1)
    
    # Install dependencies
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("📥 Installing Dependencies", Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    install_dependencies(venv_python)
    
    # Verify critical dependencies
    verify_dependencies(venv_python)
    
    # Configuration
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("⚙️  Configuration", Colors.BOLD)
    print_colored("=" * 60, Colors.CYAN)
    setup_environment_file()
    create_directories()
    
    # Run application
    print_colored("", Colors.RESET)
    print_colored("=" * 60, Colors.GREEN)
    print_colored("✅ Setup Complete - Starting Beep.AI.Community", Colors.BOLD + Colors.GREEN)
    print_colored("=" * 60, Colors.GREEN)
    if args.port != 5001 or args.host != '127.0.0.1':
        print_colored(f"   Server: http://{args.host}:{args.port}", Colors.CYAN)
    print_colored("", Colors.RESET)
    run_community(venv_python, extra_args)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n👋 Goodbye!", Colors.CYAN)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        sys.exit(1)
