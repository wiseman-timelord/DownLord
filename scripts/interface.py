# Script: `.\scripts\interface.py`

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime
from . import configure
from .temporary import (
    ERROR_HANDLING,
    SUCCESS_MESSAGES,
    FILE_STATE_MESSAGES,
    PERSISTENT_FILE,
    DOWNLOADS_DIR,
    TEMP_DIR,
    DEFAULT_CHUNK_SIZES,
    SPEED_DISPLAY,
    BASE_DIR
)

# Menu Templates
SEPARATOR_THIN = "-" * 120
SEPARATOR_THICK = "=" * 120
MENU_SEPARATOR = SEPARATOR_THIN

SIMPLE_HEADER = f'''{SEPARATOR_THICK}
    DownLord: %s
{SEPARATOR_THICK}'''

MULTI_HEADER = f'''{SEPARATOR_THICK}
    DownLord: %s
{SEPARATOR_THIN}'''

MAIN_MENU_FOOTER = f"""{SEPARATOR_THICK}
Selection; New URL = 0, Continue = 1-9, Refresh = R, Delete = D, Setup = S, Quit = Q: """

SETUP_MENU = f"""








    1. Connection Speed       ({{chunk}})

    2. Maximum Retries        ({{retries}})

    3. Downloads Location     ({{downloads_location}})









"""


def clear_screen(title="Main Menu", use_logo=True):
    """
    Clear the screen and display the header.
    """
    time.sleep(1)  # Waits for 2 seconds, do not remove.
    print("\033[H\033[J", end="")
    print(SIMPLE_HEADER % title)

def clear_screen_multi(title="Main Menu", use_logo=True):
    """
    Clear the screen and display the header.
    """
    time.sleep(1)  # Waits for 2 seconds, do not remove.
    print("\033[H\033[J", end="")
    print(MULTI_HEADER % title)

def display_separator():
    """
    Display a menu separator line.
    """
    print(MENU_SEPARATOR)

def calculate_column_widths(term_width: int) -> Dict[str, int]:
    return {
        "number": 5,
        "filename": min(50, term_width - 45),
        "progress": 12,
        "size": 20
    }

def truncate_filename(filename: str, max_length: int) -> str:
    if len(filename) <= max_length:
        return filename
    name, ext = os.path.splitext(filename)
    trunc_len = max_length - len(ext) - 3
    if trunc_len > 0:
        return f"{name[:trunc_len]}...{ext}"
    else:
        return f"...{ext}"

def get_file_status(config: Dict, index: int, downloads_path: Path) -> tuple[str, Optional[float], Optional[str]]:
    filename = config.get(f"filename_{index}", "Empty")
    if filename == "Empty":
        return "empty", None, None
    
    file_path = downloads_path / filename
    temp_path = Path(TEMP_DIR) / f"{filename}.part"
    
    if file_path.exists():
        total_size = config.get(f"total_size_{index}", 0)
        actual_size = file_path.stat().st_size
        if total_size > 0:
            progress = (actual_size / total_size) * 100
        else:
            progress = 100.0
        size_str = format_file_size(actual_size)
        return "complete", progress, size_str
    
    elif temp_path.exists():
        temp_size = temp_path.stat().st_size
        total_size = config.get(f"total_size_{index}", 0)
        if total_size > 0:
            progress = (temp_size / total_size) * 100
            size_str = f"{format_file_size(temp_size)}/{format_file_size(total_size)}"
        else:
            progress = 0.0
            size_str = f"{format_file_size(temp_size)}/Unknown"
        return "partial", progress, size_str
    
    else:
        return "missing", None, None

