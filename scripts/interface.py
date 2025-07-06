# Script: `.\scripts\interface.py`

# Imports
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
    DOWNLOAD_TRACKING,
    BASE_DIR
)
from . import temporary 


# Menu Templates
SEPARATOR_THIN = "-" * 119
SEPARATOR_THICK = "=" * 119
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
    time.sleep(1)
    if temporary.PLATFORM == 'windows':
        os.system('cls')
    else:
        os.system('clear')
    print(SIMPLE_HEADER % title)

def clear_screen_multi(title="Main Menu", use_logo=True):
    time.sleep(1)
    if temporary.PLATFORM == 'windows':
        os.system('cls')
    else:
        os.system('clear')
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
        elif temp_path.exists():
            temp_path.unlink()
        else:
            display_error(f"File not found: {filename}")
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
        configure.Config_Manager.save(config)
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
    from .manage import handle_download, handle_orphaned_files, URLProcessor
    config = configure.Config_Manager.load()
    downloads_path = configure.get_downloads_path(config)
    while True:
        display_main_menu(config)
        choice = input().strip().lower()
        if choice == 's':
            setup_menu()
            config = configure.Config_Manager.load()
            continue
        if choice == 'r':
            handle_orphaned_files(config)
            config = configure.Config_Manager.load()
            clear_screen()
            continue
        if choice == 'q':
            exit_sequence()
            break
        if choice == '0':
            clear_screen("Initialize Download")
            while True:
                url_input = input("\nEnter download URL(s) separated by commas (Q to cancel): ").strip()
                if url_input.lower() == 'q':
                    break
                urls = [u.strip() for u in url_input.split(',') if u.strip()]
                valid_urls = []
                for url in urls:
                    if not URLProcessor.validate_url(url):
                        display_error(f"Invalid URL skipped: {url}")
                        time.sleep(1)
                        continue
                    valid_urls.append(url)
                if not valid_urls:
                    display_error("No valid URLs provided")
                    time.sleep(2)
                    continue
                free_slots = configure.Config_Manager.get_available_slots()
                if len(valid_urls) > free_slots:
                    display_error(f"Need {len(valid_urls)} slots, only {free_slots} available")
                    time.sleep(3)
                    continue
                from .manage import handle_multiple_downloads
                success_count = handle_multiple_downloads(valid_urls, config)
                display_success(f"Downloads Completed {success_count}/{len(valid_urls)} downloads")
                time.sleep(2)
                config = configure.Config_Manager.load()
                break
        elif choice.isdigit() and 1 <= int(choice) <= 9:
            index = int(choice)
            url = config.get(f"url_{index}", "")
            filename = config.get(f"filename_{index}", "Empty")
            if filename == "Empty":
                display_error("Invalid choice. Please try again.")
                time.sleep(3)
                continue
            clear_screen("Initialize Download")  # Transition immediately
            existing_file = downloads_path / filename
            if existing_file.exists():
                display_success(f"'{filename}' is already downloaded!")
                time.sleep(2)
                config = configure.Config_Manager.load()
                continue
            if not url:
                new_url = display_download_prompt()
                if new_url is None:
                    continue
                if not URLProcessor.validate_url(new_url):
                    display_error("Invalid URL. Please enter a valid URL starting with http:// or https://")
                    time.sleep(3)
                    continue
                config[f"url_{index}"] = new_url
                configure.Config_Manager.save(config)
                success, error = handle_download(new_url, config)
                if not success:
                    display_error(error)
                    time.sleep(3)
                else:
                    config = configure.Config_Manager.load()
                time.sleep(2)
            else:
                success, error = handle_download(url, config)
                if not success:
                    display_error(error)
                    time.sleep(3)
                else:
                    config = configure.Config_Manager.load()
                time.sleep(2)
        elif choice == 'd':
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
    print("A glorious program by Wiseman-Timelord!")
    print("Website: WiseTime.Rf.Gd")
    print("Patreon: Patreon.Com/WiseManTimeLord")
    print("Kofi: Ko-Fi.Com/WiseManTimeLord")
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

def display_batch_progress(active_downloads: list):
    clear_screen("Batch Downloads")
    for idx, dl in enumerate(active_downloads, 1):
        print(f"Download {idx}: {truncate_filename(dl['filename'], 40)}")
        print(f"Progress: {dl['progress']}% | Speed: {format_file_size(dl['speed'])}/s")
    print(SEPARATOR_THICK)

def get_active_downloads() -> list:
    """Get sanitized list of active downloads with calculated metrics and batch info"""
    global ACTIVE_DOWNLOADS
    return [{
        'filename': d.get('filename', 'Unknown'),
        'current': d.get('current', 0),
        'total': d.get('total', 1),
        'speed': d.get('speed', 0),
        'elapsed': time.time() - d.get('start_time', time.time()),
        'remaining': (d.get('total', 1) - d.get('current', 0)) / d['speed'] if d.get('speed', 0) > 0 else 0,
        'batch_index': d.get('batch_index'),
        'batch_total': d.get('batch_total')
    } for d in ACTIVE_DOWNLOADS if 'current' in d]

