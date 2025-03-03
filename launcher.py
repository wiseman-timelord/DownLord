# # Script: `.\launcher.py`

# Imports
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict
from scripts.configure import ConfigManager, get_downloads_path
from scripts.interface import (
    display_main_menu,
    setup_menu,
    PERSISTENT_FILE,
    display_error,
    handle_error,
    display_success,
    display_download_prompt,
    clear_screen,
    update_history,
    delete_file,
    exit_sequence,
    get_user_choice_after_error  # Added this line
)
from scripts.temporary import (
    DOWNLOADS_DIR,
    APP_TITLE,
    RUNTIME_CONFIG,
    BASE_DIR,
    TEMP_DIR
)
from scripts.manage import (
    handle_orphaned_files,
    DownloadManager,
    URLProcessor,
    get_file_name_from_url,
    DownloadError
)

# Initialize
def initialize_startup() -> Dict:
    print(f"Initializing {APP_TITLE}...")
    if not check_environment():
        print("Environment issues detected. Exiting...")
        time.sleep(3)
        sys.exit(1)
    
    config = ConfigManager.load()
    handle_orphaned_files(config)
    
    # Resolve downloads location
    downloads_location_str = config.get("downloads_location", "downloads")
    downloads_path = Path(downloads_location_str)
    if not downloads_path.is_absolute():
        downloads_path = BASE_DIR / downloads_path
    downloads_path = downloads_path.resolve()
    downloads_path.mkdir(parents=True, exist_ok=True)
    
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    print("Startup initialization complete.\n")
    return config

def handle_download(url: str, config: dict) -> bool:
    """
    Handle the download process for a given URL.
    """
    try:
        processor = URLProcessor()
        try:
            download_url, metadata = processor.process_url(url, config)
        except DownloadError as e:
            handle_error(str(e))
            return False

        filename = metadata.get("filename") or get_file_name_from_url(download_url)
        if not filename:
            handle_error("Unable to extract filename from the URL. Please try again.")
            return False

        update_history(config, filename, url, metadata.get('size', 0))
        ConfigManager.save(config)

        downloads_path = get_downloads_path(config)
        dm = DownloadManager(downloads_path)
        chunk_size = config.get("chunk", 4096000)

        short_url = url if len(url) <= 60 else f"{url[:57]}..."
        short_download_url = download_url if len(download_url) <= 60 else f"{download_url[:57]}..."
        print(f"Initializing download for URL: {short_url}")
        print(f"Resolved final download endpoint: {short_download_url}")

        out_path = downloads_path / filename
        success, error = dm.download_file(download_url, out_path, chunk_size)

        if success:
            return True
        elif error == "Download abandoned by user":
            print("Download abandoned. Returning to main menu.")
            time.sleep(2)
            return False
        else:
            handle_error(f"Download failed: {error}")
            return False

    except Exception as e:
        handle_error(f"Unexpected error: {str(e)}")
        choice = get_user_choice_after_error()
        if choice == 'r':
            return handle_download(url, config)
        elif choice == '0':
            new_url = display_download_prompt()
            if new_url and new_url.lower() == 'b':
                return False
            if new_url and filename:
                for i in range(1, 10):
                    if config[f"filename_{i}"] == filename:
                        config[f"url_{i}"] = new_url
                        ConfigManager.save(config)
                        break
            return handle_download(new_url, config) if new_url else False
        elif choice == 'b':
            return False
        else:
            handle_error("Invalid choice. Please try again.")
            return False

def check_environment() -> bool:
    try:
        if not PERSISTENT_FILE.exists():
            raise FileNotFoundError(f"Missing configuration file: {PERSISTENT_FILE.name}")
        
        config = ConfigManager.load()
        downloads_path = get_downloads_path(config)
        
        if not downloads_path.exists():
            downloads_path.mkdir(parents=True, exist_ok=True)
        elif not downloads_path.is_dir():
            display_error(f"Path is not a directory: {downloads_path}")
            return False
        
        test_file = downloads_path / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except FileNotFoundError as e:
        clear_screen()
        print(f"\nCritical Error: {str(e)}")
        print("Please run the installer first!")
        time.sleep(3)
        sys.exit(1)
    except Exception as e:
        display_error(f"Environment check failed: {str(e)}")
        return False