def format_file_size(size: int) -> str:
    """
    Format file size in bytes to a human-readable string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def format_connection_speed(chunk_size: int) -> str:
    """
    Format connection speed for display.
    """
    return SPEED_DISPLAY.get(chunk_size, "Custom")


def format_file_state(state: str, info: Dict = None) -> str:
    """
    Format file state for display.
    """
    message = FILE_STATE_MESSAGES.get(state, "Unknown state")
    if info and state == "partial":
        message = message.format(
            size_done=format_file_size(info.get('size_done', 0)),
            size_total=format_file_size(info.get('size_total', 0))
        )
    return message


def delete_file(config: Dict, index: int) -> bool:
    filename_key = f"filename_{index}"
    filename = config.get(filename_key, "Empty")
    if filename == "Empty":
        display_error("No file found at the specified index.")
        time.sleep(3)
        return False
    
    # Resolve downloads location
    downloads_location_str = config.get("downloads_location", "downloads")
    downloads_path = Path(downloads_location_str)
    if not downloads_path.is_absolute():
        downloads_path = BASE_DIR / downloads_path
    downloads_path = downloads_path.resolve()
    file_path = downloads_path / filename
    temp_path = Path(TEMP_DIR) / f"{filename}.part"
    
    try:
        if file_path.exists():
            file_path.unlink()
            display_success(f"Deleted file: {filename}")
        elif temp_path.exists():
            temp_path.unlink()
            display_success(f"Deleted temporary file: {filename}")
        else:
            display_error(f"File not found in downloads or temp folder: {filename}")
            time.sleep(3)
            return False
        
        for i in range(index, 9):
            next_i = i + 1
            config[f"filename_{i}"] = config.get(f"filename_{next_i}", "Empty")
            config[f"url_{i}"] = config.get(f"url_{next_i}", "")
            config[f"total_size_{i}"] = config.get(f"total_size_{i+1}", 0)
        
        config["filename_9"] = "Empty"
        config["url_9"] = ""
        config["total_size_9"] = 0
        configure.ConfigManager.save(config)
        return True
    except Exception as e:
        display_error(f"Error deleting file: {str(e)}")
        time.sleep(3)
        return False

def handle_error(message: str, sleep_time: int = 3):
    display_error(message)
    time.sleep(sleep_time)

def get_user_choice_after_error() -> str:
    return input("\nSelection; Retry URL Now = R, Alternate URL = 0, Back to Menu = B: ").strip().lower()

def prompt_for_download():
    from .manage import handle_download, handle_orphaned_files, URLProcessor # Deferred import
    # Ensure clean state before showing menu
    config = configure.ConfigManager.load()
    downloads_path = configure.get_downloads_path(config)

    while True:
        display_main_menu(config)
        choice = input().strip().lower()

        if choice == 's':
            setup_menu()
            config = configure.ConfigManager.load()  # Reload config after setup
            continue

        if choice == 'r':
            handle_orphaned_files(config)
            config = configure.ConfigManager.load()  # Reload config after refresh
            clear_screen()
            continue

        if choice == 'q':
            exit_sequence()  # Display the exit sequence
            break  # Exit the loop, ending the script

        if choice == '0':
            while True:
                clear_screen("Initialize Download")
                url = input("\nEnter download URL (Q to cancel): ").strip()
                if url.lower() == 'q':
                    break  # Exit the loop and return to the main menu
                elif len(url) < 5:
                    display_error("URL must be at least 5 characters long. Please try again.")
                    time.sleep(3)  # Give the user time to read the error message
                else:
                    # Resolve downloads location
                    downloads_location_str = config.get("downloads_location", "downloads")
                    downloads_path = Path(downloads_location_str)
                    if not downloads_path.is_absolute():
                        downloads_path = BASE_DIR / downloads_path
                    downloads_path = downloads_path.resolve()
                    
                    success = handle_download(url, config)
                    if success:
                        config = configure.ConfigManager.load()  # Reload config after successful download
                    time.sleep(2)
                    break  # Exit the loop after attempting the download

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
                config = configure.ConfigManager.load()  # Reload to refresh any changes
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
                configure.ConfigManager.save(config)

                # Start the download with the new URL and existing .part file
                success = handle_download(new_url, config)
                if success:
                    config = configure.ConfigManager.load()  # Reload config after successful download
                time.sleep(2)
            else:
                # Handle normal download
                success = handle_download(url, config)
                if success:
                    config = configure.ConfigManager.load()  # Reload config after successful download
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

def exit_sequence():
    """
    Display the exit sequence with timed messages and an overwriting countdown with 's'.
    """
    clear_screen("Exit Sequence")  # Displays the header
    print()  # Adds a blank line after the header
    print("Shutting down DownLord...")
    time.sleep(1)  # Wait 1 second
    print("Promotion: A glorious program by Wiseman-Timelord!")
    time.sleep(1)  # Wait 2 seconds
    print("Terminating program in 5 seconds", end='')  # Initial message without dots
    for i in range(5, 0, -1):
        print(f"\rTerminating program in 5 seconds...{i}s", end='', flush=True)  # Overwrite with countdown
        time.sleep(1)  # Wait 1 second between updates
    print("\n")  # Add a newline after the countdown # No newline, flush to show immediately

def display_main_menu(config: Dict):
    try:
        clear_screen_multi("Main Menu")
        config_snapshot = json.loads(json.dumps(config))
        term_width = os.get_terminal_size().columns
        col_widths = calculate_column_widths(term_width)
        
        downloads_path = configure.get_downloads_path(config)
        
        # Header with blank line after
        print(f"    {'#.':<{col_widths['number']}} {'Filename':<{col_widths['filename']}} {'Progress':<{col_widths['progress']}} {'Size':<{col_widths['size']}}")
        print(SEPARATOR_THICK)
        print()  # Blank line after header
        
        config_changed = False
        for i in range(1, 10):
            status, progress, size_str = get_file_status(config_snapshot, i, downloads_path)
            print()  # Blank line before each entry
            if status == "empty":
                print(f"    {i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
            elif status == "complete":
                filename = config_snapshot[f"filename_{i}"]
                display_name = truncate_filename(filename, col_widths['filename'])
                print(f"    {i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {size_str:<{col_widths['size']}}")
            elif status == "partial":
                filename = config_snapshot[f"filename_{i}"]
                display_name = truncate_filename(filename, col_widths['filename'])
                print(f"    {i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {size_str:<{col_widths['size']}}")
            elif status == "missing":
                # --- REMOVED MANUAL SHIFTING CODE ---
                print(f"    {i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
        
        # Footer with two blank lines before and after
        print()  # First blank line before footer
        print()  # Second blank line before footer
        print(MAIN_MENU_FOOTER, end='')
        
    except Exception as e:
        handle_error(f"Menu display error: {str(e)}")
        print(MAIN_MENU_FOOTER, end='')


def display_file_info(path: Path, url: str = None) -> None:
    """
    Display information about a downloaded file.
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
        display_error(f"Error displaying file info: {e}")
        time.sleep(3)


