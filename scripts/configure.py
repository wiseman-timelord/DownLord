# Script: `.\scripts\configure.py`

# Imports
import json
import time
from pathlib import Path
from typing import Dict
from .temporary import (
    PERSISTENT_FILE,
    DEFAULT_CONFIG,
    DOWNLOADS_DIR,
    RETRY_OPTIONS,
    REFRESH_OPTIONS,
    DEFAULT_CHUNK_SIZES,
    ERROR_HANDLING,
    BASE_DIR
)
from . import interface
import sys

# Classes
class ConfigManager:
    """
    Manages loading, saving, and validating the application configuration.
    """

    @staticmethod
    def load() -> Dict:
        """
        Load the configuration file with validation.
        """
        try:
            if not PERSISTENT_FILE.exists():
                raise FileNotFoundError("Missing configuration file")

            with open(PERSISTENT_FILE, "r") as f:
                config = json.load(f)
                return ConfigManager.validate(config)

        except Exception as e:
            raise RuntimeError(f"Config load failed: {e}")

    @staticmethod
    def save(config: Dict) -> bool:
        """
        Save the configuration file with atomic write and backup.
        """
        try:
            validated = ConfigManager.validate(config)
            temp_path = PERSISTENT_FILE.with_suffix('.tmp')

            with open(temp_path, 'w') as f:
                json.dump(validated, f, indent=4)

            # Create a backup if the persistent file exists
            if PERSISTENT_FILE.exists():
                backup_path = PERSISTENT_FILE.with_suffix('.bak')
                
                # Remove the existing backup file if it exists
                if backup_path.exists():
                    backup_path.unlink()  # Delete the existing backup file
                
                # Rename the current persistent file to backup
                PERSISTENT_FILE.rename(backup_path)

            # Move the temporary file to the persistent file location
            temp_path.rename(PERSISTENT_FILE)
            return True

        except Exception as e:
            raise RuntimeError(f"Config save failed: {e}")

    @staticmethod
    def validate(config: Dict) -> Dict:
        """Validate and clean the configuration."""
        validated = DEFAULT_CONFIG.copy()
        
        # Remove obsolete keys
        config.pop("refresh", None)
        config.pop("download", None)
        
        # Merge valid keys
        valid_keys = (
            ['chunk', 'retries', 'timeout_length', 'downloads_location'] +
            [f"filename_{i}" for i in range(1, 10)] +
            [f"url_{i}" for i in range(1, 10)] +
            [f"total_size_{i}" for i in range(1, 10)]
        )
        
        for key in valid_keys:
            if key in config:
                validated[key] = config[key]
        
        # Validate chunk size
        if validated["chunk"] not in DEFAULT_CHUNK_SIZES.values():
            validated["chunk"] = DEFAULT_CHUNK_SIZES["cable"]
        
        # Ensure downloads_location is a string; default to "downloads" if invalid
        if not isinstance(validated.get("downloads_location"), str):
            validated["downloads_location"] = "downloads"
        
        return validated

# Functions
def get_downloads_path(config: Dict) -> Path:
    downloads_location_str = config.get("downloads_location", "downloads")
    downloads_path = Path(downloads_location_str)
    if not downloads_path.is_absolute():
        downloads_path = BASE_DIR / downloads_path
    return downloads_path.resolve()        

def check_environment() -> bool:
    try:
        if not PERSISTENT_FILE.exists():
            raise FileNotFoundError(f"Missing configuration file: {PERSISTENT_FILE.name}")
        config = ConfigManager.load()
        downloads_path = get_downloads_path(config)
        if not downloads_path.exists():
            downloads_path.mkdir(parents=True, exist_ok=True)
        elif not downloads_path.is_dir():
            interface.display_error(f"Path is not a directory: {downloads_path}")
            return False
        
        test_file = downloads_path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except FileNotFoundError as e:
        interface.clear_screen()
        interface.display_error(f"Critical Error: {str(e)}")
        print("Please run the installer first!")
        time.sleep(3)
        sys.exit(1)
    except Exception as e:
        interface.display_error(f"Environment check failed: {str(e)}")
        return False