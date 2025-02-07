# .\launcher.py

import os
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional
from scripts.utility import DownloadManager, URLProcessor, get_file_name_from_url
from scripts.interface import (
    display_main_menu,
    setup_menu,
    load_config,
    save_config,
    display_error,
    display_success,
    display_download_prompt,
    display_download_status,
    display_file_info,
    update_history,
    ERROR_MESSAGES,
    delete_file  # Add this
)
from scripts.temporary import (
    DOWNLOADS_DIR,
    LOG_FILE,
    APP_TITLE,
    RUNTIME_CONFIG,
    FILE_STATES,
    TEMP_DIR  # Add this
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

def handle_download(url: str, config: dict) -> bool:
    if not validate_url(url):
        display_error(ERROR_MESSAGES["invalid_url"])
        return False

    try:
        # Process URL and get metadata
        processor = URLProcessor()
        download_url, metadata = processor.process_url(url, config)
        filename = metadata.get("filename") or get_file_name_from_url(download_url)
        
        if not filename:
            display_error(ERROR_MESSAGES["filename_error"])
            return False

        # Remove the call to update_history
        # update_history(config, filename, url, metadata.get('size', 0))  # Commented out

        out_path = DOWNLOADS_DIR / filename
        display_download_status(filename, FILE_STATES["new"])
        
        manager = DownloadManager()
        success, error = manager.download_file(download_url, out_path, config["chunk"])
        
        if success:
            display_download_status(filename, FILE_STATES["complete"])
            display_file_info(out_path, url)
            return True
        else:
            display_error(error)
            display_download_status(filename, FILE_STATES["error"])
            return False
            
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        display_error(str(e))
        return False

def check_environment() -> bool:
    try:
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        config = load_config()
        
        if not config:
            display_error(ERROR_MESSAGES["config_error"])
            return False
            
        test_file = DOWNLOADS_DIR / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            display_error("No write permission in downloads directory")
            return False
            
        display_success("Environment check passed")
        return True
        
    except Exception as e:
        logging.error(f"Environment check failed: {str(e)}")
        display_error(f"Environment verification failed: {str(e)}")
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
        elif choice == 'd':  # Handle delete option
            delete_index = input("Enter the number of the file to delete (1-9): ").strip()
            if delete_index.isdigit() and 1 <= int(delete_index) <= 9:
                delete_file(config, int(delete_index))
            else:
                display_error("Invalid input. Please enter a number between 1 and 9.")
            continue
        else:
            display_error(ERROR_MESSAGES["invalid_choice"])
            continue

        if url:
            success = handle_download(url, config)
            if success:
                config = load_config()  # Reload config after successful download
            input("\nPress Enter to continue...")
        else:
            display_error(ERROR_MESSAGES["invalid_choice"])
            input("\nPress Enter to continue...")

def main():
    """
    Main application entry point.
    """
    print(f"\nInitializing {APP_TITLE}...")
    
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