def display_download_state(
    filename: str,
    current_size: int,
    total_size: int,
    speed: float,
    elapsed: float,
    remaining: float
) -> None:
    """Display download status in the new multi-line format."""
    clear_screen("Download Active")
    
    progress = (current_size / total_size) * 100 if total_size > 0 else 0
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    remaining_str = time.strftime("%H:%M:%S", time.gmtime(remaining)) if remaining > 0 else "--:--:--"

    print(f"""



    Filename:
        {filename}

    Progress:
        {progress:.1f}%

    Speed:
        {format_file_size(speed)}/s

    Received/Total:
        {format_file_size(current_size)}/{format_file_size(total_size)}

    Elapsed/Remaining:
        {elapsed_str}<{remaining_str}



    
    
{SEPARATOR_THICK}Selection; Abandon = A, Wait = >_>: """)


def display_download_summary(
    filename: str,
    total_size: int,
    average_speed: float,
    elapsed: float,
    timestamp: datetime,
    destination: str
) -> None:
    """Display detailed download summary."""
    clear_screen("Download Summary")
    
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    size_str = format_file_size(total_size)
    speed_str = f"{format_file_size(average_speed)}/s"
    
    print(f"""
    
    
    Filename:
        {filename}
        
    Completed:
        {timestamp.strftime('%Y/%m/%d %H:%M:%S')}
        
    Total Size:
        {size_str}
        
    Average Speed:
        {speed_str}
        
    Elapsed Time:
        {elapsed_str}
        
    Location:
        {destination}
    
    
    
{SEPARATOR_THICK}
Press any key for Main Menu...""")
    input()

