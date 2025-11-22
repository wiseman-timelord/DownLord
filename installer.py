#!/usr/bin/env python3
# Script: `.\installer.py`

# Imports
import os
import time
import subprocess
import sys
import platform
from pathlib import Path
from typing import List, Tuple, Optional

# Constants
APP_TITLE = "DownLord"
MIN_PYTHON_VERSION = (3, 6)
BASE_DIR = Path(__file__).parent
VENV_DIR = BASE_DIR / ".venv"

# Determine platform once at startup
CURRENT_PLATFORM = "linux"  # Default to Linux
if len(sys.argv) > 1 and sys.argv[1].lower() == "windows":
    CURRENT_PLATFORM = "windows"
elif platform.system().lower().startswith("win"):
    CURRENT_PLATFORM = "windows"

# Directory Structure
APP_DIRECTORIES = [
    BASE_DIR / "data",
    BASE_DIR / "downloads",
    BASE_DIR / "scripts",
    BASE_DIR / "incomplete"
]

# File Paths
REQUIREMENTS_FILE = BASE_DIR / "data" / "requirements.txt"
INIT_FILE = BASE_DIR / "scripts" / "__init__.py"
PERSISTENT_FILE = BASE_DIR / "data" / "persistent.json"

# File Templates
REQUIREMENTS_TEXT = """requests>=2.31.0
tqdm>=4.66.1
urllib3>=2.1.0
pathlib>=1.0.1
"""

PERSISTENT_TEMPLATE = """{
    "chunk": 4096000,
    "retries": 100,
    "timeout_length": 120,
    "downloads_location": "downloads",
    "python_path": "%PYTHON_PATH%",
    "filename_1": "Empty",
    "filename_2": "Empty",
    "filename_3": "Empty",
    "filename_4": "Empty",
    "filename_5": "Empty",
    "filename_6": "Empty",
    "filename_7": "Empty",
    "filename_8": "Empty",
    "filename_9": "Empty",
    "url_1": "",
    "url_2": "",
    "url_3": "",
    "url_4": "",
    "url_5": "",
    "url_6": "",
    "url_7": "",
    "url_8": "",
    "url_9": "",
    "total_size_1": 0,
    "total_size_2": 0,
    "total_size_3": 0,
    "total_size_4": 0,
    "total_size_5": 0,
    "total_size_6": 0,
    "total_size_7": 0,
    "total_size_8": 0,
    "total_size_9": 0
}"""

def print_action(message: str, delay: float = 0.3) -> None:
    """Print action with status indicator."""
    print(f">> {message}", end=' ', flush=True)
    time.sleep(delay)
    print("[OK]")

def check_python_version() -> bool:
    """Verify Python version meets requirements."""
    if sys.version_info >= MIN_PYTHON_VERSION:
        version_str = '.'.join(map(str, MIN_PYTHON_VERSION))
        print_action(f"Python {version_str}+ confirmed")
        return True
    
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    required_version = '.'.join(map(str, MIN_PYTHON_VERSION))
    print(f"Error: Requires Python {required_version}+ - Found: {current_version}")
    return False

def setup_directories() -> bool:
    """Create all required directories with permission checks."""
    for directory in APP_DIRECTORIES:
        try:
            existed = directory.exists()
            directory.mkdir(exist_ok=True, mode=0o755)
            
            # Verify write permissions
            test_file = directory / ".test_write"
            test_file.touch()
            test_file.unlink()
            
            rel_path = directory.relative_to(BASE_DIR).as_posix()
            print_action(f"{'Verified' if existed else 'Created'} directory: {rel_path}")
        except (PermissionError, OSError) as e:
            print(f"Failed to create/access {directory.name}: {e}")
            if CURRENT_PLATFORM == "linux":
                print("Try running with 'sudo' or adjust permissions")
            return False
    return True

def create_file(path: Path, content: str, desc: str) -> bool:
    """Helper to create files with consistent messaging."""
    try:
        path.parent.mkdir(exist_ok=True, parents=True)
        with open(path, 'w') as f:
            f.write(content)
        rel_path = path.relative_to(BASE_DIR).as_posix()
        print_action(f"Created {desc}: {rel_path}")
        return True
    except Exception as e:
        print(f"Error creating {desc}: {e}")
        return False

def get_virtualenv_pip() -> Optional[Path]:
    """Get the path to the virtual environment's pip executable."""
    if CURRENT_PLATFORM == "windows":
        pip_path = VENV_DIR / "Scripts" / "pip.exe"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
    
    return pip_path if pip_path.exists() else None

def get_virtualenv_python() -> Optional[Path]:
    """Get the path to the virtual environment's python executable."""
    if CURRENT_PLATFORM == "windows":
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_path = VENV_DIR / "bin" / "python"
    
    return python_path if python_path.exists() else None

def upgrade_pip(venv_python: Path) -> bool:
    """Upgrade pip in the virtual environment."""
    try:
        print("Upgrading pip in virtual environment...")
        subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        print_action("Successfully upgraded pip")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error upgrading pip: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error upgrading pip: {e}")
        return False