def prompt_for_download():
    """
    Main loop for handling user input and initiating downloads.
    """
    # Ensure clean state before showing menu
    config = ConfigManager.load()

    while True:
        display_main_menu(config)
        choice = input().strip().lower()

        if choice == 's':
            setup_menu()
            config = ConfigManager.load()  # Reload config after setup
            continue

        if choice == 'r':
            handle_orphaned_files(config)
            config = ConfigManager.load()  # Reload config after refresh
            clear_screen()
            continue

        if choice == 'q':
            exit_sequence()  # Display the exit sequence
            break  # Exit the loop, ending the script

        if choice == '0':
            clear_screen("Initialize Download")
            url = input("\nEnter download URL (Q to cancel): ").strip()
            if url.lower() == 'q':
                continue

            # Resolve downloads location
            downloads_location_str = config.get("downloads_location", "downloads")
            downloads_path = Path(downloads_location_str)
            if not downloads_path.is_absolute():
                downloads_path = BASE_DIR / downloads_path
            downloads_path = downloads_path.resolve()
            
            success = handle_download(url, config)
            if success:
                config = ConfigManager.load()  # Reload config after successful download
            time.sleep(2)

        elif choice.isdigit() and 1 <= int(choice) <= 9:
            index = int(choice)
            url = config.get(f"url_{index}", "")
            filename = config.get(f"filename_{index}", "Empty")

            if filename == "Empty":
                display_error("Invalid choice. Please try again.")
                time.sleep(3)
                continue

            # Clear screen for Initialize Download
            clear_screen("Initialize Download")

            # Resolve downloads location
            downloads_location_str = config.get("downloads_location", "downloads")
            downloads_path = Path(downloads_location_str)
            if not downloads_path.is_absolute():
                downloads_path = BASE_DIR / downloads_path
            downloads_path = downloads_path.resolve()
            
            existing_file = downloads_path / filename
            if existing_file.exists():
                display_success(f"'{filename}' is already downloaded!")
                time.sleep(2)
                config = ConfigManager.load()  # Reload to refresh any changes
                continue
            
            # Handle orphaned files (no URL)
            if not url:
                new_url = display_download_prompt()
                if new_url is None:  # User chose to go back to the menu
                    continue

                # Validate the new URL
                if not URLProcessor.validate_url(new_url):
                    display_error("Invalid URL. Please enter a valid URL starting with http:// or https://")
                    time.sleep(3)
                    continue

                # Update the config with the new URL
                config[f"url_{index}"] = new_url
                ConfigManager.save(config)

                # Start the download with the new URL and existing .part file
                success = handle_download(new_url, config)
                if success:
                    config = ConfigManager.load()  # Reload config after successful download
                time.sleep(2)
            else:
                # Handle normal download
                success = handle_download(url, config)
                if success:
                    config = ConfigManager.load()  # Reload config after successful download
                time.sleep(2)
        elif choice == 'd':  # Handle delete option
            delete_index = input("Enter the number of the file to delete (1-9): ").strip()
            if delete_index.isdigit() and 1 <= int(delete_index) <= 9:
                delete_file(config, int(delete_index))
            else:
                display_error("Invalid input. Please enter a number between 1 and 9.")
                time.sleep(3)
            continue
        else:
            display_error("Invalid choice. Please try again.")
            time.sleep(3)


def main():
    """
    Main application entry point.
    """
    try:
        # Initialize the application
        config = initialize_startup()

        # Start the main menu loop
        prompt_for_download()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        time.sleep(3)

if __name__ == "__main__":
    main()