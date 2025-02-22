# Script: `.\scripts\manage.py`

# Imports
import os, cgi, re, time, requests, json, random, socket
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
from tqdm import tqdm
from .configure import ConfigManager
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
    DEFAULT_CONFIG
)
from .interface import (
    display_error,
    display_success,
    display_download_state,
    display_download_complete,
    clear_screen,
    format_file_size,
    display_download_prompt,
    display_download_summary,
    update_history,
    delete_file
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

        print_status("Establishing connection...")

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
    @register_handler("huggingface")
    def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process HuggingFace URLs for downloading."""
        if "cdn-lfs" in url:
            try:
                print("\nProcessing CDN URL")
                headers = DEFAULT_HEADERS.copy()
                timeout_length = config.get("timeout_length", 120)
                start_time = time.time()
                print(f"Verifying URL accessibility ({timeout_length}s timeout): ", end='', flush=True)
                
                while (time.time() - start_time) < timeout_length:
                    try:
                        test_response = requests.head(
                            url,
                            headers=headers,
                            allow_redirects=True,
                            timeout=1
                        )
                        if test_response.status_code != 200:
                            raise DownloadError(f"URL returned status code: {test_response.status_code}")
                        elapsed = time.time() - start_time
                        print(f"Completed in {elapsed:.1f}s")
                        break
                    except (Timeout, ConnectionError):
                        remaining = timeout_length - (time.time() - start_time)
                        print(f"{remaining:.1f}s", end=' ', flush=True)
                        continue

                remote_info = URLProcessor.get_remote_file_info(url, headers, config)
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                content_disp_encoded = query_params.get('response-content-disposition', [None])[0]
                if content_disp_encoded:
                    content_disp = unquote(content_disp_encoded).replace('\r', '').replace('\n', '')
                    filename = extract_filename_from_disposition(content_disp)
                    if filename:
                        print(f"Found filename: {filename}")
                        return url, {"filename": filename, "is_cdn": True}

                if "filename*=UTF-8''" in url:
                    start = url.find("filename*=UTF-8''") + 17
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0])
                    print(f"Found UTF-8 filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}

                if "filename=" in url:
                    start = url.find("filename=") + 9
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0]).replace('"', '')
                    print(f"Found filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}

                raise DownloadError("Could not find filename in HuggingFace CDN URL")

            except Exception as e:
                display_error(f"CDN URL processing failed: {str(e)}")
                time.sleep(3)
                raise DownloadError(f"HuggingFace CDN error: {str(e)}")

        hf_config = config["download"]["huggingface"]
        headers = DEFAULT_HEADERS.copy()
        if hf_config["use_auth"] and hf_config["token"]:
            headers["authorization"] = f"Bearer {hf_config['token']}"

        if model_match := re.match(URL_PATTERNS["huggingface"]["model_pattern"], url):
            try:
                model_id = model_match.group(1)
                response = requests.head(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    timeout=config.get("timeout_length", 60)
                )
                response.raise_for_status()
                files = response.json()

                if hf_config["prefer_torch"]:
                    torch_files = [f for f in files if f["rfilename"].endswith((".pt", ".pth", ".safetensors"))]
                    if torch_files:
                        files = torch_files

                target_file = max(files, key=lambda x: x.get("size", 0))
                download_url = f"https://huggingface.co/{model_id}/resolve/main/{target_file['rfilename']}"

                remote_info = URLProcessor.get_remote_file_info(download_url, headers, config)
                return (download_url, {
                    **remote_info,
                    "size": target_file.get("size", 0),
                    "filename": target_file["rfilename"]
                })
            except Exception as e:
                raise DownloadError(f"Failed to process HuggingFace URL: {str(e)}")

        if re.match(URL_PATTERNS["huggingface"]["file_pattern"], url):
            remote_info = URLProcessor.get_remote_file_info(url, headers, config)
            return url, remote_info

        raise DownloadError("Invalid HuggingFace URL format")

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


@staticmethod
def get_remote_file_info(url: str, headers: Dict, config: Dict) -> Dict:
    """Get metadata about a remote file with timeout countdown."""
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
    def process_github_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process GitHub URLs for downloading."""
        headers = DEFAULT_HEADERS.copy()
        if 'Authorization' in headers:
            del headers['Authorization']

        # Handle release assets
        release_match = re.match(
            r'https?://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)',
            url
        )
        if release_match:
            owner, repo, tag, filename = release_match.groups()
            download_url = f"https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}"
            remote_info = URLProcessor.get_remote_file_info(download_url, headers, config)
            return download_url, {**remote_info, "filename": filename}

        # Handle raw content
        raw_match = re.match(
            r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)',
            url
        )
        if raw_match:
            owner, repo, branch, path = raw_match.groups()
            download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            remote_info = URLProcessor.get_remote_file_info(download_url, headers, config)
            filename = os.path.basename(path)
            return download_url, {**remote_info, "filename": filename}

        # Handle repository archive
        archive_match = re.match(
            r'https?://github\.com/([^/]+)/([^/]+)/?$',
            url
        )
        if archive_match:
            owner, repo = archive_match.groups()
            download_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
            remote_info = URLProcessor.get_remote_file_info(download_url, headers, config)
            filename = f"{repo}-main.zip"
            return download_url, {**remote_info, "filename": filename}

        raise DownloadError("Invalid GitHub URL format")

    @staticmethod
    def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
        if "cdn-lfs" in url:
            try:
                print("\nProcessing CDN URL")  # Single newline
                headers = DEFAULT_HEADERS.copy()

                # Verify URL accessibility
                timeout_length = config.get("timeout_length", 120)
                start_time = time.time()
                print(f"Verifying URL accessibility ({timeout_length}s timeout): ", end='', flush=True)
                
                while (time.time() - start_time) < timeout_length:
                    try:
                        # Removed duplicate timeout print here
                        test_response = requests.head(
                            url,
                            headers=headers,
                            allow_redirects=True,
                            timeout=1
                        )
                        if test_response.status_code != 200:
                            raise DownloadError(f"URL returned status code: {test_response.status_code}")
                        elapsed = time.time() - start_time
                        print(f"Completed in {elapsed:.1f}s")
                        break
                    except (Timeout, ConnectionError):
                        remaining = timeout_length - (time.time() - start_time)
                        print(f"{remaining:.1f}s", end=' ', flush=True)
                        continue

                remote_info = URLProcessor.get_remote_file_info(url, headers, config)

                # Parse URL to get content disposition from query parameters
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                content_disp_encoded = query_params.get('response-content-disposition', [None])[0]
                if content_disp_encoded:
                    # Decode and clean the content disposition
                    content_disp = unquote(content_disp_encoded).replace('\r', '').replace('\n', '')
                    filename = extract_filename_from_disposition(content_disp)
                    if filename:
                        print(f"Found filename: {filename}")
                        return url, {"filename": filename, "is_cdn": True}

                # Fallback to URL pattern matching if content disposition not found
                if "filename*=UTF-8''" in url:
                    start = url.find("filename*=UTF-8''") + 17
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0])
                    print(f"Found UTF-8 filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}

                if "filename=" in url:
                    start = url.find("filename=") + 9
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0]).replace('"', '')
                    print(f"Found filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}

                raise DownloadError("Could not find filename in HuggingFace CDN URL")

            except Exception as e:
                display_error(f"CDN URL processing failed: {str(e)}")
                time.sleep(3)
                raise DownloadError(f"HuggingFace CDN error: {str(e)}")

        # Handle non-CDN HuggingFace URLs
        hf_config = config["download"]["huggingface"]
        headers = DEFAULT_HEADERS.copy()
        if hf_config["use_auth"] and hf_config["token"]:
            headers["authorization"] = f"Bearer {hf_config['token']}"

        if model_match := re.match(URL_PATTERNS["huggingface"]["model_pattern"], url):
            try:
                model_id = model_match.group(1)
                response = requests.head(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    timeout=config.get("timeout_length", 60)
                )
                response.raise_for_status()
                files = response.json()

                if hf_config["prefer_torch"]:
                    torch_files = [f for f in files if f["rfilename"].endswith((".pt", ".pth", ".safetensors"))]
                    if torch_files:
                        files = torch_files

                target_file = max(files, key=lambda x: x.get("size", 0))
                download_url = f"https://huggingface.co/{model_id}/resolve/main/{target_file['rfilename']}"

                # Get remote file info
                remote_info = URLProcessor.get_remote_file_info(download_url, headers, config)
                return (download_url, {
                    **remote_info,
                    "size": target_file.get("size", 0),
                    "filename": target_file["rfilename"]
                })
            except Exception as e:
                raise DownloadError(f"Failed to process HuggingFace URL: {str(e)}")

        if re.match(URL_PATTERNS["huggingface"]["file_pattern"], url):
            remote_info = URLProcessor.get_remote_file_info(url, headers, config)
            return url, remote_info

        raise DownloadError("Invalid HuggingFace URL format")

    @staticmethod
    def process_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process URLs based on their platform type."""
        for platform, pattern in URL_PATTERNS.items():
            if not re.search(pattern["pattern"], url):
                continue

            if platform == "huggingface":
                return URLProcessor.process_huggingface_url(url, config)
            elif platform == "github":
                return URLProcessor.process_github_url(url, config)
            elif platform == "dropbox":
                processed_url = url.replace("?dl=0", "?dl=1")
                remote_info = URLProcessor.get_remote_file_info(processed_url, DEFAULT_HEADERS.copy(), config)
                return processed_url, remote_info

        # Handle as direct download if no platform matches
        remote_info = URLProcessor.get_remote_file_info(url, DEFAULT_HEADERS.copy(), config)
        return url, remote_info


class DownloadManager:
    """Manage file downloads with retries and resume support."""

    def __init__(self, downloads_location: Path):
        self.config = ConfigManager.load()
        self.downloads_location = downloads_location
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Register existing temp files
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
        for i in range(1, 10):
            if self.config[f"filename_{i}"] in ["Empty", filename]:
                self.config[f"filename_{i}"] = filename
                self.config[f"url_{i}"] = url
                self.config[f"total_size_{i}"] = total_size
                ConfigManager.save(self.config)
                break

    def _register_early_metadata(self, filename: str, url: str, total_size: int) -> None:
        """
        Register download metadata immediately after verifying total size.
        Ensures the entry is added to the JSON configuration file early in the download process.
        """
        try:
            # Ensure total_size is valid before registering
            if total_size > 0:
                # Register the file entry in the first available slot
                for i in range(1, 10):
                    if self.config[f"filename_{i}"] in ["Empty", filename]:
                        self.config[f"filename_{i}"] = filename
                        self.config[f"url_{i}"] = url
                        self.config[f"total_size_{i}"] = total_size
                        ConfigManager.save(self.config)
                        print(f"Registered early metadata for: {filename} (Size: {total_size})")
                        print("Setting up download...") # Long wait, after here and before `Download Active` display, leave in.  
                        break
            else:
                display_error("Could not determine file size from server. Registration delayed.")
                # Retry registration after a delay or when size is available
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
        """Download a file from a remote URL with retries and resume support."""
        temp_path = None
        try:
            # Truncate the remote URL for display
            short_remote_url = remote_url if len(remote_url) <= 60 else f"{remote_url[:57]}..."
            print(f"Initializing download for: {short_remote_url}")
            print("Processing download URL...")

            print(f"\nRetrieving file metadata: ", end='', flush=True)  # Removed [2/2]
            download_url, metadata = URLProcessor.process_url(remote_url, RUNTIME_CONFIG)
            print("Done")  # Replace JSON dump

            # Truncate the resolved download URL for display
            short_download_url = download_url if len(download_url) <= 60 else f"{download_url[:57]}..."
            print(f"Resolved download URL: {short_download_url}")

            filename = metadata.get("filename") or get_file_name_from_url(download_url)
            if not filename:
                return False, ERROR_HANDLING["messages"]["filename_error"]
            print(f"Found filename: {filename}")

            exists, existing_path, state = self._check_existing_download(remote_url, out_path.name)

            if exists and existing_path:
                if self.verify_download(existing_path, metadata):
                    display_success(f"File already exists and is complete: {out_path.name}")
                    return True, None

                temp_path = state.get('temp_path') if state.get('has_temp') else TEMP_DIR / f"{out_path.name}.part"
                if existing_path.exists() and not state.get('has_temp'):
                    existing_path.rename(temp_path)
            else:
                temp_path = TEMP_DIR / f"{out_path.name}.part"

            existing_size = temp_path.stat().st_size if temp_path and temp_path.exists() else 0
            if existing_size > 0:
                print(f"Found incomplete file, resuming from: {format_file_size(existing_size)}")

            # Create session with custom retry and connection settings
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                max_retries=5,
                pool_connections=50,
                pool_maxsize=50
            )
            session.mount('https://', adapter)
            session.mount('http://', adapter)

            retries = 0
            early_registration_done = False
            last_fs_update = time.time()
            last_display_update = last_fs_update

            while retries < RUNTIME_CONFIG["download"]["max_retries"]:
                try:
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

                        # Register metadata immediately after getting total size
                        if not early_registration_done:
                            self._register_early_metadata(filename, remote_url, total_size)
                            early_registration_done = True

                        # Setup progress tracking
                        start_time = time.time()
                        bytes_since_last_update = 0
                        written_size = existing_size

                        with open(temp_path, 'ab' if existing_size else 'wb') as out_file:
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    written_size += len(chunk)
                                    bytes_since_last_update += len(chunk)
                                    current_time = time.time()

                                    # File system updates (every 5 seconds)
                                    if current_time - last_fs_update >= 5:
                                        current_size = temp_path.stat().st_size
                                        total_size = metadata.get('size', current_size)
                                        last_fs_update = current_time

                                    # Visual updates (every 1 second)
                                    if current_time - last_display_update >= 1:
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
                                        
                                        bytes_since_last_update = 0
                                        last_display_update = current_time

                                    out_file.write(chunk)

                            # Ensure file is closed before moving
                            out_file.flush()
                            os.fsync(out_file.fileno())

                        # Force garbage collection before move
                        import gc
                        gc.collect()

                        # Attempt move with retries
                        move_success = False
                        move_retries = 5
                        move_delay = 1.0

                        for move_attempt in range(move_retries):
                            try:
                                if not temp_path.exists():
                                    display_error(f"Source file missing: {temp_path}")
                                    time.sleep(3)
                                    return False, "Source file missing after download"

                                out_path.parent.mkdir(parents=True, exist_ok=True)
                                if not move_with_retry(temp_path, out_path):
                                    raise DownloadError("File move failed")
                                move_success = True
                                break

                            except PermissionError as e:
                                if move_attempt < move_retries - 1:
                                    print(f"Move attempt {move_attempt + 1} failed, retrying in {move_delay}s: {e}")
                                    time.sleep(move_delay)
                                else:
                                    display_error(f"Failed to move file after {move_retries} attempts: {e}")
                                    time.sleep(3)
                                    return False, f"Failed to move file: {str(e)}"

                            except Exception as e:
                                display_error(f"Unexpected error moving file: {e}")
                                time.sleep(3)
                                return False, f"Error moving file: {str(e)}"

                        if not move_success:
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

                        # Update final size
                        final_size = out_path.stat().st_size
                        for i in range(1, 10):
                            if self.config[f"filename_{i}"] == filename:
                                if self.config[f"total_size_{i}"] != final_size:
                                    print(f"Updating final size for {filename} from {self.config[f'total_size_{i}']} to {final_size}")
                                    self.config[f"total_size_{i}"] = final_size
                                    ConfigManager.save(self.config)
                                break

                        return True, None

                except OSError as e:
                    if e.errno == 28:  # No space left on device
                        display_error("No space left on device - Cannot continue download")
                        time.sleep(3)
                        choice = input("\nSelection; Resume Download = R, Back To Menu = B: ").strip().lower()
                        if choice == 'b':
                            return False, "Returning to menu"
                        elif choice == 'r':
                            continue  # Continue the download loop
                        else:
                            return False, "Invalid choice"
                    else:
                        raise  # Re-raise other OSError exceptions

                except (Timeout, ConnectionError, RequestException) as e:
                    retries += 1
                    if retries >= RUNTIME_CONFIG["download"]["max_retries"]:
                        display_error("Download Initialization Failed.\nCheck link validity, internet, firewall, and then retry.")
                        choice = input("\nSelection; Resume Download = R, Alternate URL = 0, Back to Menu = B: ").strip().lower()
                        if choice == 'r':
                            return self.download_file(remote_url, out_path, chunk_size)  # Retry same URL
                        elif choice == '0':
                            new_url = display_download_prompt()
                            return self.download_file(new_url, out_path, chunk_size)
                        elif choice == 'b':
                            return False, "Returning to menu"
                        else:
                            return False, "Invalid choice"
                    else:
                        time.sleep(calculate_retry_delay(retries))
                        print(f"Retry {retries}/{RUNTIME_CONFIG['download']['max_retries']}: {str(e)}")

        except Exception as e:
            display_error(f"Download error: {str(e)}")
            display_error(str(e))
            time.sleep(3)
            choice = input("\nSelection; New URL = 0, Back to Menu = B: ").strip().lower()
            if choice == '0':
                new_url = display_download_prompt()
                if new_url.lower() == 'q':
                    return False, "User cancelled download"
                return self.download_file(new_url, out_path, chunk_size)
            elif choice == 'b':
                return False, "Returning to menu"
            else:
                return False, "Invalid choice"
        finally:
            # Only cleanup if move failed and temp file still exists
            if temp_path and temp_path.exists():
                self._cleanup_temp_files(out_path.name)

        return False, "Maximum retries exceeded"


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
    """
    Unified orphan handling: registration + cleanup.
    """
    registered_files = set()

    # 1. Register orphans
    for folder in [TEMP_DIR, DOWNLOADS_DIR]:
        for file in folder.glob("*"):
            filename = file.stem if file.suffix == ".part" else file.name
            if not any(config.get(f"filename_{i}") == filename for i in range(1, 10)):
                # Register in first empty slot
                for i in range(1, 10):
                    if config[f"filename_{i}"] == "Empty":
                        config[f"filename_{i}"] = filename
                        config[f"url_{i}"] = ""
                        config[f"total_size_{i}"] = file.stat().st_size
                        registered_files.add(filename)
                        break

    # 2. Cleanup unregistered
    for folder in [TEMP_DIR, DOWNLOADS_DIR]:
        for file in folder.glob("*"):
            if file.name not in registered_files and not any(
                config.get(f"filename_{i}") == file.name for i in range(1, 10)
            ):
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


def move_with_retry(src: Path, dst: Path, max_retries: int = 5, delay: float = 1.0) -> bool:
    """
    Move file with retry mechanism for Windows file locks.
    """
    import time

    for attempt in range(max_retries):
        try:
            if not src.exists():
                display_error(f"Source file missing: {src}")
                return False

            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Force close any potential file handles
            import gc
            gc.collect()

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