def display_download_state(multiple: list = None) -> None:
    """Display download status for active downloads with distinct single and batch interfaces"""
    if not multiple:
        clear_screen("Download Active")
        print("\n\n\nNo active downloads.\n\n\n")
        print(SEPARATOR_THIN)
        print("Selection; Back to Menu = B: ", end="", flush=True)
        return

    # Determine if this is a batch download (check ANY active downloads for batch context)
    is_batch = any(
        'batch_total' in dl and dl['batch_total'] is not None and dl['batch_total'] > 1
        for dl in multiple
    )

    # Select appropriate header
    header = "Batch Download Active" if is_batch else "Download Active"
    clear_screen(header)
    print("\n\n")  # Two blank lines after header

    if is_batch:
        # Batch download interface
        for dl in multiple:
            if 'batch_index' in dl and 'batch_total' in dl:
                print(f"    File in Sequence:\n        {dl['batch_index']}/{dl['batch_total']}\n")
                progress_pct = (dl['current'] / dl['total']) * 100 if dl['total'] > 0 else 0
                speed_str = f"{format_file_size(dl['speed'])}/s"
                size_str = f"{format_file_size(dl['current'])}/{format_file_size(dl['total'])}"
                elapsed_str = time.strftime("%H:%M:%S", time.gmtime(dl['elapsed']))
                remaining_str = time.strftime("%H:%M:%S", time.gmtime(dl['remaining'])) if dl['remaining'] > 0 else "--:--:--"

                print(f"    Filename:\n        {dl['filename']}\n")
                print(f"    Progress:\n        {progress_pct:.1f}%\n")
                print(f"    Speed:\n        {speed_str}\n")
                print(f"    Received/Total:\n        {size_str}\n")
                print(f"    Elapsed/Remaining:\n        {elapsed_str}<{remaining_str}\n")
                print("\n")  # One blank line between downloads
    else:
        # Single download interface (only first active download)
        dl = multiple[0]
        progress_pct = (dl['current'] / dl['total']) * 100 if dl['total'] > 0 else 0
        speed_str = f"{format_file_size(dl['speed'])}/s"
        size_str = f"{format_file_size(dl['current'])}/{format_file_size(dl['total'])}"
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(dl['elapsed']))
        remaining_str = time.strftime("%H:%M:%S", time.gmtime(dl['remaining'])) if dl['remaining'] > 0 else "--:--:--"

        print(f"    Filename:\n        {dl['filename']}\n")
        print(f"    Progress:\n        {progress_pct:.1f}%\n")
        print(f"    Speed:\n        {speed_str}\n")
        print(f"    Received/Total:\n        {size_str}\n")
        print(f"    Elapsed/Remaining:\n        {elapsed_str}<{remaining_str}\n")
        print("\n")  # One blank line before separator

    print(SEPARATOR_THIN)
    print("Selection; Abandon Download = A, Wait for Completion = >_>: ", end="", flush=True)

# Possibly to stop circular import
from pathlib import Path

def display_download_summary(
    filename: str,
    total_size: int,
    average_speed: float,
    elapsed: float,
    timestamp: datetime,
    destination: str,
    batch_mode: bool = False
) -> None:
    import time
    from .interface import clear_screen, SEPARATOR_THIN
    from pathlib import Path

    clear_screen("Download Summary")
    
    # Format all values for display
    elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    size_str = format_file_size(total_size)
    speed_str = f"{format_file_size(average_speed)}/s"
    destination_dir = str(Path(destination).parent)

    # Build the summary content
    summary_content = [
        "\n\n",
        f"    Filename:",
        f"        {filename}\n",
        f"    Completed At:",
        f"        {timestamp.strftime('%Y/%m/%d %H:%M:%S')}\n",
        f"    Size:",
        f"        {size_str}\n",
        f"    Average Speed:",
        f"        {speed_str}\n",
        f"    Download Time:",
        f"        {elapsed_str}\n",
        f"    Saved To:",
        f"        {destination_dir}",
        "\n\n",
        SEPARATOR_THIN
    ]

    # Display the summary
    print("\n".join(summary_content))
    
    if batch_mode:
        # Display the summary for 5 seconds, then proceed
        print("5 Seconds until, Next File or Main Menu...", end="", flush=True)
        time.sleep(5)
        print("\r" + " " * 50 + "\r", end="", flush=True)  # Clear the line
    else:
        # Wait for any key press for single downloads
        input("10 Seconds until Main Menu...")
        time.sleep(10)
    
    clear_screen("Download Summary")

def display_download_complete(filename: str, timestamp: datetime) -> None:
    """
    Display the download completion message.
    """
    print(f"\nDownload completed on {timestamp.strftime('%Y/%m/%d')} at {timestamp.strftime('%H:%M')}.")
    print(SEPARATOR_THIN)
    input("Press any key to return to menu...")


def setup_menu():
    while True:
        config = configure.Config_Manager.load()
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
            configure.Config_Manager.save(config)

        elif choice == '2':
            # Cycle through retry options
            current_retries = config["retries"]
            try:
                idx = RETRY_OPTIONS.index(current_retries)
                config["retries"] = RETRY_OPTIONS[(idx + 1) % len(RETRY_OPTIONS)]
            except ValueError:
                config["retries"] = RETRY_OPTIONS[0]
            configure.Config_Manager.save(config)

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
                    configure.Config_Manager.save(config)
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
                    configure.Config_Manager.save(config)  # Fixed
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
            configure.Config_Manager.save(config)  # Fixed
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
        configure.Config_Manager.save(config)  # Fixed
        print(f"Successfully registered new download: {filename} ({short_url}) with size {total_size}")

    except Exception as e:
        display_error(f"Error updating history: {e}")
        time.sleep(3)