# .\scripts\interface.py

import json, os, logging, time
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime
from scripts.temporary import (
    FILE_STATE_MESSAGES,
    FILE_STATES,
    PERSISTENT_FILE,
    DOWNLOADS_DIR,
    RUNTIME_CONFIG,
    DEFAULT_CHUNK_SIZES,
    APP_TITLE,
    ERROR_TYPES,
    DATA_DIR,
    TEMP_DIR,
    RETRY_OPTIONS,
    REFRESH_OPTIONS,
    DEFAULT_CHUNK_SIZES,
    SPEED_DISPLAY
)

# ASCII Art
# Menu Templates
MENU_SEPARATOR = "-" * 80

ASCII_LOGO = '''===============================================================================
          ________                      .____                    .___
          \______ \   ______  _  ______ |    |    ___________  __| _/
           |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ | 
           |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ | 
          /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ | 
                  \/                  \/        \/                \/ 
-------------------------------------------------------------------------------
    %s
==============================================================================='''

SIMPLE_HEADER = '''===============================================================================
    DownLord: %s
==============================================================================='''


MAIN_MENU_FOOTER = """===============================================================================
Selection; New URL = 0, Continue = 1-9, Delete = D, Setup = S, Quit = Q: """

SETUP_MENU = """





    1. Connection Speed       ({chunk})

    2. Maximum Retries        ({retries})

    3. Screen Refresh         ({refresh}s)

    4. Downloads Location     ({downloads_location})





==============================================================================="""


# Error Messages
ERROR_MESSAGES = {
    "invalid_choice": "Invalid choice. Please try again.",
    "invalid_url": "Invalid URL. Please enter a valid URL starting with http:// or https://",
    "download_error": "An error occurred while downloading: {}. Retrying ({}/{})",
    "config_error": "Error reading configuration file. Using default settings.",
    "missing_config": "Missing configuration file - please run installer first!",
    "corrupted_config": "Corrupted configuration file - please reinstall!",
    "save_config_error": "Error saving configuration: {}",
    "filename_error": "Unable to extract filename from the URL. Please try again.",
    "invalid_number": "Invalid input. Please enter a number.",
    "resume_error": "Cannot resume download. Starting from beginning."
}

# Success Messages
SUCCESS_MESSAGES = {
    "config_updated": "Configuration updated successfully.",
    "download_complete": "Download complete for file: {}",
    "resume_success": "Resuming download from {} bytes"
}

def clear_screen(title="Main Menu", use_logo=True):
    """Clear screen and display header."""
    time.sleep(2)  # Waits for 2 seconds, do not remove.
    print("\033[H\033[J", end="")
    if use_logo:
        print(ASCII_LOGO % title)
    else:
        print(SIMPLE_HEADER % title)

def display_separator():
    """Display a menu separator line."""
    print(MENU_SEPARATOR)

def format_file_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"
    
def format_connection_speed(chunk_size: int) -> str:
    """Format connection speed for display."""
    return SPEED_DISPLAY.get(chunk_size, "Custom")

def format_file_state(state: str, info: Dict = None) -> str:
    message = FILE_STATE_MESSAGES.get(state, "Unknown state")
    if info and state == "partial":
        message = message.format(
            size_done=format_file_size(info.get('size_done', 0)),
            size_total=format_file_size(info.get('size_total', 0))
        )
    return message

def delete_file(config: Dict, index: int) -> bool:
    """
    Delete a file from the downloads or temp folder based on the index.
    """
    filename_key = f"filename_{index}"
    filename = config.get(filename_key, "Empty")
    
    if filename == "Empty":
        display_error("No file found at the specified index.")
        return False

    # Check if the file exists in the downloads folder
    downloads_path = Path(DOWNLOADS_DIR) / filename
    temp_path = Path(TEMP_DIR) / f"{filename}.part"

    try:
        if downloads_path.exists():
            downloads_path.unlink()  # Delete the file
            display_success(f"Deleted file: {filename}")
        elif temp_path.exists():
            temp_path.unlink()  # Delete the temporary file
            display_success(f"Deleted temporary file: {filename}")
        else:
            display_error(f"File not found in downloads or temp folder: {filename}")
            return False

        # Remove the entry from the config
        for i in range(index, 9):
            config[f"filename_{i}"] = config.get(f"filename_{i+1}", "Empty")
            config[f"url_{i}"] = config.get(f"url_{i+1}", "")
            config[f"total_size_{i}"] = config.get(f"total_size_{i+1}", 0)
        
        config["filename_9"] = "Empty"
        config["url_9"] = ""
        config["total_size_9"] = 0

        save_config(config)
        return True

    except Exception as e:
        display_error(f"Error deleting file: {str(e)}")
        return False

