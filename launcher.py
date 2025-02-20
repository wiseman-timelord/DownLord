# .\launcher.py

# Imports
import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict
from scripts.configure import ConfigManager
from scripts.interface import (
    display_main_menu,
    setup_menu,
    PERSISTENT_FILE,
    display_error,
    display_success,
    display_download_prompt,
    clear_screen,
)
from scripts.temporary import (
    DOWNLOADS_DIR,
    APP_TITLE,
    RUNTIME_CONFIG,
    TEMP_DIR,
)
from scripts.manage import (
    handle_orphaned_files,
    DownloadManager,
    URLProcessor,
    get_file_name_from_url,
    DownloadError,
)

# Initialize
def initialize_startup() -> Dict:
    """
    Perform all required initialization tasks at program startup.
    Returns the loaded and validated configuration.
    """
    print(f"Initializing {APP_TITLE}...")

    # 1. Verify environment
    if not check_environment():
        print("Environment issues detected. Exiting...")
        time.sleep(3)
        sys.exit(1)

    # 2. Load configuration
    config = ConfigManager.load()

    # 3. Handle orphaned files
    handle_orphaned_files(config)

    # 4. Ensure downloads directory exists
    downloads_location = Path(config.get("downloads_location", str(DOWNLOADS_DIR)))
    downloads_location.mkdir(parents=True, exist_ok=True)

    # 5. Ensure temp directory exists
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Startup initialization complete.\n")
    return config

def handle_download(url: str, config: dict) -> bool:
    """
    Handle the download process for a given URL.
    """
    try:
        processor = URLProcessor()
        download_url, metadata = processor.process_url(url, config)  # Validation happens here
    except DownloadError as e:
        display_error(str(e))
        time.sleep(3)
        return False

    filename = None
    while True:
        try:
            # Truncate URLs for display
            short_url = url if len(url) <= 60 else f"{url[:57]}..."
            print(f"\nInitializing download for: {short_url}")

            # Remove duplicate URLProcessor instantiation (already done above)
            download_url, metadata = processor.process_url(url, config)

            # Truncate resolved download URL for display
            short_download_url = download_url if len(download_url) <= 60 else f"{download_url[:57]}..."
            print(f"Resolved download URL: {short_download_url}")

            filename = metadata.get("filename") or get_file_name_from_url(download_url)
            if not filename:
                display_error("Unable to extract filename from the URL. Please try again.")
                time.sleep(3)
                return False

            downloads_location = Path(config.get("downloads_location", str(DOWNLOADS_DIR)))
            out_path = downloads_location / filename

            # Register the download in the JSON file
            update_history(config, filename, url, metadata.get('size', 0))
            ConfigManager.save(config)  # Ensure the config is saved after updating

            # Initialize download manager with configured location
            dm = DownloadManager(downloads_location)
            chunk_size = config.get("chunk", 4096000)

            # Execute the actual download
            success, error = dm.download_file(download_url, out_path, chunk_size)

            if success:
                display_success(f"Download complete for file: {filename}")
                update_history(config, filename, url, out_path.stat().st_size)
                return True
            else:
                display_error(f"Download failed: {error}")
                time.sleep(3)
                return False

        except Exception as e:
            display_error(f"Unexpected error: {str(e)}")
            time.sleep(3)
            choice = input("\nSelection; Retry URL Now = R, Alternate URL = 0, Back to Menu = B: ").strip().lower()

            if choice == 'r':
                continue
            elif choice == '0':
                new_url = display_download_prompt()
                if new_url.lower() == 'b':
                    return False
                # Update config if we have filename context
                if filename:
                    for i in range(1, 10):
                        if config[f"filename_{i}"] == filename:
                            config[f"url_{i}"] = new_url
                            ConfigManager.save(config)
                            break
                url = new_url
                clear_screen()
                continue
            elif choice == 'b':
                return False
            else:
                display_error("Invalid choice. Please try again.")
                time.sleep(3)
                return False


def check_environment() -> bool:
    """
    Verify environment with proper error handling.
    """
    try:
        # Check if config file exists
        if not PERSISTENT_FILE.exists():
            raise FileNotFoundError(f"Missing configuration file: {PERSISTENT_FILE.name}")

        # Load config and get absolute paths
        config = ConfigManager.load()
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
            display_error(f"Resetting downloads location. Reason: {reset_reason}")
            print(f"\nConfiguration reset required:")
            print(f"• {reset_reason}")
            print(f"• Default location: {default_downloads}")

            # Update and save config
            config["downloads_location"] = str(default_downloads)
            if ConfigManager.save(config):
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
            time.sleep(3)
            return False

        return True

    except FileNotFoundError as e:
        clear_screen()
        print(f"\nCritical Error: {str(e)}")
        print("Please run the installer first!")
        time.sleep(3)
        sys.exit(1)
    except Exception as e:
        display_error(f"Environment check failed: {str(e)}")
        display_error(f"Startup failed: {str(e)}")
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

        if choice == 'q':
            print("Quitting...")
            break

        if choice == '0':
            clear_screen("Initialize Download")
            url = input("\nEnter download URL (Q to cancel): ").strip()
            if url.lower() == 'q':
                continue

            # Use the configured downloads location
            downloads_location = Path(config.get("downloads_location", str(DOWNLOADS_DIR)))
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
    finally:
        print(f"\nFinding it useful? Donations to Wiseman-Timelord!")


if __name__ == "__main__":
    main()