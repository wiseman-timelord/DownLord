# Script: `.\scripts\manage.py`

# Imports
import os, cgi, re, time, requests, json, random, socket, msvcrt
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
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
    BASE_DIR
)

_pending_handlers = []

# Constants
FS_UPDATE_INTERVAL = 5  # File system updates every 5 seconds
DISPLAY_REFRESH = 1     # Visual refresh every 1 second

# Classes
class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

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
            return DOWNLOAD_VALIDATION["new"]

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

def handle_download(url: str, config: dict) -> bool:
    from .configure import ConfigManager, get_downloads_path # Already deferred or kept as needed
    from .interface import (
        display_error,
        display_success,
        display_download_state,
        display_download_summary,
        update_history,
        clear_screen,
        format_file_size  # Added this
    )
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
        ConfigManager.save(config)  # Now accessible

        downloads_path = get_downloads_path(config)  # Now accessible
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

@staticmethod
def get_remote_file_info(url: str, headers: Dict, config: Dict) -> Dict:
    from .interface import display_error # Deferred import
    timeout_length = config.get("timeout_length", 120)
    start_time = time.time()
    attempt = 0
    base_delay = 1
    max_attempts = 5
    last_update = 0
    status_line_length = 120  # Match your separator width

    def print_status(message):
        # Pad the message with spaces to clear the line
        padded_message = message.ljust(status_line_length)
        print(f"\r{padded_message}", end='', flush=True)

    print_status("Establishing connection...")

    try:
        while (time.time() - start_time) < timeout_length and attempt < max_attempts:
            attempt += 1
            try:
                # Update status every second
                current_time = time.time()
                if current_time - last_update > 1:
                    remaining = timeout_length - (time.time() - start_time)
                    status_msg = f"Establishing connection (attempt {attempt}/{max_attempts})... {remaining:.1f}s remaining"
                    print_status(status_msg)
                    last_update = current_time

                # Attempt HEAD request first
                response = requests.head(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    timeout=3
                )
                response.raise_for_status()

                # Check if Content-Length is present
                content_length = int(response.headers.get('content-length', 0))
                if content_length == 0:
                    # Fallback to GET request with Range to get Content-Range
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
                print_status(f"Connection established in {elapsed:.1f}s")  # Success message
                
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
                
        # Timeout reached
        print_status(f"Connection timed out after {timeout_length}s")
        raise Timeout(f"Connection timed out after {timeout_length}s")
        
    except Exception as e:
        display_error(f"Remote info error: {str(e)}")
        time.sleep(3)
        return {}


