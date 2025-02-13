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
    incomplete_dir = Path(TEMP_DIR)  # TEMP_DIR is now .\incomplete
    persistent = load_config()
    
    # Keep track of all valid filenames including .part variants
    valid_files = set()
    for i in range(1, 10):
        filename = persistent.get(f"filename_{i}", "Empty")
        if filename != "Empty":
            valid_files.add(filename)
            valid_files.add(f"{filename}.part")  # Protect active temp files

    # Check both download and incomplete directories
    for folder in [downloads_dir, incomplete_dir]:
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