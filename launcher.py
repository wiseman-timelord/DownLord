# .\launcher.py

import os
import sys
import logging
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict  # Added Dict import
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
from scripts.manage import cleanup_orphaned_files  # Add this import

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

    while True:
        try:
            # Process URL and get metadata
            processor = URLProcessor()
            download_url, metadata = processor.process_url(url, config)
            filename = metadata.get("filename") or get_file_name_from_url(download_url)
            
            if not filename:
                display_error(ERROR_MESSAGES["filename_error"])
                return False

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
                choice = input("\nSelection; Abandon = A or New URL = 0: ").strip().lower()
                if choice == 'a':
                    return False
                elif choice == '0':
                    url = display_download_prompt()
                    if url.lower() == 'q':
                        return False
                    clear_screen()  # Clear screen for new attempt
                    continue  # Try again with new URL
                else:
                    display_error("Invalid choice")
                    return False
                    
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            display_error(str(e))
            choice = input("\nSelection; Abandon = A or New URL = 0: ").strip().lower()
            if choice == 'a':
                return False
            elif choice == '0':
                url = display_download_prompt()
                if url.lower() == 'q':
                    return False
                clear_screen()  # Clear screen for new attempt
                continue  # Try again with new URL
            else:
                display_error("Invalid choice")
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
    # Add this at start of loop
    cleanup_orphaned_files()  # Ensure clean state before showing menu
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
            if url is None:  # User chose to go back to the menu
                continue
            if url.lower() == 'b':  # Redundant check, but ensures consistency
                continue
        elif choice.isdigit() and 1 <= int(choice) <= 9:
            index = int(choice)
            url = config.get(f"url_{index}", "")
            filename = config.get(f"filename_{index}", "Empty")
            
            if filename == "Empty":
                display_error(ERROR_MESSAGES["invalid_choice"])
                input("\nPress Enter to continue...")
                continue
            
            # Handle orphaned files (no URL)
            if not url:
                new_url = display_download_prompt()
                if new_url is None:  # User chose to go back to the menu
                    continue
                
                # Validate the new URL
                if not validate_url(new_url):
                    display_error(ERROR_MESSAGES["invalid_url"])
                    input("\nPress Enter to continue...")
                    continue
                
                # Update the config with the new URL
                config[f"url_{index}"] = new_url
                save_config(config)
                
                # Start the download with the new URL and existing .part file
                success = handle_download(new_url, config)
                if success:
                    config = load_config()  # Reload config after successful download
                input("\nPress Enter to continue...")
            else:
                # Handle normal download
                success = handle_download(url, config)
                if success:
                    config = load_config()  # Reload config after successful download
                input("\nPress Enter to continue...")
        elif choice == 'd':  # Handle delete option
            delete_index = input("Enter the number of the file to delete (1-9): ").strip()
            if delete_index.isdigit() and 1 <= int(delete_index) <= 9:
                delete_file(config, int(delete_index))
            else:
                display_error("Invalid input. Please enter a number between 1 and 9.")
            continue
        else:
            display_error(ERROR_MESSAGES["invalid_choice"])
            input("\nPress Enter to continue...")

def check_for_orphaned_temp_files(config: Dict) -> None:
    """Check the incomplete folder for orphaned temp files and register them in the config."""
    incomplete_dir = Path(TEMP_DIR)
    for temp_file in incomplete_dir.glob("*.part"):
        filename = temp_file.name.replace(".part", "")
        if not any(config.get(f"filename_{i}") == filename for i in range(1, 10)):
            # Find the first empty slot
            for i in range(1, 10):
                if config.get(f"filename_{i}") == "Empty":
                    config[f"filename_{i}"] = filename
                    config[f"url_{i}"] = ""  # URL will be populated on resume
                    config[f"total_size_{i}"] = 0  # Set total size to 0 (unknown)
                    save_config(config)
                    logging.info(f"Registered orphaned temp file: {filename} in slot {i}")
                    break


def main():
    """Main application entry point."""
    print(f"\nInitializing {APP_TITLE}...")
    
    # Verify environment
    if not check_environment():
        input("\nPress Enter to exit...")
        return

    # Load config and check for orphaned temp files
    config = load_config()
    check_for_orphaned_temp_files(config)

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