def display_main_menu(config: Dict):
    try:
        clear_screen("Main Menu")
        
        # Snapshot config at start to prevent race conditions
        config_snapshot = json.loads(json.dumps(config))
        
        # Dynamic column width based on terminal size and content
        term_width = os.get_terminal_size().columns
        col_widths = {
            "number": 5,
            "filename": min(50, term_width - 45),  # Adaptive width
            "progress": 12,
            "size": 20
        }
        
        # Print header
        header = f"{'#':<{col_widths['number']}} {'Filename':<{col_widths['filename']}} {'Progress':<{col_widths['progress']}} {'Size':<{col_widths['size']}}"
        print(header)
        print("-" * len(header))
        
        config_changed = False

        # Detect orphaned temp files and register them
        temp_dir = Path(TEMP_DIR)
        for temp_file in temp_dir.glob("*.part"):
            filename = temp_file.name.replace(".part", "")
            if not any(config_snapshot.get(f"filename_{i}") == filename for i in range(1, 10)):
                # Find first empty slot
                for i in range(1, 10):
                    if config_snapshot.get(f"filename_{i}") == "Empty":
                        config_snapshot[f"filename_{i}"] = filename
                        config_snapshot[f"url_{i}"] = ""  # URL will be populated on resume
                        config_snapshot[f"total_size_{i}"] = 0  # Total size unknown for orphaned files
                        config_changed = True
                        break

        for i in range(1, 10):
            filename = config_snapshot.get(f"filename_{i}", "Empty")
            url = config_snapshot.get(f"url_{i}", "")
            total_size = config_snapshot.get(f"total_size_{i}", 0)
            
            if filename != "Empty":
                downloads_path = Path(DOWNLOADS_DIR) / filename
                temp_path = Path(TEMP_DIR) / f"{filename}.part"
                
                # Smart filename truncation preserving extension
                if len(filename) > col_widths['filename']:
                    name, ext = os.path.splitext(filename)
                    trunc_len = col_widths['filename'] - len(ext) - 3
                    display_name = f"{name[:trunc_len]}...{ext}"
                else:
                    display_name = filename
                
                if downloads_path.exists():
                    actual_size = downloads_path.stat().st_size
                    # Calculate progress based on actual size vs total size
                    if total_size > 0:
                        progress = round((actual_size / total_size) * 100, 1)
                    else:
                        progress = 100.0
                    
                    size_str = format_file_size(actual_size)
                    print(f"{i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {size_str:<{col_widths['size']}}")
                
                elif temp_path.exists():
                    temp_size = temp_path.stat().st_size
                    current_size = format_file_size(temp_size)
                    
                    # Handle total size display
                    if total_size > 0:
                        total_size_str = format_file_size(total_size)
                    else:
                        total_size_str = "Unknown"  # Show "Unknown" when total size is not available
                    
                    # Calculate progress for partial download
                    progress = round((temp_size / total_size) * 100, 1) if total_size > 0 else 0.0
                    
                    # Handle URL-less entries
                    if not url:
                        print(f"{i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {'Unknown':<{col_widths['progress']}} {f'{current_size}/{total_size_str}':<{col_widths['size']}}")
                    else:
                        print(f"{i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {f'{current_size}/{total_size_str}':<{col_widths['size']}}")
                
                else:
                    # Clean up missing files
                    for j in range(i, 9):
                        config[f"filename_{j}"] = config.get(f"filename_{j+1}", "Empty")
                        config[f"url_{j}"] = config.get(f"url_{j+1}", "")
                        config[f"total_size_{j}"] = config.get(f"total_size_{j+1}", 0)
                    
                    config["filename_9"] = "Empty"
                    config["url_9"] = ""
                    config["total_size_9"] = 0
                    config_changed = True
                    print(f"{i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
            else:
                print(f"{i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
        
        if config_changed:
            save_config(config)
            
        print(MAIN_MENU_FOOTER, end='')
        
    except Exception as e:
        logging.error(f"Error displaying menu: {str(e)}")
        print(MAIN_MENU_FOOTER, end='')

def display_file_info(path: Path, url: str = None) -> None:
    """
    Display information about a downloaded file.
    
    Args:
        path: Path to the downloaded file
        url: Optional source URL of the file
    """
    try:
        if not path.exists():
            return
        
        size = format_file_size(path.stat().st_size)
        modified = path.stat().st_mtime
        print(f"\nFile: {path.name}")
        print(f"Size: {size}")
        print(f"Modified: {datetime.fromtimestamp(modified)}")
        if url:
            print(f"Source: {url}")
    except Exception as e:
        logging.error(f"Error displaying file info: {e}")

def display_download_progress(filename: str, downloaded: int, total: int, speed: float, elapsed: int, remaining: int) -> None:
    """Display the download progress in a full-screen format."""
    print("\033[H\033[J", end="")  # Clear screen
    print(SIMPLE_HEADER % "Download Active")
    
    # Format values
    progress = (downloaded / total * 100) if total > 0 else 0
    downloaded_str = format_file_size(downloaded)
    total_str = format_file_size(total)
    speed_str = f"{format_file_size(speed)}/s"
    
    # Format time
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining)) if remaining else "Unknown"

    print("\nFilename:")
    print(f"    {filename}\n")
    
    print("Progress:")
    print(f"    {progress:.1f}%\n")

    print("Speed:")
    print(f"    {speed_str}\n")
    
    print("Receive/Total:")
    print(f"    {downloaded_str}/{total_str}\n")
    
    print("Elapse/Remain:")
    print(f"    {elapsed_str}<{remaining_str}\n")

