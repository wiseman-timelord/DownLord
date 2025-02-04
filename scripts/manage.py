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
    """Remove orphaned files from history."""
    downloads_dir = Path(DOWNLOADS_DIR)
    persistent = load_config()
    
    for i in range(1, 10):
        filename = persistent[f"filename_{i}"]
        if filename != "Empty":
            file_path = downloads_dir / filename
            if not file_path.exists():
                for j in range(i, 9):
                    persistent[f"filename_{j}"] = persistent[f"filename_{j+1}"]
                    persistent[f"url_{j}"] = persistent[f"url_{j+1}"]
                persistent["filename_9"] = "Empty"
                persistent["url_9"] = ""
                logging.info(f"Removed orphaned file from history: {filename}")
    
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