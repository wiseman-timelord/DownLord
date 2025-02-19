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
                PERSISTENT_FILE.rename(backup_path)

            # Move the temporary file to the persistent file location
            temp_path.rename(PERSISTENT_FILE)
            return True

        except Exception as e:
            raise RuntimeError(f"Config save failed: {e}")

    @staticmethod
    def validate(config: Dict) -> Dict:
        """
        Validate the configuration and ensure all required fields are present.
        """
        default = DEFAULT_CONFIG.copy()
        default["downloads_location"] = str(DOWNLOADS_DIR)

        # Ensure all required fields are present
        for key, value in default.items():
            if key not in config:
                config[key] = value

        # Validate chunk size
        if config["chunk"] not in DEFAULT_CHUNK_SIZES.values():
            config["chunk"] = DEFAULT_CHUNK_SIZES["cable"]

        # Validate retries
        if config["retries"] not in RETRY_OPTIONS:
            config["retries"] = RETRY_OPTIONS[0]

        # Validate refresh rate
        if config["refresh"] not in REFRESH_OPTIONS:
            config["refresh"] = REFRESH_OPTIONS[0]

        # Validate downloads location
        downloads_location = config.get("downloads_location", str(DOWNLOADS_DIR))
        try:
            downloads_path = Path(downloads_location).expanduser().resolve()
            downloads_path.mkdir(parents=True, exist_ok=True)
            config["downloads_location"] = str(downloads_path)
        except Exception as e:
            print(f"Error: Invalid downloads location: {e}")
            time.sleep(3)
            config["downloads_location"] = str(DOWNLOADS_DIR)

        return config