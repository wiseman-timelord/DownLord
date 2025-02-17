# .\launcher.py

# Imports
import os, sys, logging, json
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict  # Added Dict import
from scripts.utility import DownloadManager, URLProcessor, get_file_name_from_url
from scripts.interface import (
    display_main_menu,
    setup_menu,
    load_config,
    save_config,
    PERSISTENT_FILE,
    display_error,
    display_success,
    display_download_prompt,
    display_download_status,
    display_file_info,
    update_history,
    delete_file,
    clear_screen,  # Add this import
    ERROR_MESSAGES,
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
            # Clear the screen and display the "Initialize Download" header
            clear_screen("Initialize Download", use_logo=False)

            processor = URLProcessor()
            download_url, metadata = processor.process_url(url, config)
            
            if not download_url or not metadata:
                error_msg = "Failed to process URL. Check if it's a valid Hugging Face CDN link."
                display_error(error_msg)
                logging.error(f"URL processing failed: {url}")
                return False

            filename = metadata.get("filename") or get_file_name_from_url(download_url)
            if not filename:
                display_error(ERROR_MESSAGES["filename_error"] + " (no filename in metadata)")
                return False

            # Use the configured downloads location
            downloads_location = Path(config.get("downloads_location", str(DOWNLOADS_DIR)))
            out_path = downloads_location / filename  # Correct output path

            # Display the "Starting new download" message
            display_download_status(filename, FILE_STATES["new"])

            # Print the initialization details
            print(f"\nInitializing download for: {url}")
            print("Phase 1: URL processing...")
            print(f"Resolved download URL: {download_url}")
            print(f"Metadata: {json.dumps(metadata, indent=2)}")
            print(f"Found filename: {filename}")

            # Pass the configured downloads location to DownloadManager
            manager = DownloadManager(downloads_location)
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
    """Verify environment with proper error handling."""
    try:
        # Check if config file exists
        if not PERSISTENT_FILE.exists():
            raise FileNotFoundError(f"Missing configuration file: {PERSISTENT_FILE.name}")
        
        # Load config and get absolute paths
        config = load_config()
        default_downloads = DOWNLOADS_DIR.resolve()
        configured_downloads = Path(config.get("downloads_location", "")).expanduser().resolve()

        # Check if configured path needs reset
        needs_reset = False
        reset_reason = ""
        
        # 1. Check path exists and is directory
        if not configured_downloads.exists():
            reset_reason = f"Path does not exist: {configured_downloads}"
            needs_reset = True
        elif not configured_downloads.is_dir():
            reset_reason = f"Path is not a directory: {configured_downloads}"
            needs_reset = True

        if needs_reset:
            logging.warning(f"Resetting downloads location. Reason: {reset_reason}")
            print(f"\nConfiguration reset required:")
            print(f"• {reset_reason}")
            print(f"• Default location: {default_downloads}")
            
            # Update and save config
            config["downloads_location"] = str(default_downloads)
            if save_config(config):
                print("✓ Configuration updated successfully")
            else:
                print("⚠ Failed to save configuration changes!")
                return False

            # Ensure directory structure
            default_downloads.mkdir(parents=True, exist_ok=True)

        # Final validation
        test_file = default_downloads / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            display_error(f"Write permission denied in: {default_downloads}")
            return False
            
        return True
        
    except FileNotFoundError as e:
        clear_screen()
        print(f"\nCritical Error: {str(e)}")
        print("Please run the installer first!")
        input("\nPress any key to exit...")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Environment check failed: {str(e)}")
        display_error(f"Startup failed: {str(e)}")
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

            # Use the configured downloads location
            downloads_location = Path(config.get("downloads_location", str(DOWNLOADS_DIR)))
            success = handle_download(url, config)
            if success:
                config = load_config()  # Reload config after successful download
            input("\nPress Enter to continue...")

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