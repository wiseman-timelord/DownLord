# .\scripts\utility.py

import os
import re
import cgi
import time
import json
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
from tqdm import tqdm
from .interface import (
    load_config, 
    save_config, 
    display_error, 
    display_success, 
    display_download_status,
    display_download_progress,
    display_download_complete,
    ERROR_MESSAGES, 
    SUCCESS_MESSAGES,
    clear_screen,  # Add this
    format_file_size  # Add this too since it's used in the download messages
)
from .manage import cleanup_orphaned_files
from .temporary import (
    URL_PATTERNS, CONTENT_TYPES, TEMP_DIR, LOG_FILE, RUNTIME_CONFIG,
    RETRY_STRATEGY, DEFAULT_HEADERS, calculate_retry_delay,
    get_download_headers, extract_filename_from_disposition,
    FILE_STATES
)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class DownloadManager:
    def __init__(self):
        self.config = self._load_config()
        self.persistent = load_config()
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.cleanup_unregistered_files()

    def _load_config(self) -> Dict:
        config = RUNTIME_CONFIG.copy()
        persistent = load_config()
        config["download"]["chunk_size"] = persistent["chunk"]
        config["download"]["max_retries"] = persistent["retries"]
        config["download"]["refresh_rate"] = persistent.get("refresh", 2)  # Add refresh rate with default
        return config

    def _check_existing_download(self, url: str, filename: str) -> Tuple[bool, Optional[Path], Dict]:
        downloads_dir = Path("./downloads")
        file_path = downloads_dir / filename
        
        for i in range(1, 10):
            if (self.persistent[f"url_{i}"] == url and 
                self.persistent[f"filename_{i}"] == filename):
                if file_path.exists():
                    return True, file_path, {'index': i}
                self._remove_from_persistent(i)
                break
                
        temp_path = TEMP_DIR / f"{filename}.part"
        if temp_path.exists():
            return True, file_path, {'has_temp': True, 'temp_path': temp_path}
            
        if file_path.exists():
            return True, file_path, {}
            
        return False, None, {}

    def _remove_from_persistent(self, index: int) -> None:
        for i in range(index, 9):
            self.persistent[f"filename_{i}"] = self.persistent[f"filename_{i+1}"]
            self.persistent[f"url_{i}"] = self.persistent[f"url_{i+1}"]
            self.persistent[f"total_size_{i}"] = self.persistent[f"total_size_{i+1}"]
        
        self.persistent["filename_9"] = "Empty"
        self.persistent["url_9"] = ""
        self.persistent["total_size_9"] = 0
        save_config(self.persistent)

    def _register_early_metadata(self, filename: str, url: str, total_size: int) -> None:
        """Register download metadata at 1% progress."""
        try:
            slot_index = None
            for i in range(1, 10):
                if (self.persistent[f"filename_{i}"] == filename and 
                    self.persistent[f"url_{i}"] == url):
                    slot_index = i
                    break
                elif slot_index is None and self.persistent[f"filename_{i}"] == "Empty":
                    slot_index = i
                    break

            if slot_index is not None:
                self.persistent[f"filename_{slot_index}"] = filename
                self.persistent[f"url_{slot_index}"] = url
                self.persistent[f"total_size_{slot_index}"] = total_size
                save_config(self.persistent)
                logging.info(f"Early metadata registered for {filename} in slot {slot_index}")
        except Exception as e:
            logging.error(f"Error registering early metadata: {str(e)}")

    def cleanup_unregistered_files(self) -> None:
        """Remove files not registered in persistent.json."""
        try:
            registered_files = set()
            for i in range(1, 10):
                filename = self.persistent[f"filename_{i}"]
                if filename != "Empty":
                    registered_files.add(filename)
                    registered_files.add(f"{filename}.part")

            for folder in [DOWNLOADS_DIR, TEMP_DIR]:
                for file_path in folder.glob("*"):
                    if file_path.name not in registered_files:
                        try:
                            file_path.unlink()
                            logging.info(f"Removed unregistered file: {file_path}")
                        except Exception as e:
                            logging.error(f"Error removing file {file_path}: {str(e)}")
        except Exception as e:
            logging.error(f"Error in cleanup_unregistered_files: {str(e)}")

    def _cleanup_temp_files(self, filename: str) -> None:
        """Clean up temporary download files."""
        try:
            temp_pattern = f"{filename}*.part"
            for temp_file in TEMP_DIR.glob(temp_pattern):
                try:
                    temp_file.unlink()
                    logging.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logging.error(f"Error removing temp file {temp_file}: {e}")
        except Exception as e:
            logging.error(f"Error during temp cleanup: {e}")

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

        logging.warning(f"Rate limited. Waiting {delay} seconds before retry")
        time.sleep(max(1, delay))
        return True

    def verify_download(self, filepath: Path, remote_info: Dict) -> bool:
        """Verify if download is complete and matches expected size."""
        if not filepath.exists():
            return False
        return filepath.stat().st_size == remote_info.get('size', 0)

    def download_file(self, remote_url: str, out_path: Path, chunk_size: int) -> Tuple[bool, Optional[str]]:
        """Download a file with progress display and early metadata registration."""
        temp_path = None
        try:
            clear_screen("Initiate Download", use_logo=False)
            print("\nInitializing download sequence...")
            print("Processing pasted URL...")
            
            processor = URLProcessor()
            download_url, metadata = processor.process_url(remote_url, self.config)
            
            filename = metadata.get("filename") or get_file_name_from_url(download_url)
            if not filename:
                return False, ERROR_MESSAGES["filename_error"]
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
            
            session = requests.Session()
            retries = 0
            early_registration_done = False
            refresh_rate = self.config["download"].get("refresh_rate", 2)  # Get refresh rate from config

            while retries < self.config["download"]["max_retries"]:
                try:
                    headers = get_download_headers(existing_size)
                    print("Connecting to server...")
                    with session.get(
                        download_url,
                        stream=True,
                        headers=headers,
                        timeout=self.config["download"]["timeout"],
                        verify=False
                    ) as response:
                        if response.status_code == 429 and self._handle_rate_limit(response):
                            continue

                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0)) + existing_size

                        # Setup progress tracking
                        start_time = time.time()
                        last_update_time = start_time
                        bytes_since_last_update = 0
                        written_size = existing_size

                        with open(temp_path, 'ab' if existing_size else 'wb') as out_file:
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    written_size += len(chunk)
                                    bytes_since_last_update += len(chunk)
                                    current_time = time.time()

                                    # Register metadata at 1% progress
                                    if not early_registration_done and total_size > 0:
                                        progress = (written_size / total_size) * 100
                                        if progress >= 1:
                                            self._register_early_metadata(filename, remote_url, total_size)
                                            early_registration_done = True

                                    # Update display based on refresh rate
                                    if current_time - last_update_time >= refresh_rate:
                                        elapsed = int(current_time - start_time)
                                        speed = bytes_since_last_update / (current_time - last_update_time)
                                        remaining = int((total_size - written_size) / speed) if speed > 0 else 0
                                        
                                        display_download_progress(
                                            filename,
                                            written_size,
                                            total_size,
                                            speed,
                                            elapsed,
                                            remaining
                                        )
                                        
                                        bytes_since_last_update = 0
                                        last_update_time = current_time
                                    
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
                                    logging.error(f"Source file missing: {temp_path}")
                                    return False, "Source file missing after download"
                                    
                                out_path.parent.mkdir(parents=True, exist_ok=True)
                                temp_path.replace(out_path)
                                move_success = True
                                break
                                
                            except PermissionError as e:
                                if move_attempt < move_retries - 1:
                                    logging.warning(f"Move attempt {move_attempt + 1} failed, retrying in {move_delay}s: {e}")
                                    time.sleep(move_delay)
                                else:
                                    logging.error(f"Failed to move file after {move_retries} attempts: {e}")
                                    return False, f"Failed to move file: {str(e)}"
                                    
                            except Exception as e:
                                logging.error(f"Unexpected error moving file: {e}")
                                return False, f"Error moving file: {str(e)}"
                        
                        if not move_success:
                            return False, "Failed to move downloaded file to destination"
                        
                        display_download_complete(filename, datetime.now())
                        
                        # Update final size
                        final_size = out_path.stat().st_size
                        for i in range(1, 10):
                            if self.persistent[f"filename_{i}"] == filename:
                                if self.persistent[f"total_size_{i}"] != final_size:
                                    logging.info(f"Updating final size for {filename} from {self.persistent[f'total_size_{i}']} to {final_size}")
                                    self.persistent[f"total_size_{i}"] = final_size
                                    save_config(self.persistent)
                                break
                        
                        return True, None

                except (Timeout, ConnectionError, RequestException) as e:
                    retries += 1
                    if retries >= self.config["download"]["max_retries"]:
                        display_error(ERROR_MESSAGES["download_error"].format(str(e), retries, self.config["download"]["max_retries"]))
                        choice = input("\nSelection; Abandon = A or New URL = 0: ").strip().lower()
                        if choice == 'a':
                            return False, str(e)
                        elif choice == '0':
                            new_url = display_download_prompt()
                            if new_url.lower() == 'q':
                                return False, "User cancelled download"
                            return self.download_file(new_url, out_path, chunk_size)
                        else:
                            return False, "Invalid choice"
                    
                    time.sleep(calculate_retry_delay(retries))
                    logging.warning(f"Retry {retries}/{self.config['download']['max_retries']}: {str(e)}")

        except Exception as e:
            logging.error(f"Download error: {str(e)}")
            display_error(str(e))
            choice = input("\nSelection; Abandon = A or New URL = 0: ").strip().lower()
            if choice == 'a':
                return False, str(e)
            elif choice == '0':
                new_url = display_download_prompt()
                if new_url.lower() == 'q':
                    return False, "User cancelled download"
                return self.download_file(new_url, out_path, chunk_size)
            else:
                return False, "Invalid choice"
        finally:
            # Only cleanup if move failed and temp file still exists
            if temp_path and temp_path.exists():
                self._cleanup_temp_files(out_path.name)

        return False, "Maximum retries exceeded"
            
