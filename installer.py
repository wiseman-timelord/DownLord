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
CONFIG_FILE = DATA_DIR / "config.json"
REQUIREMENTS_FILE = DATA_DIR / "requirements.txt"
INIT_FILE = SCRIPTS_DIR / "__init__.py"

# Requirements text to be written to requirements.txt
REQUIREMENTS_TEXT = '''requests>=2.31.0
tqdm>=4.66.1
urllib3>=2.1.0
pathlib>=1.0.1'''

# Default configuration (minimal version for installer)
DEFAULT_CONFIG = {
    "version": "1.2.0",
    "last_updated": "",
    "download": {
        "chunk_size": 4096000,
        "max_retries": 100,
        "timeout": 30,
        "verify_hash": True,
        "parallel_downloads": False,
        "max_parallel": 3,
        "bandwidth_limit": None,
        "auto_resume": True,
        "huggingface": {
            "use_auth": False,
            "token": None,
            "mirror": None,
            "prefer_torch": True
        }
    },
    "storage": {
        "temp_dir": str(TEMP_DIR),
        "download_dir": str(DOWNLOADS_DIR),
        "keep_incomplete": True,
        "organize_by_type": False
    },
    "security": {
        "verify_ssl": True,
        "allowed_domains": [],
        "blocked_extensions": [".exe", ".bat", ".sh", ".dll"],
        "scan_downloads": False,
        "hash_verification": True,
        "hash_algorithm": "sha256"
    },
    "interface": {
        "show_progress": True,
        "show_speed": True,
        "show_eta": True,
        "dark_mode": False,
        "detailed_logging": False
    },
    "history": {
        "max_entries": 9,
        "entries": [],
        "auto_clean": True,
        "clean_after_days": 30
    }
}

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

def create_default_config() -> Dict:
    """Create default configuration with current timestamp."""
    from datetime import datetime
    config = DEFAULT_CONFIG.copy()
    config["last_updated"] = datetime.now().isoformat()
    return config

def handle_config() -> bool:
    """Create or update config.json file."""
    if CONFIG_FILE.exists():
        print("Config file already exists at:", CONFIG_FILE)
        resp = input("Do you want to overwrite it? (y/n): ").strip().lower()
        if resp != 'y':
            print_action("Skipping config creation")
            return True

    try:
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        config = create_default_config()
        
        # Initialize download history
        for i in range(1, 10):
            config[f"filename_{i}"] = "Empty"
            config[f"url_{i}"] = ""
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print_action("Created default config")
        return True
    except Exception as e:
        print(f"Error creating config file: {e}")
        return False

def check_permissions() -> bool:
    """Check if the program has necessary permissions."""
    try:
        # Try to write to all necessary directories
        for directory in [DATA_DIR, DOWNLOADS_DIR, SCRIPTS_DIR, TEMP_DIR]:
            directory.mkdir(exist_ok=True)
            test_file = directory / ".test_write"
            test_file.touch()
            test_file.unlink()
        return True
    except PermissionError:
        print("Error: Insufficient permissions to create/write to directories")
        return False

def display_success():
    """Display success message with ASCII art."""
    success_message = f"""
========================================================================================================================
Installation Complete!

{APP_TITLE} has been successfully installed with the following components:

- Directory structure created
- Python dependencies installed
- Configuration file initialized
- Download directories prepared

You can now run {APP_TITLE} using the launcher.

Thank you for installing {APP_TITLE}!
========================================================================================================================
"""
    print(success_message)

def main():
    """Main installation process."""
    print(f"\nInstalling {APP_TITLE}...")
    print("-" * 50)

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
    if not handle_config():
        print("Installation failed at configuration step")
        input("Press Enter to exit...")
        return False

    # Display success message
    display_success()
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