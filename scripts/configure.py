# Script: .\scripts\configure.py

# Imports
import json, time
from pathlib import Path
from typing import Dict
from .temporary import (
    PERSISTENT_FILE,
    DEFAULT_CONFIG,
    DOWNLOADS_DIR,
    RETRY_OPTIONS,
    REFRESH_OPTIONS,
    DEFAULT_CHUNK_SIZES,
    ERROR_HANDLING
)


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
        # Start with default configuration
        validated = DEFAULT_CONFIG.copy()
        validated["downloads_location"] = str(DOWNLOADS_DIR)  # Corrected from DLOADS_DIR to DOWNLOADS_DIR
        
        # Remove obsolete keys that might exist in old configs
        config.pop("refresh", None)
        config.pop("download", None)
        
        # Merge valid keys from existing config
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
        
        # Validate downloads location
        try:
            dl_path = Path(validated["downloads_location"]).expanduser().resolve()
            dl_path.mkdir(parents=True, exist_ok=True)
            validated["downloads_location"] = str(dl_path)
        except Exception as e:
            print(f"Invalid downloads location: {e}")
            validated["downloads_location"] = str(DOWNLOADS_DIR)
        
        return validated