class URLProcessor:
    @staticmethod
    def get_remote_file_info(url: str, headers: Dict) -> Dict:
        try:
            response = requests.head(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            return {
                'size': int(response.headers.get('content-length', 0)),
                'modified': response.headers.get('last-modified'),
                'etag': response.headers.get('etag'),
                'content_type': response.headers.get('content-type')
            }
        except Exception as e:
            logging.error(f"Error getting remote file info: {str(e)}")
            return {}

    @staticmethod
    def compare_files(local_path: Path, remote_info: Dict) -> str:
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
        """
        Process GitHub URLs for downloading.
        Handles releases, raw content, and repository files.
        """
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
            remote_info = URLProcessor.get_remote_file_info(download_url, headers)
            return download_url, {**remote_info, "filename": filename}

        # Handle raw content
        raw_match = re.match(
            r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)',
            url
        )
        if raw_match:
            owner, repo, branch, path = raw_match.groups()
            download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            remote_info = URLProcessor.get_remote_file_info(download_url, headers)
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
            remote_info = URLProcessor.get_remote_file_info(download_url, headers)
            filename = f"{repo}-main.zip"
            return download_url, {**remote_info, "filename": filename}

        raise DownloadError("Invalid GitHub URL format")

    @staticmethod
    def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
        if "cdn-lfs" in url:
            try:
                logging.info("Processing CDN URL")
                headers = DEFAULT_HEADERS.copy()
                remote_info = URLProcessor.get_remote_file_info(url, headers)
                
                # Parse URL to get content disposition from query parameters
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                content_disp_encoded = query_params.get('response-content-disposition', [None])[0]
                
                if content_disp_encoded:
                    # Decode the content disposition value
                    content_disp = unquote(content_disp_encoded)
                    filename = extract_filename_from_disposition(content_disp)
                    if filename:
                        logging.info(f"Found filename in content disposition: {filename}")
                        return url, {**remote_info, "filename": filename, "is_cdn": True}
                
                # Fallback to URL pattern matching if content disposition not found
                if "filename*=UTF-8''" in url:
                    start = url.find("filename*=UTF-8''") + 17
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0])
                    logging.info(f"Found UTF-8 filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}
                
                if "filename=" in url:
                    start = url.find("filename=") + 9
                    end = url.find("&", start) or len(url)
                    filename = unquote(url[start:end].split(";")[0]).replace('"', '')
                    logging.info(f"Found filename in URL: {filename}")
                    return url, {**remote_info, "filename": filename, "is_cdn": True}
                
                raise DownloadError("Could not find filename in HuggingFace CDN URL")
                
            except Exception as e:
                logging.error(f"Error processing CDN URL: {str(e)}")
                raise DownloadError(f"Failed to process HuggingFace CDN URL: {str(e)}")
        
        # Handle non-CDN HuggingFace URLs
        hf_config = config["download"]["huggingface"]
        headers = DEFAULT_HEADERS.copy()
        if hf_config["use_auth"] and hf_config["token"]:
            headers["authorization"] = f"Bearer {hf_config['token']}"
        
        if model_match := re.match(URL_PATTERNS["huggingface"]["model_pattern"], url):
            try:
                model_id = model_match.group(1)
                response = requests.get(f"https://huggingface.co/api/models/{model_id}/files", headers=headers)
                response.raise_for_status()
                files = response.json()
                
                if hf_config["prefer_torch"]:
                    torch_files = [f for f in files if f["rfilename"].endswith((".pt", ".pth", ".safetensors"))]
                    if torch_files:
                        files = torch_files
                
                target_file = max(files, key=lambda x: x.get("size", 0))
                download_url = f"https://huggingface.co/{model_id}/resolve/main/{target_file['rfilename']}"
                
                # Get remote file info
                remote_info = URLProcessor.get_remote_file_info(download_url, headers)
                return (download_url, {
                    **remote_info,
                    "size": target_file.get("size", 0),
                    "filename": target_file["rfilename"]
                })
            except Exception as e:
                raise DownloadError(f"Failed to process HuggingFace URL: {str(e)}")
        
        if re.match(URL_PATTERNS["huggingface"]["file_pattern"], url):
            remote_info = URLProcessor.get_remote_file_info(url, headers)
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
                remote_info = URLProcessor.get_remote_file_info(processed_url, DEFAULT_HEADERS.copy())
                return processed_url, remote_info
                
        # Handle as direct download if no platform matches
        remote_info = URLProcessor.get_remote_file_info(url, DEFAULT_HEADERS.copy())
        return url, remote_info

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
        logging.error(f"Error extracting filename from URL: {str(e)}")
        return None

def move_with_retry(src: Path, dst: Path, max_retries: int = 5, delay: float = 1.0) -> bool:
    """Move file with retry mechanism for Windows file locks."""
    import time
    
    for attempt in range(max_retries):
        try:
            if not src.exists():
                logging.error(f"Source file missing: {src}")
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
                logging.warning(f"Move attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logging.error(f"Failed to move file after {max_retries} attempts: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Unexpected error moving file: {e}")
            return False
            
    return False

def cleanup_orphaned_files() -> None:
    downloads_dir = Path("./downloads")
    persistent = load_config()
    
    for i in range(1, 10):
        filename = persistent[f"filename_{i}"]
        if filename != "Empty":
            file_path = downloads_dir / filename
            if not file_path.exists():
                for j in range(i, 9):
                    persistent[f"filename_{j}"] = persistent[f"filename_{j+1}"]
                    persistent[f"url_{j}"] = persistent[f"url_{j+1}"]
                    persistent[f"total_size_{j}"] = persistent[f"total_size_{j+1}"]  # Add this
                persistent["filename_9"] = "Empty"
                persistent["url_9"] = ""
                persistent["total_size_9"] = 0  # Add this
    
    save_config(persistent)