class DownloadManager:
    def __init__(self, downloads_location: Path):
        from .configure import ConfigManager  # Deferred import
        self.config = ConfigManager.load()  # Now accessible
        self.downloads_location = downloads_location
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self._register_existing_temp_files()

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
        """
        Register any .part files in temp directory.
        """
        for temp_file in TEMP_DIR.glob("*.part"):
            filename = temp_file.stem
            if not any(self.config[f"filename_{i}"] == filename for i in range(1, 10)):
                self._register_file_entry(filename, "", temp_file.stat().st_size)
                print(f"Registered temporary file: {temp_file.name}")

    def _remove_from_persistent(self, index: int) -> None:
        """Remove an entry from the persistent configuration."""
        from .configure import ConfigManager  # Deferred import
        for i in range(index, 9):
            self.config[f"filename_{i}"] = self.config[f"filename_{i+1}"]
            self.config[f"url_{i}"] = self.config[f"url_{i+1}"]
            self.config[f"total_size_{i}"] = self.config[f"total_size_{i+1}"]

        self.config["filename_9"] = "Empty"
        self.config["url_9"] = ""
        self.config["total_size_9"] = 0
        ConfigManager.save(self.config)  

    def _register_file_entry(self, filename: str, url: str, total_size: int) -> None:
        """Register a file entry in the first available slot."""
        from .configure import ConfigManager  # Deferred import
        for i in range(1, 10):
            if self.config[f"filename_{i}"] in ["Empty", filename]:
                self.config[f"filename_{i}"] = filename
                self.config[f"url_{i}"] = url
                self.config[f"total_size_{i}"] = total_size
                ConfigManager.save(self.config)  # Now accessible
                break

    def _register_early_metadata(self, filename: str, url: str, total_size: int) -> None:
        """
        Register download metadata immediately after verifying total size.
        """
        from .configure import ConfigManager  # Deferred import
        try:
            for i in range(1, 10):
                if self.config[f"filename_{i}"] in ["Empty", filename]:
                    self.config[f"filename_{i}"] = filename
                    self.config[f"url_{i}"] = url
                    self.config[f"total_size_{i}"] = total_size if total_size > 0 else "Unknown"
                    ConfigManager.save(self.config)  # Now accessible
                    print(f"Registered early metadata for: {filename} (Size: {total_size if total_size > 0 else 'Unknown'})")
                    print("Setting up download...")
                    break

            # If total_size is unknown, retry registration after a delay
            if total_size <= 0:
                display_error("Could not determine file size from server. Registration delayed.")
                time.sleep(2)
                if total_size > 0:  # Re-check size after delay
                    self._register_early_metadata(filename, url, total_size)
                else:
                    display_error("Failed to register metadata due to unknown file size.")
        except Exception as e:
            display_error(f"Error registering early metadata: {str(e)}")
            time.sleep(3)

    def cleanup_unregistered_files(self) -> None:
        """Remove files not registered in persistent.json."""
        try:
            registered_files = set()
            for i in range(1, 10):
                filename = self.config[f"filename_{i}"]
                if filename != "Empty":
                    registered_files.add(filename)
                    registered_files.add(f"{filename}.part")

            for folder in [DOWNLOADS_DIR, TEMP_DIR]:
                for file_path in folder.glob("*"):
                    if file_path.name not in registered_files and not any(
                        self.config.get(f"filename_{i}") == file.name for i in range(1, 10)
                    ):
                        try:
                            file_path.unlink()
                            print(f"Removed unregistered file: {file_path}")
                        except Exception as e:
                            display_error(f"Error removing file {file_path}: {str(e)}")
                            time.sleep(3)
        except Exception as e:
            display_error(f"Error in cleanup_unregistered_files: {str(e)}")

    def _cleanup_temp_files(self, filename: str) -> None:
        """
        Clean up temporary download files.
        """
        try:
            temp_pattern = f"{filename}*.part"
            for temp_file in TEMP_DIR.glob(temp_pattern):
                try:
                    temp_file.unlink()
                    print(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    display_error(f"Error removing temp file {temp_file}: {e}")
                    time.sleep(3)
        except Exception as e:
            display_error(f"Error during temp cleanup: {e}")
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

    def verify_download(self, filepath: Path, remote_info: Dict) -> bool:
        """Verify if download is complete and matches expected size."""
        if not filepath.exists():
            return False
        return filepath.stat().st_size == remote_info.get('size', 0)

    def _get_retry_prompt(self) -> str:
        return "\nSelection; Retry Now = R, Alternate URL = 0, Menu = B: "

    def download_file(self, remote_url: str, out_path: Path, chunk_size: int) -> Tuple[bool, Optional[str]]:
        from .interface import (
            display_error,
            display_success,
            display_download_state,
            display_download_summary,
            update_history,
            clear_screen,
            format_file_size  # Added this
        )
        temp_path = TEMP_DIR / f"{out_path.name}.part"  # Initialize temp_path early
        pre_registration_attempts = 0
        retries = 0
        max_pre_attempts = 5

        try:
            while pre_registration_attempts < max_pre_attempts or retries < RUNTIME_CONFIG["download"]["max_retries"]:
                try:
                    # Step 1: Process URL and metadata
                    print(f"Retrieving file metadata (attempt {pre_registration_attempts + retries + 1}): ", end='', flush=True)
                    download_url, metadata = URLProcessor.process_url(remote_url, RUNTIME_CONFIG)
                    print("Done")

                    short_download_url = download_url if len(download_url) <= 60 else f"{download_url[:57]}..."
                    print(f"Resolved download URL: {short_download_url}")

                    filename = metadata.get("filename") or get_file_name_from_url(download_url)
                    if not filename:
                        return False, ERROR_HANDLING["messages"]["filename_error"]
                    print(f"Found filename: {filename}")

                    # Step 2: Check existing download
                    exists, existing_path, state = self._check_existing_download(remote_url, out_path.name)
                    if exists and existing_path:
                        if self.verify_download(existing_path, metadata):
                            if existing_path.suffix == '.part':
                                try:
                                    existing_path.rename(out_path)
                                    display_success(f"Moved completed download to: {out_path}")
                                    update_history(self.config, out_path.name, remote_url, out_path.stat().st_size)
                                except Exception as e:
                                    display_error(f"Failed to move completed download: {e}")
                                    return False, f"Failed to move completed download: {e}"
                            else:
                                display_success(f"File already exists and is complete: {out_path.name}")
                            return True, None
                        elif existing_path.suffix == '.part':
                            temp_path = existing_path  # Use existing .part file

                    # Step 3: Register metadata if not already done
                    early_registration_done = any(self.config[f"filename_{i}"] == filename for i in range(1, 10))
                    if not early_registration_done:
                        total_size = metadata.get('size', 0)
                        self._register_early_metadata(filename, remote_url, total_size)
                        early_registration_done = True

                    # Step 4: Start/resume download
                    existing_size = temp_path.stat().st_size if temp_path.exists() else 0
                    if existing_size > 0:
                        print(f"Found incomplete file, resuming from: {format_file_size(existing_size)}")

                    session = requests.Session()
                    adapter = requests.adapters.HTTPAdapter(max_retries=5, pool_connections=50, pool_maxsize=50)
                    session.mount('https://', adapter)
                    session.mount('http://', adapter)

                    headers = get_download_headers(existing_size)
                    print("Connecting to server...")
                    print("(Ignore Certificate Warnings)")
                    with session.get(
                        download_url,
                        stream=True,
                        headers=headers,
                        timeout=RUNTIME_CONFIG["download"]["timeout"],
                        verify=False
                    ) as response:
                        if response.status_code == 429 and self._handle_rate_limit(response):
                            continue

                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0)) + existing_size

                        start_time = time.time()
                        bytes_since_last_update = 0
                        written_size = existing_size
                        last_fs_update = time.time()
                        last_display_update = last_fs_update

                        with open(temp_path, 'ab' if existing_size else 'wb') as out_file:
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    written_size += len(chunk)
                                    bytes_since_last_update += len(chunk)
                                    current_time = time.time()

                                    if current_time - last_fs_update >= FS_UPDATE_INTERVAL:
                                        current_size = temp_path.stat().st_size
                                        total_size = metadata.get('size', current_size)
                                        last_fs_update = current_time

                                    if current_time - last_display_update >= DISPLAY_REFRESH:
                                        speed = bytes_since_last_update / (current_time - last_display_update)
                                        elapsed = current_time - start_time
                                        remaining = (total_size - written_size) / speed if speed > 0 else 0
                                        display_download_state(
                                            filename=filename,
                                            current_size=written_size,
                                            total_size=total_size,
                                            speed=speed,
                                            elapsed=elapsed,
                                            remaining=remaining
                                        )
                                        if msvcrt.kbhit():
                                            key = msvcrt.getch().decode().lower()
                                            if key == 'a':
                                                return False, "Download abandoned by user"
                                        bytes_since_last_update = 0
                                        last_display_update = current_time

                                    out_file.write(chunk)

                                out_file.flush()
                                os.fsync(out_file.fileno())

                        # Move file to final location
                        import gc
                        gc.collect()
                        time.sleep(1)
                        if not move_with_retry(temp_path, out_path):
                            return False, "Failed to move downloaded file to destination"

                        elapsed = time.time() - start_time
                        average_speed = written_size / elapsed if elapsed > 0 else 0
                        display_download_summary(
                            filename=filename,
                            total_size=written_size,
                            average_speed=average_speed,
                            elapsed=elapsed,
                            timestamp=datetime.now(),
                            destination=str(out_path)
                        )

                        final_size = out_path.stat().st_size
                        update_history(self.config, filename, remote_url, final_size)
                        return True, None

                except Exception as e:
                    # Determine which retry counter to increment
                    if not early_registration_done:
                        pre_registration_attempts += 1
                        if pre_registration_attempts >= max_pre_attempts:
                            return False, f"Failed to initialize download after {max_pre_attempts} attempts"
                    else:
                        retries += 1
                        if retries >= RUNTIME_CONFIG["download"]["max_retries"]:
                            return False, "Maximum retries exceeded"

                    # Exponential backoff with clear_screen
                    delay_seconds = min(2 ** (retries + pre_registration_attempts - 1), 71)  # Cap at 71s
                    title = "Download Error" if not early_registration_done else "Initialize Download"
                    clear_screen(title=title, use_logo=True)
                    print()  # Newline for separation
                    print(f"Error: {str(e)}")
                    print(f"Reconnecting in... {delay_seconds}s", end='', flush=True)
                    for remaining in range(delay_seconds, 0, -1):
                        time.sleep(1)
                        print(f"\rReconnecting in... {remaining}s ", end='', flush=True)
                    print("\nRetrying download...")

        except Exception as e:
            display_error(f"Fatal error: {str(e)}")
            return False, str(e)

        finally:
            if temp_path.exists() and not any(self.config[f"filename_{i}"] == out_path.name for i in range(1, 10)):
                self._cleanup_temp_files(out_path.name)

        return False, "Download failed"



