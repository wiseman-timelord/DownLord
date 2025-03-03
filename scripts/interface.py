# Script: `.\scripts\interface.py`

import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Union
from datetime import datetime
from .configure import ConfigManager
from .temporary import (
    ERROR_HANDLING,
    SUCCESS_MESSAGES,
    FILE_STATE_MESSAGES,
    PERSISTENT_FILE,
    DOWNLOADS_DIR,
    TEMP_DIR,
    DEFAULT_CHUNK_SIZES,
    SPEED_DISPLAY,
    BASE_DIR,
    RETRY_OPTIONS
)

# ASCII Art
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
            config[f"total_size_{i}"] = config.get(f"total_size_{next_i}", 0)
        
        config["filename_9"] = "Empty"
        config["url_9"] = ""
        config["total_size_9"] = 0
        ConfigManager.save(config)
        return True
    except Exception as e:
        display_error(f"Error deleting file: {str(e)}")
        time.sleep(3)
        return False


def display_main_menu(config: Dict):
    """
    Display the main menu with download options.
    """
    try:
        clear_screen_multi("Main Menu")
        config_snapshot = json.loads(json.dumps(config))
        term_width = os.get_terminal_size().columns
        col_widths = {
            "number": 5,
            "filename": min(50, term_width - 45),
            "progress": 12,
            "size": 20
        }
        
        # Resolve downloads location
        downloads_location_str = config.get("downloads_location", "downloads")
        downloads_path = Path(downloads_location_str)
        if not downloads_path.is_absolute():
            downloads_path = BASE_DIR / downloads_path
        downloads_path = downloads_path.resolve()
        
        print(f"    {'#.':<{col_widths['number']}} {'Filename':<{col_widths['filename']}} {'Progress':<{col_widths['progress']}} {'Size':<{col_widths['size']}}")
        print(SEPARATOR_THICK)
        print()
        
        config_changed = False
        for i in range(1, 10):
            filename = config_snapshot.get(f"filename_{i}", "Empty")
            url = config_snapshot.get(f"url_{i}", "")
            total_size = config_snapshot.get(f"total_size_{i}", 0)
            
            # Add blank line before each entry
            print()
            
            if filename != "Empty":
                file_path = downloads_path / filename  # Use resolved path
                temp_path = Path(TEMP_DIR) / f"{filename}.part"
                
                # Smart filename truncation preserving extension
                if len(filename) > col_widths['filename']:
                    name, ext = os.path.splitext(filename)
                    trunc_len = col_widths['filename'] - len(ext) - 3
                    display_name = f"{name[:trunc_len]}...{ext}"
                else:
                    display_name = filename
                
                if file_path.exists():  # Changed from downloads_path to file_path for consistency
                    actual_size = file_path.stat().st_size
                    # Calculate progress based on actual size vs total size
                    if total_size > 0:
                        progress = round((actual_size / total_size) * 100, 1)
                    else:
                        progress = 100.0
                    
                    size_str = format_file_size(actual_size)
                    print(f"    {i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {size_str:<{col_widths['size']}}")
                
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
                        print(f"    {i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {'Unknown':<{col_widths['progress']}} {f'{current_size}/{total_size_str}':<{col_widths['size']}}")
                    else:
                        print(f"    {i:<{col_widths['number']}} {display_name:<{col_widths['filename']}} {f'{progress:.1f}%':<{col_widths['progress']}} {f'{current_size}/{total_size_str}':<{col_widths['size']}}")
                
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
                    print(f"    {i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
            else:
                print(f"    {i:<{col_widths['number']}} {'Empty':<{col_widths['filename']}} {'-':<{col_widths['progress']}} {'-':<{col_widths['size']}}")
        
        if config_changed:
            ConfigManager.save(config)
        
        # Add blank line before footer
        print("\n")
        print(MAIN_MENU_FOOTER, end='')
    
    except Exception as e:
        display_error(f"Menu display error: {str(e)}")
        time.sleep(3)
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
        config = ConfigManager.load()
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
            ConfigManager.save(config)

        elif choice == '2':
            # Cycle through retry options
            current_retries = config["retries"]
            try:
                idx = RETRY_OPTIONS.index(current_retries)
                config["retries"] = RETRY_OPTIONS[(idx + 1) % len(RETRY_OPTIONS)]
            except ValueError:
                config["retries"] = RETRY_OPTIONS[0]
            ConfigManager.save(config)

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
                        ConfigManager.save(config)
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
                    ConfigManager.save(config)
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
            ConfigManager.save(config)
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
        ConfigManager.save(config)
        print(f"Successfully registered new download: {filename} ({short_url}) with size {total_size}")

    except Exception as e:
        display_error(f"Error updating history: {e}")
        time.sleep(3)