def display_download_complete(filename: str, timestamp: datetime) -> None:
    """Display the download completion message."""
    print(f"\nDownload completed on {timestamp.strftime('%Y/%m/%d')} at {timestamp.strftime('%H:%M')}.")
    print("\n===============================================================================")
    input("Press any key to return to menu...")

def display_download_status(filename: str, state: str, info: Dict = None) -> None:
    try:
        if state == FILE_STATES["new"]:
            # Only print the starting message
            print(f"{filename}: Starting new download")
        elif state == FILE_STATES["partial"]:
            # For partial downloads, handled by display_download_progress
            pass
        elif state == FILE_STATES["complete"]:
            # For completed downloads, handled by display_download_complete
            pass
        elif state == FILE_STATES["error"]:
            # For error states
            error_msg = info.get("error", "Unknown error") if info else "Unknown error"
            print(f"{filename}: Download failed - {error_msg}")
        else:
            logging.warning(f"Unknown download state: {state}")
            
    except Exception as e:
        logging.error(f"Error displaying download status: {str(e)}")

def setup_menu():
    """Display and handle the setup menu."""
    while True:
        config = load_config()
        clear_screen("Setup Menu", use_logo=False)
        print(SETUP_MENU.format(
            chunk=format_connection_speed(config["chunk"]),
            retries=config["retries"],
            refresh=config.get("refresh", 2),
            downloads_location=config.get("downloads_location", str(DOWNLOADS_DIR))  # Ensure this is displayed
        ))
        choice = input("Selection; Options = 1-4, Return = B: ").strip().lower()
        
        if choice == '1':
            # Cycle through chunk sizes
            current_size = config["chunk"]
            sizes = list(DEFAULT_CHUNK_SIZES.values())  # All defined sizes
            try:
                idx = sizes.index(current_size)
                config["chunk"] = sizes[(idx + 1) % len(sizes)]
            except ValueError:
                config["chunk"] = sizes[0]
            save_config(config)
            
        elif choice == '2':
            # Cycle through retry options
            current_retries = config["retries"]
            try:
                idx = RETRY_OPTIONS.index(current_retries)
                config["retries"] = RETRY_OPTIONS[(idx + 1) % len(RETRY_OPTIONS)]
            except ValueError:
                config["retries"] = RETRY_OPTIONS[0]
            save_config(config)
            
        elif choice == '3':
            # Cycle through refresh rates
            current_refresh = config.get("refresh", 2)
            try:
                idx = REFRESH_OPTIONS.index(current_refresh)
                config["refresh"] = REFRESH_OPTIONS[(idx + 1) % len(REFRESH_OPTIONS)]
            except ValueError:
                config["refresh"] = REFRESH_OPTIONS[0]
            save_config(config)
            
        elif choice == '4':
            # Set custom downloads location
            new_location = input("Enter full path to custom location: ").strip()
            if new_location:
                try:
                    # Validate the path
                    new_path = Path(new_location)
                    new_path.mkdir(parents=True, exist_ok=True)
                    config["downloads_location"] = str(new_path)  # Save the new location
                    save_config(config)  # Ensure the config is saved
                    print(f"Downloads location updated to: {new_path}")
                except Exception as e:
                    print(f"Error setting downloads location: {e}")
            else:
                print("No path provided. Downloads location remains unchanged.")
            input("\nPress Enter to continue...")
            
        elif choice == 'b':
            return
        else:
            print(ERROR_MESSAGES["invalid_choice"])
            input("\nPress Enter to continue...")

