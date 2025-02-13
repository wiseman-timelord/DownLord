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

def cleanup_orphaned_files() -> None:
    """Enhanced orphan cleanup"""
    downloads_dir = Path(DOWNLOADS_DIR)
    temp_dir = Path(TEMP_DIR)
    persistent = load_config()
    
    # Check both download and temp directories
    for folder in [downloads_dir, temp_dir]:
        for file_path in folder.glob("*"):
            filename = file_path.name.replace(".part", "")
            if not any(persistent[f"filename_{i}"] == filename for i in range(1,10)):
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