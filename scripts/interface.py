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

def _clear_terminal():
    """Clear the terminal, keying off the real host OS rather than argv."""
    if temporary.platform_name() == 'windows':
        os.system('cls')
    else:
        os.system('clear')

def clear_screen(title="Main Menu", use_logo=True, pause: float = 1.0):
    # `pause` exists because this used to hard-code time.sleep(1).  The download
    # display calls this once per refresh, so that sleep was silently added to
    # DISPLAY_REFRESH: a "1 second" refresh actually took 2 seconds, which is
    # half of why abandoning a download felt unresponsive.  Screens the user
    # reads in passing keep the default; the download screen passes pause=0.
    if pause:
        time.sleep(pause)
    _clear_terminal()
    print(SIMPLE_HEADER % title)

def clear_screen_multi(title="Main Menu", use_logo=True, pause: float = 1.0):
    if pause:
        time.sleep(pause)
    _clear_terminal()
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

def get_terminal_width(default: int = 120) -> int:
    """Terminal width, with a fallback.

    os.get_terminal_size() raises OSError ("Inappropriate ioctl for device")
    whenever stdout is not a terminal -- piping output, redirecting to a file,
    running under a service manager.  That exception used to escape into
    display_main_menu's handler and replace the entire menu with
    "Error: Menu display error: [Errno 25]".  The layout assumes 120 anyway.
    """
    try:
        return os.get_terminal_size().columns
    except (OSError, ValueError):
        return default


def get_file_status(config: Dict, index: int, downloads_path: Path) -> tuple:
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
        # Both are removed, not one-or-the-other.  The old `elif` left a stale
        # .part behind whenever a finished file and a partial existed for the
        # same name, and that orphan then reappeared in the list on next launch
        # via _register_existing_temp_files.
        removed = False
        if file_path.exists():
            file_path.unlink()
            removed = True
        if temp_path.exists():
            temp_path.unlink()
            removed = True
        if not removed:
            display_error(f"File not found: {filename}")
            time.sleep(3)
            # Entry is stale; still drop it from the list below.
        
        for i in range(index, 9):
            next_i = i + 1
            config[f"filename_{i}"] = config.get(f"filename_{next_i}", "Empty")
            config[f"url_{i}"] = config.get(f"url_{next_i}", "")
            config[f"total_size_{i}"] = config.get(f"total_size_{next_i}", 0)
        
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
    while True:
        # Recomputed per loop: it used to be resolved once before the loop, so
        # changing Downloads Location in the Setup menu had no effect on the
        # "already downloaded?" check until the program was restarted.
        downloads_path = configure.get_downloads_path(config)
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

            print(f"\n    {filename}\n")

            target_url = url
            if url:
                # A URL is already remembered for this slot, so offer to reuse it
                # rather than making the user go back out to option 0 and paste
                # the whole thing in again.
                answer = input(
                    "Do you want to, Continue/Resume (C) or Enter a new URL (N)? (Back = B): "
                ).strip().lower()
                while answer not in ("c", "n", "b"):
                    answer = input("Selection; Continue = C, New URL = N, Back = B: ").strip().lower()
                if answer == 'b':
                    continue
                if answer == 'n':
                    target_url = ""

            if not target_url:
                new_url = input("Enter new URL for the download (Back = B): ").strip()
                if not new_url or new_url.lower() == 'b':
                    continue
                if not URLProcessor.validate_url(new_url):
                    display_error("Invalid URL. Please enter a valid URL starting with http:// or https://")
                    time.sleep(3)
                    continue
                config[f"url_{index}"] = new_url
                configure.Config_Manager.save(config)
                target_url = new_url

            success, error = handle_download(target_url, config)
            if not success and error:
                # `error` is empty when the user deliberately abandoned; that
                # path has already shown its own message.
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
        term_width = get_terminal_width()
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

# NOTE: get_active_downloads used to be defined here as well as in manage.py.
# This copy referenced ACTIVE_DOWNLOADS, which interface.py never imports, so it
# raised NameError if anything ever called it.  manage.get_active_downloads is
# the live one (and it carries resume_status, which this copy dropped).

