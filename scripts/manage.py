# Script: `.\scripts\manage.py`

# Imports
import os, re, time, requests, json, random, socket, threading, sys
import gc
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError, ChunkedEncodingError
from tqdm import tqdm
from urllib3.exceptions import IncompleteRead
from .temporary import (
    URL_PATTERNS,
    CONTENT_TYPES,
    TEMP_DIR,
    RUNTIME_CONFIG,
    RETRY_STRATEGY,
    DEFAULT_HEADERS,
    FILE_STATES,
    DOWNLOADS_DIR,
    SUCCESS_MESSAGES,
    ERROR_HANDLING,
    DOWNLOAD_VALIDATION,
    HTTP_CODES,
    PLATFORM_SETTINGS,
    RETRY_OPTIONS,
    REFRESH_OPTIONS,
    DEFAULT_CHUNK_SIZES,
    SPEED_DISPLAY,
    DISPLAY_FORMATS,
    HISTORY_ENTRY,
    PERSISTENT_FILE,
    DEFAULT_CONFIG,
    BASE_DIR,
    FS_UPDATE_INTERVAL,
    DISPLAY_REFRESH,
    _pending_handlers,
    ACTIVE_DOWNLOADS
)
from . import configure  # Add this line
from .configure import Config_Manager, get_downloads_path
from .interface import display_download_state, display_download_summary, clear_screen, format_file_size, display_success, display_error, SEPARATOR_THIN
from . import temporary 

# Conditional Imports
# Keyed off temporary.IS_WINDOWS (the real host OS), NOT temporary.PLATFORM.
# PLATFORM is set from argv by launcher.py, but only *if* an argv was given --
# run `python launcher.py` with no argument on Windows and PLATFORM is still
# "None" here, `"None" != 'windows'` is True, and this module used to try
# `import termios` and blow up at import time before main() ever set the
# default. The host OS cannot change mid-run, so resolve it from the OS.
if temporary.IS_WINDOWS:
    import msvcrt
else:
    import select
    import termios
    import tty

# Classes
class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass


# ── Keyboard handling ────────────────────────────────────────────────────────
# The old inline check lived inside the chunk loop:
#
#     if msvcrt.kbhit() and msvcrt.getch().decode().lower() == 'a':
#
# Three separate problems, which together produced the reported symptom
# (mash "a" for ages, nothing happens, then the menu appears pre-filled with
# "aaaaaaaaaaaaaaaaaaaa"):
#
#  1. It only ran once per chunk.  A chunk is `chunk` bytes from persistent.json
#     -- 4 MB by default -- and iter_content blocks until the whole chunk has
#     arrived.  On a bad line that is one keyboard poll every 30+ seconds.
#  2. It consumed exactly ONE character per poll.  Every other keypress stayed
#     queued in the console input buffer, survived the return to the menu, and
#     got handed straight to the menu's input() -- that is the "aaaaa...".
#  3. .decode() on a special key (arrows send b'\xe0' + a scan code) raised
#     UnicodeDecodeError inside the download loop.
#
# Now: a daemon thread polls at 100 ms regardless of chunk size, sets
# ABORT_EVENT the instant it sees the key, prints the notice immediately, and
# swallows every remaining keystroke so nothing leaks back to the menu.  The
# download loop checks ABORT_EVENT after each chunk is written, so the chunk in
# flight still completes and is kept -- no re-downloading that data on resume.

def _stdin_is_tty() -> bool:
    """True only if we can actually read keystrokes from stdin."""
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:
        return False


def flush_input_buffer() -> None:
    """Discard anything the user typed that we have not consumed."""
    if not _stdin_is_tty():
        return
    try:
        if temporary.IS_WINDOWS:
            while msvcrt.kbhit():
                msvcrt.getch()
        else:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except Exception:
        pass


def read_key(timeout: float = 0.1) -> Optional[str]:
    """Return one lowercased keystroke, or None if nothing was typed in `timeout`."""
    try:
        if temporary.IS_WINDOWS:
            deadline = time.time() + timeout
            while time.time() < deadline:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in (b'\x00', b'\xe0'):
                        msvcrt.getch()   # special key: drop its scan code too
                        continue
                    return ch.decode('utf-8', 'ignore').lower() or None
                time.sleep(0.02)
            return None
        else:
            # Requires cbreak mode, which download_file sets up.
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if not ready:
                return None
            ch = sys.stdin.read(1)
            return ch.lower() if ch else None
    except Exception:
        return None


class KeyListener:
    """Watches for the abandon key on a background thread during a download."""

    def __init__(self, keys=('a',)):
        self.keys = {k.lower() for k in keys}
        self._stop = threading.Event()
        self.thread = None

    def start(self) -> None:
        temporary.ABORT_EVENT.clear()
        self._stop.clear()
        if not _stdin_is_tty():
            return   # nothing to listen to; downloads still run normally
        flush_input_buffer()   # ignore anything typed before the download began
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        self.thread = None
        flush_input_buffer()   # nothing reaches the menu's input()

    def _run(self) -> None:
        while not self._stop.is_set():
            key = read_key(timeout=0.1)
            if key and key in self.keys:
                temporary.ABORT_EVENT.set()
                # Immediate feedback: the display thread will repaint this on its
                # next 1s refresh, but say it now so there is zero dead air.
                print("\nStopping the active download, finishing current chunk...",
                      flush=True)
                flush_input_buffer()   # eat the repeats from key-mashing
                return