def bootstrap_pip(venv_python: Path) -> bool:
    """Bootstrap pip into a virtual environment that's missing it."""
    try:
        print("Bootstrapping pip in virtual environment...")
        subprocess.run(
            [str(venv_python), "-m", "ensurepip", "--upgrade", "--default-pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        print_action("Successfully bootstrapped pip")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error bootstrapping pip: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error bootstrapping pip: {e}")
        return False

def setup_virtualenv() -> bool:
    """Create and activate a virtual environment."""
    venv_python = get_virtualenv_python()
    
    if venv_python:
        print_action("Virtual environment exists")
        
        # Ensure pip is present and upgraded
        pip_path = get_virtualenv_pip()
        if not pip_path:
            if not bootstrap_pip(venv_python):
                return False
        return upgrade_pip(venv_python)
    
    # Create new virtual environment
    try:
        print_action("Creating virtual environment")
        subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Get new venv python path
        venv_python = get_virtualenv_python()
        if not venv_python:
            print("Error: Virtual environment Python not found")
            return False
            
        # Bootstrap pip if needed
        pip_path = get_virtualenv_pip()
        if not pip_path:
            if not bootstrap_pip(venv_python):
                return False
                
        # Upgrade pip
        if not upgrade_pip(venv_python):
            return False
            
        print_action(f"Virtual environment created at: {VENV_DIR.relative_to(BASE_DIR).as_posix()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr}")
        print("Make sure the 'venv' module is available")
        if CURRENT_PLATFORM != "windows":
            print("On Ubuntu/Debian, try: sudo apt install python3-venv")
        return False
    except Exception as e:
        print(f"Unexpected error creating virtual environment: {e}")
        return False

def install_dependencies() -> bool:
    """Install required Python packages in virtual environment."""
    # Ensure virtual environment exists
    if not setup_virtualenv():
        return False
    
    # Get the virtual environment's pip
    pip_path = get_virtualenv_pip()
    if not pip_path:
        print("Error: Could not find pip in virtual environment")
        return False
    
    # Install requirements
    try:
        print_action("Installing dependencies in virtual environment")
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_action("Dependencies installed successfully")
            return True
        
        print(f"Package installation failed:\n{result.stderr}")
        return False
    except Exception as e:
        print(f"Installation error: {e}")
        return False

def setup_persistent_config() -> bool:
    """Handle persistent.json creation with Python path and overwrite confirmation."""
    # Get Python path
    python_path = sys.executable
    
    # Create config with Python path
    persistent_text = PERSISTENT_TEMPLATE.replace("%PYTHON_PATH%", python_path.replace("\\", "\\\\"))
    
    if PERSISTENT_FILE.exists():
        rel_path = PERSISTENT_FILE.relative_to(BASE_DIR).as_posix()
        print(f"\nConfig file exists: {rel_path}")
        print("Overwrite existing config? y=Yes, n=No")
        
        while True:
            try:
                # Use raw_input style approach with explicit prompt
                if CURRENT_PLATFORM == "windows":
                    # Windows: use msvcrt for direct character input
                    import msvcrt
                    print("Enter choice (y/n): ", end='', flush=True)
                    
                    # Read characters until we get a valid response or Enter
                    chars = []
                    while True:
                        if msvcrt.kbhit():
                            char = msvcrt.getch()
                            # Handle Enter key
                            if char in (b'\r', b'\n'):
                                print()  # New line after enter
                                break
                            # Handle backspace
                            elif char == b'\x08' and chars:
                                chars.pop()
                                print('\b \b', end='', flush=True)
                            # Handle printable characters
                            elif len(char) == 1 and 32 <= ord(char) < 127:
                                chars.append(char.decode('utf-8'))
                                print(char.decode('utf-8'), end='', flush=True)
                    
                    resp = ''.join(chars).strip().lower()
                else:
                    # Linux: use standard input
                    resp = input("Enter choice (y/n): ").strip().lower()
                
                if resp in {'y', 'yes'}:
                    print("Overwriting configuration file...")
                    break
                elif resp in {'n', 'no'}:
                    print_action("Skipping config creation")
                    return True
                elif resp == '':
                    # Empty input defaults to no
                    print_action("Skipping config creation")
                    return True
                else:
                    print("Invalid input. Please enter 'y' or 'n'")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping config creation")
                return True
            except Exception as e:
                print(f"\nInput error: {e}")
                print("Defaulting to skip config creation")
                return True

    return create_file(PERSISTENT_FILE, persistent_text, "configuration file")

def verify_installation() -> bool:
    """Check all critical components were installed correctly."""
    checks = [
        (all(d.exists() for d in APP_DIRECTORIES), "Directory structure"),
        (VENV_DIR.exists(), "Virtual environment"),
        (REQUIREMENTS_FILE.exists(), "Requirements file"),
        (INIT_FILE.exists(), "Scripts package marker"),
        (PERSISTENT_FILE.exists(), "Configuration file")
    ]
    
    success = all(status for status, _ in checks)
    if not success:
        print("\nInstallation verification failed:")
        for status, desc in checks:
            if not status:
                print(f"  - Missing: {desc}")
    
    return success

def main() -> None:
    """Main installation workflow."""
    print(f"\n{APP_TITLE} Installer\n{'='*40}")
    
    # Show platform information
    print_action(f"Platform: {CURRENT_PLATFORM.capitalize()}")
    
    # Pre-flight checks
    if not check_python_version():
        sys.exit(1)
    
    # Core installation
    if not setup_directories():
        sys.exit(1)
    
    if not create_file(INIT_FILE, "", "package marker"):
        sys.exit(1)
    
    if not create_file(REQUIREMENTS_FILE, REQUIREMENTS_TEXT, "requirements file"):
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    if not setup_persistent_config():
        sys.exit(1)
    
    # Final verification
    if verify_installation():
        print("\n✓ Installation completed successfully")
        print("Note: Use the launcher script to run DownLord with the virtual environment")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)