def display_download_state(multiple: list = None) -> None:
    """Display download status for active downloads with distinct single and batch interfaces"""
    if not multiple:
        clear_screen("Download Active", pause=0)
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
    clear_screen(header, pause=0)
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
                resume_str = dl.get('resume_status', 'Pending')

                print(f"    Filename:\n        {dl['filename']}\n")
                print(f"    Resume:\n        {resume_str}\n")
                print(f"    Progress:\n        {progress_pct:.1f}%\n")
                print(f"    Speed:\n        {speed_str}\n")
                print(f"    Received/Total:\n        {size_str}\n")
                print(f"    Elapsed/Remaining:\n        {elapsed_str}<{remaining_str}\n")
                print()  # One blank line between downloads
    else:
        # Single download interface (only first active download)
        dl = multiple[0]
        progress_pct = (dl['current'] / dl['total']) * 100 if dl['total'] > 0 else 0
        speed_str = f"{format_file_size(dl['speed'])}/s"
        size_str = f"{format_file_size(dl['current'])}/{format_file_size(dl['total'])}"
        elapsed_str = time.strftime("%H:%M:%S", time.gmtime(dl['elapsed']))
        remaining_str = time.strftime("%H:%M:%S", time.gmtime(dl['remaining'])) if dl['remaining'] > 0 else "--:--:--"
        resume_str = dl.get('resume_status', 'Pending')

        print(f"    Filename:\n        {dl['filename']}\n")
        print(f"    Resume:\n        {resume_str}\n")
        print(f"    Progress:\n        {progress_pct:.1f}%\n")
        print(f"    Speed:\n        {speed_str}\n")
        print(f"    Received/Total:\n        {size_str}\n")
        print(f"    Elapsed/Remaining:\n        {elapsed_str}<{remaining_str}\n")
        print()  # One blank line before separator

    print(SEPARATOR_THIN)
    if temporary.ABORT_EVENT.is_set():
        # The key listener sets ABORT_EVENT the moment "A" is seen.  The loop
        # itself can only stop once the in-flight chunk has finished landing,
        # so say so rather than leaving the prompt up looking ignored.
        print("Stopping the active download, finishing current chunk...", end="", flush=True)
    else:
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
    
    # Countdown rather than input().  The single-download branch used to call
    # input() -- which blocks forever, contradicting its own "10 Seconds until
    # Main Menu..." text -- and then slept 10s on top once Enter was pressed.
    # On Linux it ran while the terminal was still in cbreak mode (download_file
    # restores termios in its finally, which has not run yet at this point), so
    # the user was typing with no echo, and any leftover keystrokes in the buffer
    # dismissed it instantly.
    wait_seconds = 5 if batch_mode else 10
    tail = "Next File or Main Menu" if batch_mode else "Main Menu"
    for remaining in range(wait_seconds, 0, -1):
        print(f"\r{remaining} Seconds until, {tail}...".ljust(60), end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 60 + "\r", end="", flush=True)

    clear_screen("Download Summary", pause=0)

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


def _sync_slots(config: Dict, fresh: Dict) -> None:
    """Copy only the slot keys from `fresh` into the caller's `config`.

    Deliberately NOT config.clear()/config.update(fresh): the caller's dict may
    hold settings it has not written to disk yet, and replacing it wholesale
    would silently discard them.  Only the 9 slots are authoritative-on-disk.
    """
    for i in range(1, 10):
        for key in (f"filename_{i}", f"url_{i}", f"total_size_{i}"):
            config[key] = fresh[key]


def update_history(config: Dict, filename: str, url: str, total_size: int = 0) -> bool:
    """
    Register or update a download entry.  Returns True if the entry is present
    in the slot list afterwards.

    THE FILENAME IS THE IDENTITY KEY.  It is what the file in `downloads\\` and
    the file in `incomplete\\` are both named after, so two slots holding the
    same filename are always duplicates no matter which URL produced them.

    This used to match on (filename AND url) together, which is the duplicate
    bug: a second row appeared whenever the URL changed shape between the entry
    being created and the download finishing --
      * the slot was registered from a stray .part file, so its url was ""
      * the user resumed via option 0 and pasted a mirror / slightly different URL
      * the URL got rewritten en route (Google Drive -> uc?id=, GitHub blob -> raw)
      * the server sent a Content-Disposition filename and the download renamed itself
    In all of those the (filename, url) lookup missed, fell through, and inserted
    a brand new row alongside the one already there.  It looked self-healing on
    restart only because Config_Manager.validate() compacts and handle_orphaned_files
    prunes on load -- the config on disk was genuinely wrong until then.

    Also note: entries now land in the first FREE slot instead of being pushed in
    at slot 1 with everything shifted down.  The old shift silently overwrote
    slot 9 even when free slots existed, orphaning that file on disk, and it
    renumbered the list under the user between one menu draw and the next --
    unhelpful when the menu is driven by slot number.
    """
    try:
        if not filename:
            return False

        # Always read-modify-write against what is actually on disk.  Several
        # separately-loaded copies of this config are alive at once (interface
        # holds one, handle_download holds one, DownloadManager holds another),
        # and writing back a stale snapshot is how entries got resurrected.
        fresh = configure.Config_Manager.load()
        short_url = url if len(url) <= 60 else f"{url[:57]}..."

        # 1) Known filename -> update in place.
        for i in range(1, 10):
            if fresh.get(f"filename_{i}") == filename:
                if url:
                    fresh[f"url_{i}"] = url
                if total_size > 0:
                    fresh[f"total_size_{i}"] = total_size
                configure.Config_Manager.save(fresh)
                _sync_slots(config, fresh)
                return True

        # 2) New filename -> first free slot.
        for i in range(1, 10):
            if fresh.get(f"filename_{i}", "Empty") in ("Empty", "RESERVED"):
                fresh[f"filename_{i}"] = filename
                fresh[f"url_{i}"] = url
                if total_size <= 0:
                    temp_path = Path(TEMP_DIR) / f"{filename}.part"
                    if temp_path.exists():
                        total_size = 0  # size unknown; leave 0 rather than
                                        # recording the partial size as the total
                fresh[f"total_size_{i}"] = max(0, total_size)
                configure.Config_Manager.save(fresh)
                _sync_slots(config, fresh)
                print(f"Registered download in slot {i}: {filename} ({short_url})")
                return True

        # 3) No free slot.  Say so instead of quietly evicting slot 9.
        display_error("All 9 slots are in use. Delete an entry (D) before starting a new download.")
        time.sleep(3)
        return False

    except Exception as e:
        display_error(f"Error updating history: {e}")
        time.sleep(3)
        return False