def register_handler(platform: str):
    """Decorator to collect URL handlers to be registered later."""
    def decorator(func):
        _pending_handlers.append((platform, func))
        return func
    return decorator

class URLProcessor:
    """Process URLs for downloading files using registered handlers."""
    
    _handlers = {}  # Dictionary to store platform-specific handlers

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if the URL starts with http:// or https://."""
        return url.startswith(("http://", "https://"))

    @staticmethod
    def get_remote_file_info(url: str, headers: Dict, config: Dict) -> Dict:
        """Get metadata about a remote file with timeout countdown."""
        from .interface import display_error  # Deferred import to avoid circular dependency
        timeout_length = config.get("timeout_length", 120)
        start_time = time.time()
        attempt = 0
        base_delay = 1
        max_attempts = 5
        last_update = 0
        status_line_length = 120

        def print_status(message):
            padded_message = message.ljust(status_line_length)
            print(f"\r{padded_message}", end='', flush=True)

        print_status("\nEstablishing connection...")

        try:
            while (time.time() - start_time) < timeout_length and attempt < max_attempts:
                attempt += 1
                try:
                    current_time = time.time()
                    if current_time - last_update > 1:
                        remaining = timeout_length - (time.time() - start_time)
                        status_msg = f"Establishing connection (attempt {attempt}/{max_attempts})... {remaining:.1f}s remaining"
                        print_status(status_msg)
                        last_update = current_time

                    response = requests.head(
                        url,
                        headers=headers,
                        allow_redirects=True,
                        timeout=3
                    )
                    response.raise_for_status()

                    content_length = int(response.headers.get('content-length', 0))
                    if content_length == 0:
                        get_response = requests.get(
                            url,
                            headers={**headers, "Range": "bytes=0-0"},
                            allow_redirects=True,
                            timeout=3,
                            stream=True
                        )
                        get_response.raise_for_status()
                        if 'Content-Range' in get_response.headers:
                            content_range = get_response.headers['Content-Range']
                            total_size = int(content_range.split('/')[-1])
                        else:
                            total_size = 0
                    else:
                        total_size = content_length

                    elapsed = time.time() - start_time
                    print_status(f"Connection established in {elapsed:.1f}s")
                    
                    return {
                        'size': total_size,
                        'modified': response.headers.get('last-modified'),
                        'etag': response.headers.get('etag'),
                        'content_type': response.headers.get('content-type')
                    }
                    
                except (Timeout, ConnectionError) as e:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 10)
                    status_msg = f"Connection attempt {attempt}/{max_attempts} failed. Retrying in {delay:.1f}s..."
                    print_status(status_msg)
                    time.sleep(delay)
                    continue
                    
            print_status(f"Connection timed out after {timeout_length}s")
            raise Timeout(f"Connection timed out after {timeout_length}s")
            
        except Exception as e:
            display_error(f"Remote info error: {str(e)}")
            time.sleep(3)
            return {}

    @staticmethod
    def compare_files(local_path: Path, remote_info: Dict) -> str:
        """Compare local and remote file sizes."""
        if not local_path.exists():
            # Was DOWNLOAD_VALIDATION["new"] -- that key does not exist in the
            # dict (it only has size_mismatch/incomplete/complete/unknown), so
            # this raised KeyError. Unreached today; correct it rather than
            # leave the landmine.
            return DOWNLOAD_VALIDATION["unknown"]

        local_size = local_path.stat().st_size
        if local_size == remote_info.get('size', 0):
            return DOWNLOAD_VALIDATION["complete"]
        elif local_size < remote_info.get('size', 0):
            return DOWNLOAD_VALIDATION["incomplete"]
        return DOWNLOAD_VALIDATION["size_mismatch"]

    @staticmethod
    @register_handler("google_drive")
    def process_google_drive_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process Google Drive URLs for downloading."""
        file_id_match = re.search(r"/d/([-\w]+)", url)
        if file_id_match:
            file_id = file_id_match.group(1)
            download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            session = requests.Session()
            response = session.get(download_url, stream=True)
            if "confirm=" in response.url:
                confirm_param = re.search(r"confirm=([^&]+)", response.url).group(1)
                download_url += f"&confirm={confirm_param}"

            remote_info = URLProcessor.get_remote_file_info(download_url, DEFAULT_HEADERS.copy(), config)
            return download_url, remote_info
        raise DownloadError("Invalid Google Drive URL format")

    @register_handler("github")
    def process_github_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Convert GitHub blob URLs to raw format"""
        if '/blob/' in url:
            url = url.replace('/blob/', '/raw/')
        remote_info = URLProcessor.get_remote_file_info(url, DEFAULT_HEADERS.copy(), config)
        return url, remote_info    

    @staticmethod
    def process_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process URLs using registered handlers."""
        for platform, pattern in URL_PATTERNS.items():
            if not re.search(pattern["pattern"], url):
                continue

            handler = URLProcessor._handlers.get(platform)
            if handler:
                return handler(url, config)

        # Handle as direct download if no platform matches
        remote_info = URLProcessor.get_remote_file_info(url, DEFAULT_HEADERS.copy(), config)
        return url, remote_info

for platform, func in _pending_handlers:
    URLProcessor._handlers[platform] = func

# Functions
def calculate_retry_delay(retries: int) -> float:
    """Calculate retry delay based on retry strategy."""
    return min(
        RETRY_STRATEGY["initial_delay"] * (RETRY_STRATEGY["backoff_factor"] ** retries),
        RETRY_STRATEGY["max_delay"]
    )



def get_download_headers(existing_size: int = 0) -> Dict:
    """Generate HTTP headers for download requests."""
    headers = DEFAULT_HEADERS.copy()
    if existing_size:
        headers["Range"] = f"bytes={existing_size}-"
    return headers

def extract_filename_from_disposition(disposition: str) -> Optional[str]:
    """Extract filename from Content-Disposition header."""
    try:
        if not disposition:
            return None

        # Check for filename* with RFC 5987 encoding first
        filename_match = re.search(r"filename\*?=utf-8''([^;]+)", disposition, re.IGNORECASE)
        if filename_match:
            return unquote(filename_match.group(1)).strip('"')

        # Fallback to filename=
        filename_match = re.search(r'filename="([^"]+)"', disposition)
        if not filename_match:
            filename_match = re.search(r"filename=([^;]+)", disposition)
        if filename_match:
            return unquote(filename_match.group(1).strip('"'))

        return None

    except Exception as e:
        display_error(f"Filename extraction error: {str(e)}")
        time.sleep(3)
        return None

# Download handling
def handle_download(url: str, config: dict, batch_index: Optional[int] = None, batch_total: Optional[int] = None) -> Tuple[bool, str]:
    from .configure import Config_Manager, get_downloads_path
    from .interface import (display_error, display_success, handle_error, get_user_choice_after_error,
                            display_download_state, display_download_summary, clear_screen,
                            format_file_size, update_history, display_download_prompt)
    try:
        processor = URLProcessor()
        try:
            download_url, metadata = processor.process_url(url, config)
        except DownloadError as e:
            display_error(str(e))
            time.sleep(3)
            return False, str(e)

        filename = metadata.get("filename") or get_file_name_from_url(download_url)
        if not filename:
            display_error("Unable to extract filename from the URL.")
            time.sleep(3)
            return False, "Unable to extract filename from the URL."

        # Pre-register so the slot survives a failure and can be retried from the
        # menu.  update_history now reports whether it actually got a slot.
        if not update_history(config, filename, url, metadata.get('size', 0)):
            return False, "No free slot available for this download."

        downloads_path = get_downloads_path(config)
        dm = DownloadManager(downloads_path)
        chunk_size = config.get("chunk", 4096000)

        out_path = downloads_path / filename
        # `url`, not `download_url`.  download_file runs process_url again itself,
        # so passing the already-processed URL meant processing it twice -- two
        # HEAD round-trips per download, and outright breakage for Google Drive:
        # process_google_drive_url matches on `/d/<id>`, so feeding it the
        # `uc?id=...&export=download` URL it had just produced raised
        # "Invalid Google Drive URL format". Passing the original also keeps the
        # user's URL (not a rewritten CDN one) as the URL saved for resuming.
        # For HuggingFace and plain direct links url == download_url, so this
        # path is byte-for-byte identical to before.
        success, error = dm.download_file(url, out_path, chunk_size,
                                          batch_index=batch_index, batch_total=batch_total)

        if success:
            return True, ""
        elif error in ("Download saved for later", "Download stopped by user"):
            # Abandoning is a deliberate user action, not a failure.  It used to
            # surface as "Error: Download failed: Download saved for later", and
            # then get re-printed by the caller as an error on top of that.
            display_success("Download stopped and saved. Select its slot to resume.")
            time.sleep(2)
            return False, ""
        else:
            display_error(f"Download failed: {error}")
            time.sleep(3)
            return False, f"Download failed: {error}"

    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        time.sleep(3)
        choice = get_user_choice_after_error()
        if choice == 'r':
            return handle_download(url, config, batch_index=batch_index, batch_total=batch_total)
        elif choice == '0':
            new_url = display_download_prompt()
            if new_url and new_url.lower() == 'b':
                return False, "User cancelled"
            return handle_download(new_url, config) if new_url else (False, "No URL provided")
        else:
            return False, "Invalid choice"

def handle_multiple_downloads(urls: list, config: dict) -> int:
    """Handle batch downloads sequentially"""
    from .manage import handle_download
    from .interface import display_error
    
    success_count = 0
    total = len(urls)
    for idx, url in enumerate(urls, 1):
        print(f"\rProcessing download {idx}/{total}", end="", flush=True)
        success, error_msg = handle_download(url, config, batch_index=idx, batch_total=total)
        if success:
            success_count += 1
            display_download_state(get_active_downloads())
        else:
            display_error(error_msg)
            time.sleep(3)
            return success_count  # Exit early on failure or abandonment
    return success_count

# NOTE: a second, module-level copy of get_remote_file_info used to live here,
# decorated with a bare @staticmethod at module scope. It was never called, and
# it could not be: on Python < 3.10 a staticmethod object is not callable
# outside a class body, so any call would have raised TypeError. The live
# implementation is URLProcessor.get_remote_file_info above.

def get_file_name_from_url(url: str) -> Optional[str]:
    """Extract filename from URL or headers."""
    from .interface import display_error  # Deferred import to avoid circular dependency
    try:
        # First try to extract filename from URL path
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        if filename and '.' in filename:
            return filename

        # If not found in URL, try from Content-Disposition header
        response = requests.head(url, allow_redirects=True, timeout=5)
        if 'Content-Disposition' not in response.headers:
            return filename if filename else None

        disposition = response.headers['Content-Disposition']
        return extract_filename_from_disposition(disposition) or filename

    except Exception as e:
        display_error(f"Error extracting filename from URL: {str(e)}")
        time.sleep(3)
        return None

# Helper: resolve open-mode and corrected total_size from actual HTTP response
def _resolve_response_mode(
    response: "requests.Response",
    requested_offset: int,
    total_size: int,
    temp_path: Path
) -> Tuple[str, int, int]:
    """
    Decide how to open the .part file and what the true total_size is,
    based on the server's actual response status code.

    Returns (file_mode, effective_existing_size, corrected_total_size, resume_status).

    resume_status is a human-readable string: "Available", "Unavailable", or "N/A".

    The critical case: we sent  Range: bytes=N-  but the server replied 200.
    That means it is sending the *whole* file again and does not support
    partial-content resumption.  We must:
      - truncate / delete the stale .part file
      - reset effective_existing_size to 0
      - open in 'wb' (write) mode so nothing is double-appended
    """
    status = response.status_code

    if requested_offset > 0:
        if status == 206:
            # Server honoured the Range request — safe to append.
            # Get the authoritative total from Content-Range: bytes X-Y/Z
            content_range = response.headers.get('Content-Range', '')
            if '/' in content_range:
                try:
                    total_str = content_range.rsplit('/', 1)[-1]
                    if total_str != '*':
                        total_size = int(total_str)
                except (ValueError, IndexError):
                    pass
            return 'ab', requested_offset, total_size, "Available"

        elif status == 200:
            # Server ignored the Range header and is sending the full file.
            # Appending would corrupt the output — start fresh.
            print(
                f"\n[Resume] Server returned 200 (range not supported). "
                f"Discarding existing partial file and restarting..."
            )
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except OSError as exc:
                display_error(f"Could not remove stale .part file: {exc}")
            # Update total_size from Content-Length if available
            cl = int(response.headers.get('content-length', 0))
            if cl > 0:
                total_size = cl
            return 'wb', 0, total_size, "Unavailable"

        else:
            # Unexpected status — let raise_for_status() handle it upstream.
            return 'ab', requested_offset, total_size, "Unknown"

    else:
        # Fresh download — always write mode.
        # Grab Content-Length from the actual GET response (more reliable
        # than the earlier HEAD for CDN-redirected URLs like SourceForge).
        cl = int(response.headers.get('content-length', 0))
        if cl > 0:
            total_size = cl
        return 'wb', 0, total_size, "N/A"


# Get Active Downloads (keep above DownloadManager)
def get_active_downloads() -> list:
    """Get sanitized list of active downloads with calculated metrics and batch info"""
    return [{
        'filename': d.get('filename', 'Unknown'),
        'current': d.get('current', 0),
        'total': d.get('total', 1),
        'speed': d.get('speed', 0),
        'elapsed': time.time() - d.get('start_time', time.time()),
        'remaining': (d.get('total', 1) - d.get('current', 0)) / d['speed'] if d.get('speed', 0) > 0 else 0,
        'batch_index': d.get('batch_index'),
        'batch_total': d.get('batch_total'),
        'resume_status': d.get('resume_status', 'Pending')
    } for d in ACTIVE_DOWNLOADS if 'current' in d]

# DownloadManager (keep below the above functions)
class DownloadManager:
    def __init__(self, downloads_location: Path):
        from .configure import Config_Manager
        self.config = Config_Manager.load()
        self.downloads_location = downloads_location
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self._register_existing_temp_files()
        self.display_thread = None
        self.display_refresh_active = False  # Added control flag

    def _start_display_updater(self):
        """Start display refresh thread with control flag"""
        self.display_refresh_active = True
        self.display_thread = threading.Thread(
            target=self._update_display_loop,
            args=(DISPLAY_REFRESH,),
            daemon=True
        )
        self.display_thread.start()

    def _update_display_loop(self, refresh_rate=1):
        """Controlled display updater"""
        while self.display_refresh_active:
            active = get_active_downloads()
            if active:
                display_download_state(active)
            time.sleep(refresh_rate)

    def _stop_display_updater(self):
        """Gracefully stop display updates"""
        self.display_refresh_active = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1)

    def _check_existing_download(self, url: str, filename: str) -> Tuple[bool, Optional[Path], Dict]:
        """Check if a download already exists, either complete or partial."""
        downloads_dir = self.downloads_location
        file_path = downloads_dir / filename

        for i in range(1, 10):
            if (self.config[f"url_{i}"] == url and
                self.config[f"filename_{i}"] == filename):
                if file_path.exists():
                    return True, file_path, {'index': i}
                self._remove_from_persistent(i)
                break

        temp_path = TEMP_DIR / f"{filename}.part"
        if temp_path.exists():
            return True, temp_path, {'has_temp': True, 'temp_path': temp_path}

        if file_path.exists():
            return True, file_path, {}

        return False, None, {}

    def _register_existing_temp_files(self):
        """Register any .part files in temp directory."""
        for temp_file in TEMP_DIR.glob("*.part"):
            filename = temp_file.stem
            if not any(self.config.get(f"filename_{i}") == filename for i in range(1, 10)):
                # total_size 0, not the .part's current size.  Passing the partial
                # size as the total made the menu render an unfinished file as
                # "100%" (progress = temp_size / total_size).  0 means unknown,
                # which the menu already renders as "<size>/Unknown".
                self._register_file_entry(filename, "", 0)
                print(f"Registered temporary file: {temp_file.name}")

    def _remove_from_persistent(self, index: int) -> None:
        """Remove an entry from the persistent configuration."""
        from .configure import Config_Manager
        for i in range(index, 9):
            self.config[f"filename_{i}"] = self.config[f"filename_{i+1}"]
            self.config[f"url_{i}"] = self.config[f"url_{i+1}"]
            self.config[f"total_size_{i}"] = self.config[f"total_size_{i+1}"]

        self.config["filename_9"] = "Empty"
        self.config["url_9"] = ""
        self.config["total_size_9"] = 0
        Config_Manager.save(self.config)

    def _register_file_entry(self, filename: str, url: str, total_size: int) -> None:
        """Register/refresh a file entry.

        Delegates to update_history so there is exactly ONE place that decides
        what a duplicate is.  This used to hand-roll its own slot search against
        self.config -- a snapshot loaded back in __init__ and never refreshed --
        so it happily wrote a stale view of the slot list back over a newer one.
        """
        from .interface import update_history
        update_history(self.config, filename, url, total_size)

    def _register_early_metadata(self, filename: str, url: str, total_size: int) -> None:
        """Register download metadata immediately after verifying total size."""
        from .configure import Config_Manager
        try:
            for i in range(1, 10):
                if self.config[f"filename_{i}"] in ["Empty", filename]:
                    self.config[f"filename_{i}"] = filename
                    self.config[f"url_{i}"] = url
                    self.config[f"total_size_{i}"] = total_size if total_size > 0 else 0
                    Config_Manager.save(self.config)
                    size_display = format_file_size(total_size) if total_size > 0 else 'Unknown'
                    print(f"Registered early metadata for: {filename} (Size: {size_display})")
                    print("Setting up download...")
                    break
            if total_size <= 0:
                display_error("Could not determine file size from server. Proceeding with unknown size.")
        except Exception as e:
            display_error(f"Error registering early metadata: {str(e)}")
            time.sleep(3)

    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """Handle rate limiting with exponential backoff."""
        if response.status_code != 429:
            return False

        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                delay = int(retry_after)
            except ValueError:
                try:
                    retry_date = datetime.strptime(retry_after, '%a, %d %b %Y %H:%M:%S %Z')
                    delay = (retry_date - datetime.utcnow()).total_seconds()
                except ValueError:
                    delay = RETRY_STRATEGY["initial_delay"]
        else:
            delay = RETRY_STRATEGY["initial_delay"]

        display_error(f"Rate limited. Waiting {delay} seconds before retry")
        time.sleep(max(1, delay))
        return True

    def download_file(self, remote_url: str, out_path: Path, chunk_size: int, batch_mode: bool = False, 
                     batch_index: Optional[int] = None, batch_total: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """Download a file from a remote URL with progress tracking and resumption support."""
        from .interface import display_error, display_success, update_history, format_file_size, display_download_summary
        start_time = time.time()
        temp_path = None
        filename = None
        tracking_data = None
        total_size = 0
        batch_mode = batch_index is not None and batch_total is not None

        # The URL as the user knows it -- this is what gets saved for resuming,
        # never the rewritten/CDN form.
        source_url = remote_url

        # Retries come from persistent.json (the "Maximum Retries" setup option),
        # falling back to the runtime default.  The setup menu cycles this through
        # 100/200/400/800 and it was being ignored entirely: the loop below read
        # RUNTIME_CONFIG["download"]["max_retries"], a hard-coded 10.
        max_retries = int(self.config.get("retries", RUNTIME_CONFIG["download"]["max_retries"]) or 10)

        # Terminal setup for non-Windows platforms.
        # Guarded: termios.tcgetattr() raises if stdin is not a real terminal, so
        # piping anything into launcher.py, or running it from a service/cron with
        # stdin redirected, used to kill every download at this line before a byte
        # was fetched.  Without a tty there is simply no key to listen for.
        old_term = None
        fd = None
        if not temporary.IS_WINDOWS and _stdin_is_tty():
            try:
                fd = sys.stdin.fileno()
                old_term = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            except Exception:
                old_term = None
                fd = None

        # Watch for the abandon key on its own thread; see KeyListener above.
        key_listener = KeyListener(keys=('a',))
        key_listener.start()

        try:
            retries = 0
            no_resume = False  # Set True once server confirms it won't honour Range requests.
                               # Persists across retries so we stop sending Range headers
                               # and stop treating the stale partial as resumable data.

            while retries < max_retries:
                try:
                    if temporary.ABORT_EVENT.is_set():
                        return False, "Download stopped by user"

                    # Get file metadata
                    print(f"Retrieving file metadata (attempt {retries + 1}): ", end='', flush=True)
                    # self.config, not RUNTIME_CONFIG: get_remote_file_info reads
                    # config["timeout_length"], and RUNTIME_CONFIG has no such key,
                    # so the user's configured timeout was silently replaced by the
                    # 120s default on every single request.
                    download_url, metadata = URLProcessor.process_url(remote_url, self.config)
                    total_size = metadata.get('size', 0)
                    print("Done")

                    filename = metadata.get("filename") or get_file_name_from_url(download_url)
                    if not filename:
                        return False, ERROR_HANDLING["messages"]["filename_error"]

                    temp_path = TEMP_DIR / f"{filename}.part"

                    # If the server is known to not support resume, any .part file that
                    # exists is leftover from a previous interrupted fresh download and
                    # contains data from offset 0 — not a resumable partial.  Delete it
                    # now so we start clean, and send no Range header.
                    if no_resume:
                        if temp_path.exists():
                            try:
                                temp_path.unlink()
                            except OSError:
                                pass
                        existing_size = 0
                    else:
                        existing_size = temp_path.stat().st_size if temp_path.exists() else 0

                    # Check for existing tracking data
                    tracking_data = next((d for d in ACTIVE_DOWNLOADS if d['filename'] == out_path.name), None)
                    if not tracking_data:
                        tracking_data = {
                            'filename': out_path.name,
                            'url': remote_url,
                            'status': 'connecting',
                            'current': existing_size,
                            'total': total_size,
                            'speed': 0.0,
                            'elapsed': time.time() - start_time,
                            'remaining': 0.0,
                            'start_time': start_time
                        }
                        if batch_mode:
                            tracking_data['batch_index'] = batch_index
                            tracking_data['batch_total'] = batch_total
                        ACTIVE_DOWNLOADS.append(tracking_data)
                    else:
                        tracking_data.update({
                            'current': existing_size,
                            'total': total_size,
                            'status': 'restarting' if no_resume and retries > 0 else 'connecting',
                            'start_time': start_time
                        })
                        if batch_mode:
                            tracking_data['batch_index'] = batch_index
                            tracking_data['batch_total'] = batch_total

                    # Start display thread if needed
                    if not self.display_thread or not self.display_thread.is_alive():
                        self._start_display_updater()

                    # Begin download
                    with requests.Session() as session:
                        adapter = requests.adapters.HTTPAdapter(max_retries=5)
                        session.mount('https://', adapter)
                        session.mount('http://', adapter)

                        with session.get(
                            download_url,
                            stream=True,
                            headers=get_download_headers(existing_size),
                            timeout=RUNTIME_CONFIG["download"]["timeout"],
                            verify=False
                        ) as response:
                            response.raise_for_status()

                            # ── Critical: honour (or detect lack of) range support ──
                            # _resolve_response_mode checks whether the server actually
                            # returned 206 Partial Content.  If it returned 200, it is
                            # sending the whole file and we must NOT append — that is
                            # what caused the 151% progress bug on SourceForge CDN URLs.
                            file_mode, existing_size, total_size, resume_status = _resolve_response_mode(
                                response, existing_size, total_size, temp_path
                            )

                            # Persist the no-resume determination for the lifetime of this
                            # download.  Once the server has demonstrated it ignores Range,
                            # every subsequent retry must start fresh with no Range header.
                            if resume_status == "Unavailable":
                                no_resume = True

                            # Check Content-Disposition for a server-provided filename
                            # (important for CDN-redirected URLs that change the path)
                            cd_header = response.headers.get('Content-Disposition', '')
                            if cd_header:
                                cd_filename = extract_filename_from_disposition(cd_header)
                                if cd_filename and cd_filename != filename:
                                    new_temp = TEMP_DIR / f"{cd_filename}.part"
                                    if temp_path.exists() and not new_temp.exists():
                                        try:
                                            temp_path.rename(new_temp)
                                        except OSError:
                                            pass
                                        else:
                                            temp_path = new_temp
                                    filename = cd_filename
                                    out_path = out_path.parent / filename

                            # Snapshot before the loop so speed/summary math is correct.
                            # (existing_size is updated each chunk inside the loop, so we
                            # must capture the pre-loop value here.)
                            pre_loop_existing_size = existing_size

                            # Propagate corrected total_size and resume_status to the tracking dict
                            tracking_data.update({'total': total_size, 'resume_status': resume_status})

                            # Download loop
                            with open(temp_path, file_mode) as out_file:
                                for chunk in response.iter_content(chunk_size=chunk_size):
                                    if not chunk:
                                        continue

                                    # Process chunk
                                    out_file.write(chunk)
                                    out_file.flush()
                                    os.fsync(out_file.fileno())
                                    written_size = out_file.tell()
                                    now = time.time()
                                    elapsed_chunk = now - tracking_data.get('last_chunk_time', now)
                                    tracking_data.update({
                                        'current': written_size,
                                        'total': total_size,
                                        'status': 'downloading',
                                        'speed': len(chunk) / elapsed_chunk if elapsed_chunk > 0 else 0,
                                        'last_chunk_time': now
                                    })
                                    existing_size = written_size

                                    # Abandon check AFTER the write+fsync: the
                                    # chunk that was in flight when "A" was pressed
                                    # is completed and kept, so resuming does not
                                    # re-fetch it.  KeyListener has already set this
                                    # (and printed the notice) the moment the key was
                                    # pressed -- all that is waited on here is the
                                    # current chunk finishing, not a poll.
                                    if temporary.ABORT_EVENT.is_set():
                                        self._register_file_entry(filename, source_url, total_size)
                                        return False, "Download saved for later"

                            # ── Post-download size verification ──
                            # Note: this block only runs when iter_content exits cleanly
                            # (no exception).  The ChunkedEncodingError path above handles
                            # the case where the connection drops mid-stream or after the
                            # last byte (missing terminating chunk).
                            actual_temp_size = temp_path.stat().st_size if temp_path.exists() else 0
                            if total_size > 0 and actual_temp_size != total_size:
                                size_diff = actual_temp_size - total_size
                                if size_diff < 0:
                                    # Loop ended cleanly but server sent fewer bytes than
                                    # Content-Length promised.  Retry.
                                    missing = format_file_size(total_size - actual_temp_size)
                                    print(f"\n[Incomplete] Got {format_file_size(actual_temp_size)} of {format_file_size(total_size)} — {missing} missing. Retrying...")
                                    raise IncompleteRead(b'', total_size - actual_temp_size)
                                else:
                                    # Received slightly more than expected — can happen
                                    # with some CDN edge caches.  Warn but proceed.
                                    display_error(
                                        f"Warning: received {format_file_size(actual_temp_size)} "
                                        f"but expected {format_file_size(total_size)}. "
                                        f"Proceeding — file may still be valid."
                                    )

                            # Verify and move completed file
                            if not move_with_retry(temp_path, out_path):
                                return False, "Failed to move downloaded file"

                            # Stop display updates
                            self._stop_display_updater()

                            final_size = out_path.stat().st_size
                            bytes_this_session = final_size - pre_loop_existing_size
                            elapsed_total = time.time() - start_time
                            avg_speed = bytes_this_session / elapsed_total if elapsed_total > 0 else 0

                            # Show summary
                            display_download_summary(
                                filename=filename,
                                total_size=final_size,
                                average_speed=avg_speed,
                                elapsed=elapsed_total,
                                timestamp=datetime.now(),
                                destination=str(out_path),
                                batch_mode=batch_mode
                            )

                            update_history(self.config, filename, source_url, final_size)
                            return True, None

                except (ConnectionError, ChunkedEncodingError, IncompleteRead) as e:
                    # ── SourceForge / chunked-CDN completion check ──────────────────
                    # These CDNs use Transfer-Encoding: chunked but drop the TCP
                    # connection without sending the final zero-length terminating
                    # chunk (0\r\n\r\n).  requests raises ChunkedEncodingError even
                    # though EVERY content byte has already been written to disk.
                    # Detect this by comparing .part size to the known total_size.
                    # If they match, the download is actually complete — finalize it
                    # instead of restarting the whole thing from scratch.
                    if (total_size > 0
                            and temp_path is not None
                            and temp_path.exists()
                            and temp_path.stat().st_size >= total_size):
                        print(
                            f"\n[Complete] Received all {format_file_size(total_size)} despite "
                            f"connection drop (missing terminating chunk) — finalizing..."
                        )
                        if not move_with_retry(temp_path, out_path):
                            return False, "Failed to move downloaded file"
                        self._stop_display_updater()
                        final_size = out_path.stat().st_size
                        elapsed_total = time.time() - start_time
                        # Use total bytes received this session for speed calculation.
                        # pre_loop_existing_size may be 0 on a no_resume restart, which
                        # is correct — we re-downloaded from byte 0.
                        session_bytes = final_size - (pre_loop_existing_size if 'pre_loop_existing_size' in dir() else 0)
                        avg_speed = session_bytes / elapsed_total if elapsed_total > 0 else 0
                        display_download_summary(
                            filename=filename,
                            total_size=final_size,
                            average_speed=avg_speed,
                            elapsed=elapsed_total,
                            timestamp=datetime.now(),
                            destination=str(out_path),
                            batch_mode=batch_mode
                        )
                        update_history(self.config, filename, source_url, final_size)
                        return True, None
                    # ── end completion check ─────────────────────────────────────────

                    # Network-level failures: connection reset, TCP drop, truncated body.
                    # These are retryable — but only if we handle the no_resume case.
                    retries += 1
                    err_type = type(e).__name__
                    if no_resume:
                        # Server won't resume, so any partial data written in this
                        # iteration is from a fresh download that got cut off — useless.
                        # Delete it so the next iteration starts with a clean slate.
                        if temp_path is not None and temp_path.exists():
                            try:
                                temp_path.unlink()
                            except OSError:
                                pass
                        print(f"\n[Retry {retries}] {err_type}: server does not support resume — restarting from 0...")
                    else:
                        written = temp_path.stat().st_size if (temp_path is not None and temp_path.exists()) else 0
                        print(f"\n[Retry {retries}] {err_type}: will resume from {format_file_size(written)}...")
                    if retries >= RUNTIME_CONFIG["download"]["max_retries"]:
                        raise
                    time.sleep(min(2 ** retries, 30))

                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        raise
                    time.sleep(min(2 ** retries, 10))

            # Reachable now that the loop has a real exit condition.  The old
            # condition was `while pre_registration_attempts < max_pre_attempts
            # or retries < ...` and pre_registration_attempts was never
            # incremented, so the left side was permanently True and the loop
            # could only ever be left by an exception.
            return False, f"Download failed after {max_retries} attempts"

        except Exception as e:
            display_error(f"Unexpected error: {str(e)}")
            return False, str(e)

        finally:
            # Clean up
            key_listener.stop()
            self._stop_display_updater()
            if tracking_data and tracking_data in ACTIVE_DOWNLOADS:
                ACTIVE_DOWNLOADS.remove(tracking_data)

            # Restore terminal settings on non-Windows platforms
            if not temporary.IS_WINDOWS and old_term is not None and fd is not None:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_term)

            if 'gc' in locals() or 'gc' in globals():
                gc.collect()
                
def handle_orphaned_files(config: dict) -> None:
    from .temporary import BASE_DIR          # was `from scripts.temporary import ...`
                                             # -- an absolute import from inside the
                                             # package, which only resolves because
                                             # launcher.py happens to sit in BASE_DIR.
    from .configure import Config_Manager

    registered_files = set()
    # Collect registered filenames
    for i in range(1, 10):
        filename = config.get(f"filename_{i}", "Empty")
        if filename != "Empty":
            registered_files.add(filename)
            registered_files.add(f"{filename}.part")

    downloads_path = get_downloads_path(config)

    # Sweep ONLY `incomplete\`, and only .part files.
    #
    # This used to loop over [downloads_path, TEMP_DIR] and unlink anything not
    # in the slot list.  downloads_location is user-settable from the Setup menu,
    # so pointing it at a real folder (say C:\Users\me\Downloads, or ~/Downloads)
    # meant that on the next launch -- handle_orphaned_files runs unconditionally
    # from initialize_startup -- DownLord silently deleted every unrelated file in
    # it.  The stated behaviour is "auto-remove items from its LIST when manually
    # moved from the downloads folder", i.e. drop the entry, which is what the
    # loop below does.  Deleting the user's files was never part of that.
    #
    # incomplete\ is DownLord's own scratch space, so an unregistered .part there
    # really is garbage and is still cleared.
    for file in TEMP_DIR.glob("*.part"):
        if file.name in registered_files or file.stem in registered_files:
            continue
        try:
            file.unlink()
            print(f"Removed orphaned partial: {file.name}")
        except Exception as e:
            display_error(f"Error removing file {file}: {str(e)}")
            time.sleep(3)

    
    # Check each config entry and remove if the file is missing.
    # This is the "auto-removing items from its list" behaviour: the file was
    # moved out of downloads\ or deleted, so the slot is released.
    for i in range(1, 10):
        filename = config.get(f"filename_{i}", "Empty")
        if filename == "Empty":
            continue

        # Check if the file exists in downloads or as .part in temp
        file_path = downloads_path / filename
        temp_path = TEMP_DIR / f"{filename}.part"
        
        if not file_path.exists() and not temp_path.exists():
            # Clear the entry
            config[f"filename_{i}"] = "Empty"
            config[f"url_{i}"] = ""
            config[f"total_size_{i}"] = 0
            print(f"Removed missing file entry: {filename}")
    
    # Save the updated config
    Config_Manager.save(config)

def cleanup_temp_files() -> None:
    """
    Clean temporary download files.
    """
    temp_dir = Path(TEMP_DIR)
    if temp_dir.exists():
        for file in temp_dir.glob("*.part"):
            try:
                file.unlink()
                print(f"Removed temporary file: {file.name}")
            except Exception as e:
                display_error(f"Error removing temporary file {file}: {e}")
                time.sleep(3)


def verify_download_directory() -> bool:
    """Verify download directory exists and is writable."""
    try:
        downloads_dir = Path(DOWNLOADS_DIR)
        downloads_dir.mkdir(parents=True, exist_ok=True)
        test_file = downloads_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception as e:
        display_error(f"Download directory verification failed: {e}")
        return False


def move_with_retry(src: Path, dst: Path, max_retries: int = 10, delay: float = 2.0) -> bool:
    """Cross-platform file move with retry logic"""
    for attempt in range(max_retries):
        try:
            if not src.exists():
                display_error(f"Source file missing: {src}")
                return False

            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # Use replace() which works cross-platform
            src.replace(dst)
            return True
            
        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"Move attempt {attempt+1} failed, retrying in {delay}s...")
                time.sleep(delay)
            else:
                display_error(f"Failed after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            display_error(f"Unexpected error: {e}")
            return False
    return False