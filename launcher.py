# .\launcher.py

import os
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from scripts.utility import (
    download_file,
    get_file_name_from_url,
    DownloadError,
    URLProcessor
)
from scripts.interface import (
    display_main_menu,
    setup_menu,
    load_config,
    save_config,
    display_error,
    display_success,
    display_download_prompt,
    update_history,
    ERROR_MESSAGES
)
from scripts.temporary import (
    DOWNLOADS_DIR,
    LOG_FILE,
    APP_TITLE
)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def validate_url(url: str) -> bool:
    """
    Validate if the URL is properly formatted.
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False

def handle_blocked_extension(filename: str, config: dict) -> bool:
    """
    Check if the file extension is blocked.
    
    Args:
        filename: Name of the file to check
        config: Application configuration
        
    Returns:
        bool: True if extension is blocked, False otherwise
    """
    ext = Path(filename).suffix.lower()
    return ext in config["security"]["blocked_extensions"]

def handle_download(url: str, config: dict) -> bool:
    """
    Process a download request.
    
    Args:
        url: URL to download from
        config: Application configuration
        
    Returns:
        bool: True if download successful, False otherwise
    """
    if not validate_url(url):
        display_error(ERROR_MESSAGES["invalid_url"])
        return False

    try:
        # Process URL and get metadata
        download_url, metadata = URLProcessor.process_url(url, config)
        
        # Get filename
        filename = get_file_name_from_url(download_url)
        if not filename:
            display_error(ERROR_MESSAGES["filename_error"])
            return False
            
        # Check for blocked extensions
        if handle_blocked_extension(filename, config):
            display_error(f"File type {Path(filename).suffix} is blocked in security settings")
            return False

        # Prepare output path
        out_path = DOWNLOADS_DIR / filename
        
        # Handle existing file
        if out_path.exists():
            resp = input(f"File {filename} already exists. Overwrite? (y/n): ").strip().lower()
            if resp != 'y':
                return False

        # Attempt download
        chunk_size = config["download"]["chunk_size"]
        success = download_file(download_url, out_path, chunk_size)
        
        if success:
            update_history(config, filename, url)
            display_success(f"Download complete: {filename}")
            return True
            
    except DownloadError as e:
        display_error(f"Download error: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during download: {str(e)}")
        display_error(f"An unexpected error occurred: {str(e)}")
        
    return False

def check_environment() -> bool:
    """
    Verify the application environment is properly set up.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
    try:
        # Ensure downloads directory exists
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Check if config can be loaded
        config = load_config()
        if not config:
            return False
            
        # Verify write permissions
        test_file = DOWNLOADS_DIR / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            display_error("Error: No write permission in downloads directory")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Environment check failed: {str(e)}")
        display_error(f"Failed to verify application environment: {str(e)}")
        return False

def prompt_for_download():
    """
    Main download prompt loop.
    """
    config = load_config()

    while True:
        display_main_menu(config)
        choice = input().strip().lower()

        if choice == 's':
            setup_menu()
            config = load_config()  # Reload config after setup
            continue
        
        if choice == 'q':
            print("Quitting...")
            break

        if choice == '0':
            url = display_download_prompt()
            if url.lower() == 'q':
                print("Quitting...")
                break
        elif choice.isdigit() and 1 <= int(choice) <= 9:
            url = config.get(f"url_{choice}", "")
        else:
            display_error(ERROR_MESSAGES["invalid_choice"])
            continue

        if url:
            handle_download(url, config)
            input("\nPress Enter to continue...")
        else:
            display_error(ERROR_MESSAGES["invalid_choice"])
            input("\nPress Enter to continue...")

def main():
    """
    Main application entry point.
    """
    print(f"\nStarting {APP_TITLE}...")
    
    # Verify environment
    if not check_environment():
        input("\nPress Enter to exit...")
        return

    try:
        prompt_for_download()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        display_error(f"An unexpected error occurred: {str(e)}")
    finally:
        print(f"\nThank you for using {APP_TITLE}!")

if __name__ == "__main__":
    main()