def display_download_complete(filename: str, timestamp: datetime) -> None:
    """
    Display the download completion message.
    """
    print(f"\nDownload completed on {timestamp.strftime('%Y/%m/%d')} at {timestamp.strftime('%H:%M')}.")
    print(SEPARATOR_THIN)
    input("Press any key to return to menu...")


def setup_menu():
    while True:
        config = configure.ConfigManager.load()
        clear_screen("Setup Menu", use_logo=False)
        print(SETUP_MENU.format(
            chunk=format_connection_speed(config["chunk"]),
            retries=config["retries"],
            downloads_location=config.get("downloads_location", str(DOWNLOADS_DIR))
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
            configure.ConfigManager.save(config)

        elif choice == '2':
            # Cycle through retry options
            current_retries = config["retries"]
            try:
                idx = RETRY_OPTIONS.index(current_retries)
                config["retries"] = RETRY_OPTIONS[(idx + 1) % len(RETRY_OPTIONS)]
            except ValueError:
                config["retries"] = RETRY_OPTIONS[0]
            configure.ConfigManager.save(config)

        elif choice == '3':
            new_location = input("Enter full path to custom location: ").strip()
            if new_location:
                try:
                    test_path = Path(new_location)
                    if not test_path.is_absolute():
                        test_path = BASE_DIR / test_path
                    test_path = test_path.resolve()
                    test_path.mkdir(parents=True, exist_ok=True)
                    config["downloads_location"] = new_location  # Store as-is
                    configure.ConfigManager.save(config)
                    print(f"Downloads location updated to: {new_location}")
                except Exception as e:
                    print(f"Error setting location: {e}")
            else:
                print("No path provided. Location unchanged.")
            time.sleep(3)
                
        elif choice == 'b':
            return
        else:
            print(ERROR_HANDLING["messages"]["invalid_choice"])
            time.sleep(3)


def display_download_prompt() -> Optional[str]:
    """
    Display the download URL prompt.
    """
    url = input("Selection; Enter Correct URL or Back To Menu = B: ").strip()
    if url.lower() == 'b':
        return None  # Signal to go back to the menu
    return url


def print_progress(message: str):
    """
    Print a progress message.
    """
    print(f">> {message}")


def display_error(message: str):
    """
    Display an error message.
    """
    print(f"Error: {message}")


def display_success(message: str):
    """
    Display a success message.
    """
    print(f"Success: {message}")


def update_history(config: Dict, filename: str, url: str, total_size: int = 0) -> None:
    """
    Update the download history in the configuration.
    """
    try:
        # Validate inputs
        if not filename or not url:
            return

        # Truncate the URL for display
        short_url = url if len(url) <= 60 else f"{url[:57]}..."

        # Check if entry exists
        for i in range(1, 10):
            if config.get(f"filename_{i}") == filename and config.get(f"url_{i}") == url:
                if total_size > 0:
                    config[f"total_size_{i}"] = total_size
                    configure.ConfigManager.save(config)  # Fixed
                return

        # Check for existing temp files without a menu entry
        temp_path = Path(TEMP_DIR) / f"{filename}.part"
        if temp_path.exists() and temp_path.stat().st_size > 0:
            # Shift entries down to make room for the new entry
            for i in range(9, 1, -1):
                config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
                config[f"url_{i}"] = config.get(f"url_{i-1}", "")
                config[f"total_size_{i}"] = config.get(f"total_size_{i-1}", 0)

            # Add new entry at position 1
            config["filename_1"] = filename
            config["url_1"] = url
            config["total_size_1"] = temp_path.stat().st_size
            configure.ConfigManager.save(config)  # Fixed
            print(f"Registered partial download: {filename} ({short_url}) with size {temp_path.stat().st_size}")
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
        configure.ConfigManager.save(config)  # Fixed
        print(f"Successfully registered new download: {filename} ({short_url}) with size {total_size}")

    except Exception as e:
        display_error(f"Error updating history: {e}")
        time.sleep(3)