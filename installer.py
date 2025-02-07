# .\installer.py

import os
import time
import subprocess
import json
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Union, List

# Essential setup variables
APP_TITLE = "DownLord"
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = BASE_DIR / "downloads"
SCRIPTS_DIR = BASE_DIR / "scripts"
TEMP_DIR = BASE_DIR / "temp"
REQUIREMENTS_FILE = DATA_DIR / "requirements.txt"
INIT_FILE = SCRIPTS_DIR / "__init__.py"
PERSISTENT_FILE = DATA_DIR / "persistent.json"

# Complete file templates
REQUIREMENTS_TEXT = '''requests>=2.31.0
tqdm>=4.66.1
urllib3>=2.1.0
pathlib>=1.0.1'''

PERSISTENT_TEXT = '''{
    "chunk": 4096000,
    "retries": 100,
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
}'''

def print_action(message: str, delay: float = 0.5):
    """Print action with status indicator."""
    print(f">> {message}", end=' ', flush=True)
    time.sleep(delay)
    print("[OK]")

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 6:
        print_action("Python version check passed")
        return True
    print(f"Error: Python 3.6 or higher required. Current version: {sys.version}")
    return False

def check_platform() -> bool:
    """Check platform compatibility and requirements."""
    system = platform.system().lower()
    if system not in ['windows', 'linux', 'darwin']:
        print(f"Warning: Untested platform: {system}")
        return False
    
    print_action(f"Platform check passed: {system}")
    return True

def create_directories():
    """Create all required application directories."""
    directories = [DATA_DIR, DOWNLOADS_DIR, SCRIPTS_DIR, TEMP_DIR]
    for directory in directories:
        existed = directory.exists()
        directory.mkdir(exist_ok=True)
        rel_path = f".{str(directory).replace(str(BASE_DIR), '')}"
        print_action(f"{'Checked' if existed else 'Created'} directory: {rel_path}")

def create_init_file():
    """Create __init__.py file in scripts directory."""
    INIT_FILE.touch(exist_ok=True)
    print_action("Created .\\scripts\\__init__.py")

def create_requirements():
    """Create requirements.txt file with necessary packages."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(REQUIREMENTS_FILE, 'w') as f:
        f.write(REQUIREMENTS_TEXT)
    print_action("Created .\\data\\requirements.txt")

def install_requirements() -> bool:
    """Install Python package requirements."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
            check=True,
            capture_output=True,
            text=True
        )
        print_action("Installed Python dependencies")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error installing requirements: {e}")
        return False

def handle_persistent() -> bool:
    """Create or update persistent.json file."""
    if PERSISTENT_FILE.exists():
        rel_path = f".{str(PERSISTENT_FILE).replace(str(BASE_DIR), '')}"
        print("Json file exists:", rel_path)
        resp = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if resp != 'y':
            print_action("Skipping persistent creation")
            return True

    try:
        PERSISTENT_FILE.parent.mkdir(exist_ok=True)
        with open(PERSISTENT_FILE, 'w') as f:
            f.write(PERSISTENT_TEXT)
        print_action("Created default persistent")
        return True
    except Exception as e:
        print(f"Error creating persistent file: {e}")
        return False

def check_permissions() -> bool:
    """Check if the program has necessary permissions."""
    try:
        for directory in [DATA_DIR, DOWNLOADS_DIR, SCRIPTS_DIR, TEMP_DIR]:
            directory.mkdir(exist_ok=True)
            test_file = directory / ".test_write"
            test_file.touch()
            test_file.unlink()
        return True
    except PermissionError:
        print("Error: Insufficient permissions to create/write to directories")
        return False

def main():
    """Main installation process."""
    print(f"    {APP_TITLE}: Install and Setup")
    print("===============================================================================")
    # Check system requirements
    if not check_python_version() or not check_platform():
        print("\nInstallation failed: System requirements not met")
        input("Press Enter to exit...")
        return False

    # Check permissions
    if not check_permissions():
        print("\nInstallation failed: Insufficient permissions")
        input("Press Enter to exit...")
        return False

    # Create directory structure
    create_directories()
    create_init_file()

    # Create and install requirements
    create_requirements()
    if not install_requirements():
        print("Installation failed at requirements step")
        input("Press Enter to exit...")
        return False

    # Handle configuration
    if not handle_persistent():
        print("Installation failed at persistent step")
        input("Press Enter to exit...")
        return False

    # Display success message
    input("Press Enter to exit...")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
    except Exception as e:
        print(f"\nUnexpected error during installation: {e}")
        input("Press Enter to exit...")