def get_file_name_from_url(url: str) -> Optional[str]:
    """Extract filename from URL or headers."""
    try:
        if "cdn-lfs" in url and (filename := extract_filename_from_disposition(url)):
            return filename

        parsed_url = urlparse(url)
        if filename := os.path.basename(unquote(parsed_url.path)):
            if '.' in filename:
                return filename

        response = requests.head(url, allow_redirects=True)
        if 'Content-Disposition' in response.headers:
            value, params = cgi.parse_header(response.headers['Content-Disposition'])
            if filename := params.get('filename'):
                return filename

        return filename if filename else None

    except Exception as e:
        display_error(f"Error extracting filename from URL: {str(e)}")
        time.sleep(3)
        return None


def handle_orphaned_files(config: dict) -> None:
    from scripts.temporary import BASE_DIR  # Add this import
    registered_files = set()
    for i in range(1, 10):
        filename = config.get(f"filename_{i}", "Empty")
        if filename != "Empty":
            registered_files.add(filename)
            registered_files.add(f"{filename}.part")
    
    downloads_location_str = config.get("downloads_location", "downloads")
    downloads_path = Path(downloads_location_str)
    if not downloads_path.is_absolute():
        downloads_path = BASE_DIR / downloads_path
    downloads_path = downloads_path.resolve()
    
    for folder in [downloads_path, TEMP_DIR]:  # Use resolved path
        for file in folder.glob("*"):
            if file.name in registered_files or any(
                config.get(f"filename_{i}") == file.stem for i in range(1, 10)
            ):
                continue
            try:
                file.unlink()
                print(f"Removed unregistered file: {file}")
            except Exception as e:
                display_error(f"Error removing file {file}: {str(e)}")
                time.sleep(3)

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
    """
    Move file with retry mechanism for Windows file locks.
    Increased retries and delay for better handle release
    """
    for attempt in range(max_retries):
        try:
            if not src.exists():
                display_error(f"Source file missing: {src}")
                return False

            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Force close any potential file handles (Windows-specific)
            if os.name == 'nt':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                dll = ctypes.windll.LoadLibrary("kernel32.dll")
                dll.LockFileEx.argtypes = [
                    ctypes.c_void_p,  # hFile
                    ctypes.c_uint32,  # dwFlags
                    ctypes.c_uint32,  # dwReserved
                    ctypes.c_uint32,  # nNumberOfBytesToLockLow
                    ctypes.c_uint32,  # nNumberOfBytesToLockHigh
                    ctypes.POINTER(ctypes.c_void_p)  # lpOverlapped
                ]
                dll.UnlockFileEx.argtypes = [
                    ctypes.c_void_p,  # hFile
                    ctypes.c_uint32,  # dwReserved
                    ctypes.c_uint32,  # nNumberOfBytesToUnlockLow
                    ctypes.c_uint32,  # nNumberOfBytesToUnlockHigh
                    ctypes.POINTER(ctypes.c_void_p)  # lpOverlapped
                ]

            # Attempt move
            src.replace(dst)  # Using replace instead of rename
            return True

        except PermissionError as e:
            if attempt < max_retries - 1:
                print(f"Move attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                display_error(f"Failed to move file after {max_retries} attempts: {e}")
                time.sleep(3)
                return False

        except Exception as e:
            display_error(f"Unexpected error moving file: {e}")
            time.sleep(3)
            return False

    return False