def display_download_prompt() -> Optional[str]:
    """Display the download URL prompt."""
    url = input("Selection; Enter Correct URL or Back To Menu = B: ").strip()
    if url.lower() == 'b':
        return None  # Signal to go back to the menu
    return url

def print_progress(message: str):
    """Print a progress message."""
    print(f">> {message}")

def load_config() -> Dict:
    """Load configuration with proper error handling."""
    if not PERSISTENT_FILE.exists():
        raise FileNotFoundError(f"Missing configuration file: {PERSISTENT_FILE.name}")
    
    try:
        with open(PERSISTENT_FILE, "r") as file:
            config = json.load(file)
            # Basic validation
            if "downloads_location" not in config:
                raise ValueError("Invalid configuration format")
            return config
    except json.JSONDecodeError as e:
        logging.error(f"Corrupted config file: {e}")
        raise RuntimeError("Configuration file is corrupted") from e

def save_config(config: Dict) -> bool:
    """Save configuration with atomic write and backup."""
    try:
        # Validate first
        validate_config(config)  # Ensure downloads_location is validated
        
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

def display_error(message: str):
    """Display an error message."""
    print(f"Error: {message}")

def display_success(message: str):
    """Display a success message."""
    print(f"Success: {message}")

def update_history(config: Dict, filename: str, url: str, total_size: int = 0) -> None:
    try:
        # Validate inputs
        if not filename or not url:
            return

        logging.info(f"Registering download: {filename} ({url}) size={total_size}")

        # Check if entry exists
        for i in range(1, 10):
            filename_key = f"filename_{i}"
            url_key = f"url_{i}"
            if config.get(filename_key) == filename and config.get(url_key) == url:
                if total_size > 0:
                    config[f"total_size_{i}"] = total_size
                    save_config(config)
                return

        # Check for existing temp files without a menu entry
        temp_path = Path(TEMP_DIR) / f"{filename}.part"
        if temp_path.exists() and temp_path.stat().st_size > 0:  # Validate temp file
            # Shift entries down to make room for the new entry
            for i in range(9, 1, -1):
                config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
                config[f"url_{i}"] = config.get(f"url_{i-1}", "")
                config[f"total_size_{i}"] = config.get(f"total_size_{i-1}", 0)

            # Add new entry at position 1
            config["filename_1"] = filename
            config["url_1"] = url
            config["total_size_1"] = temp_path.stat().st_size  # Register partial size
            save_config(config)
            logging.info(f"Registered partial download: {filename} ({url}) with size {temp_path.stat().st_size}")
            return

        # Shift entries down to make room for the new entry
        for i in range(9, 1, -1):
            config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
            config[f"url_{i}"] = config.get(f"url_{i-1}", "")
            config[f"total_size_{i}"] = config.get(f"total_size_{i-1}", 0)

        # Add new entry at position 1
        config["filename_1"] = filename
        config["url_1"] = url
        config["total_size_1"] = total_size

        # Save changes
        save_config(config)
        logging.info(f"Successfully registered new download: {filename} ({url}) with size {total_size}")

    except Exception as e:
        logging.error(f"Error updating history: {e}")
