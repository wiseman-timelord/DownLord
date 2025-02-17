import logging
from pathlib import Path
from typing import Optional, Dict, List
from .interface import load_config, save_config
from .temporary import (
    DOWNLOADS_DIR, 
    TEMP_DIR,
    FILE_STATES,
    FILE_STATE_MESSAGES
)

class ConfigManager:
    @staticmethod
    def load() -> Dict:
        """Load and validate the configuration."""
        try:
            if PERSISTENT_FILE.exists():
                with open(PERSISTENT_FILE, "r") as file:
                    config = json.load(file)
                    return ConfigManager.validate(config)
            logging.warning("No config file found, creating default")
            return ConfigManager.create_default()
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding config: {e}")
            return ConfigManager.create_default()
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return ConfigManager.create_default()

    @staticmethod
    def save(config: Dict) -> bool:
        """Save configuration with atomic write and backup."""
        try:
            config = ConfigManager.validate(config)
            
            # Create backup of existing config
            if PERSISTENT_FILE.exists():
                backup_path = PERSISTENT_FILE.with_suffix('.bak')
                PERSISTENT_FILE.rename(backup_path)
            
            # Write to temporary file first
            temp_path = PERSISTENT_FILE.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Atomic rename to final location
            temp_path.replace(PERSISTENT_FILE)
            
            # Remove backup if everything succeeded
            backup_path = PERSISTENT_FILE.with_suffix('.bak')
            if backup_path.exists():
                backup_path.unlink()
                
            return True
            
        except Exception as e:
            logging.error(f"Error saving config: {str(e)}")
            # Restore from backup if available
            backup_path = PERSISTENT_FILE.with_suffix('.bak')
            if backup_path.exists():
                backup_path.replace(PERSISTENT_FILE)
            return False

    @staticmethod
    def validate(config: Dict) -> Dict:
        """Validate configuration with complete field checking."""
        default = ConfigManager.create_default()
        
        try:
            # Validate all required fields
            for key in default:
                if key not in config:
                    config[key] = default[key]
                    continue
                
                # Type validation for specific fields
                if key == "chunk" and not isinstance(config[key], int):
                    config[key] = default[key]
                elif key == "retries" and not isinstance(config[key], int):
                    config[key] = default[key]
                elif key == "refresh" and not isinstance(config[key], int):
                    config[key] = default[key]
                elif key == "downloads_location" and not isinstance(config[key], str):
                    config[key] = default[key]
                elif key.startswith(("filename_", "url_")) and not isinstance(config[key], str):
                    config[key] = default[key]
                elif key.startswith("total_size_"):
                    try:
                        config[key] = int(config[key])
                        if config[key] < 0:
                            config[key] = 0
                    except (ValueError, TypeError):
                        config[key] = 0
            
            # Validate settings are in allowed options
            if config["retries"] not in RETRY_OPTIONS:
                config["retries"] = default["retries"]
                
            if config.get("refresh") not in REFRESH_OPTIONS:
                config["refresh"] = default["refresh"]
            
            # Ensure all required entries exist
            for i in range(1, 10):
                keys = [
                    f"filename_{i}", f"url_{i}",
                    f"total_size_{i}"
                ]
                for key in keys:
                    if key not in config:
                        config[key] = default.get(key, 0 if "size" in key else "")
            
            return config
            
        except Exception as e:
            logging.error(f"Error validating config: {str(e)}")
            return default

    @staticmethod
    def create_default() -> Dict:
        """Create a new default configuration."""
        from scripts.temporary import DEFAULT_CONFIG, DOWNLOADS_DIR
        config = DEFAULT_CONFIG.copy()
        
        # Add downloads location to default config
        config["downloads_location"] = str(DOWNLOADS_DIR)
        
        for i in range(1, 10):
            config[f"filename_{i}"] = "Empty"
            config[f"url_{i}"] = ""
            config[f"total_size_{i}"] = 0
        return config

def cleanup_orphaned_files() -> None:
    """Enhanced orphan cleanup"""
    print("\n[DEBUG] Running orphan cleanup...")
    downloads_dir = Path(DOWNLOADS_DIR)
    temp_dir = Path(TEMP_DIR)
    persistent = load_config()
    
    # Keep track of all valid filenames including .part variants
    valid_files = set()
    for i in range(1, 10):
        filename = persistent.get(f"filename_{i}", "Empty")
        if filename != "Empty":
            valid_files.add(filename)
            valid_files.add(f"{filename}.part")  # Protect active temp files

    # Check both download and temp directories
    for folder in [downloads_dir, temp_dir]:
        print(f"Checking folder: {folder}")
        for file_path in folder.glob("*"):
            if file_path.name not in valid_files:
                try:
                    file_path.unlink()
                    logging.info(f"Removed orphaned file: {file_path}")
                except Exception as e:
                    logging.error(f"Error removing orphan: {file_path} - {str(e)}")
    
    save_config(persistent)

def cleanup_temp_files() -> None:
    """Clean temporary download files."""
    temp_dir = Path(TEMP_DIR)
    if temp_dir.exists():
        for file in temp_dir.glob("*.part"):
            try:
                file.unlink()
                logging.info(f"Removed temporary file: {file.name}")
            except Exception as e:
                logging.error(f"Error removing temporary file {file}: {e}")

def verify_download_directory() -> bool:
    """Verify download directory exists and is writable."""
    try:
        downloads_dir = Path(DOWNLOADS_DIR)
        downloads_dir.mkdir(parents=True, exist_ok=True)
        test_file = downloads_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception as e:
        logging.error(f"Download directory verification failed: {e}")
        return False
        
def move_with_retry(src: Path, dst: Path, max_retries: int = 5, delay: float = 1.0) -> bool:
    """Move file with retry mechanism for Windows file locks."""
    import time
    
    for attempt in range(max_retries):
        try:
            if not src.exists():
                logging.error(f"Source file missing: {src}")
                return False
                
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Force close any potential file handles
            import gc
            gc.collect()
            
            # Attempt move
            src.replace(dst)  # Using replace instead of rename
            return True
            
        except PermissionError as e:
            if attempt < max_retries - 1:
                logging.warning(f"Move attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logging.error(f"Failed to move file after {max_retries} attempts: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Unexpected error moving file: {e}")
            return False
            
    return False
