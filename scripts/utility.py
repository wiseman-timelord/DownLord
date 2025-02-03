# .\scripts\utility.py

import os
import time
import hashlib
import requests
import logging
import threading
import queue
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Tuple, List
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
from tqdm import tqdm

from scripts.interface import (
    load_config,
    display_error,
    print_progress,
    display_success,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES
)
from scripts.temporary import (
    URL_PATTERNS,
    HISTORY_ENTRY,
    CONTENT_TYPES,
    HTTP_CODES,
    TEMP_DIR,
    LOG_FILE,
    ERROR_TYPES,
    RETRY_STRATEGY
)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class URLProcessor:
    """Handles URL processing and transformation for different platforms."""
    
    @staticmethod
    def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process HuggingFace URLs to get direct download links."""
        hf_config = config["download"]["huggingface"]
        headers = URL_PATTERNS["huggingface"]["download_headers"].copy()
        
        if hf_config["use_auth"] and hf_config["token"]:
            headers["authorization"] = f"Bearer {hf_config['token']}"
            
        # Check if it's a model page URL
        model_match = re.match(URL_PATTERNS["huggingface"]["model_pattern"], url)
        if model_match:
            model_id = model_match.group(1)
            api_url = f"https://huggingface.co/api/models/{model_id}/files"
            
            try:
                response = requests.get(api_url, headers=headers)
                response.raise_for_status()
                files = response.json()
                
                # Filter for preferred file type if specified
                if hf_config["prefer_torch"]:
                    preferred_files = [f for f in files if f["rfilename"].endswith((".pt", ".pth", ".safetensors"))]
                    if preferred_files:
                        files = preferred_files
                
                # Get the largest file as default
                target_file = max(files, key=lambda x: x.get("size", 0))
                return (
                    f"https://huggingface.co/{model_id}/resolve/main/{target_file['rfilename']}",
                    {"size": target_file.get("size", 0), "sha": target_file.get("sha", "")}
                )
                
            except Exception as e:
                logging.error(f"Error processing HuggingFace URL: {str(e)}")
                raise DownloadError(f"Failed to process HuggingFace URL: {str(e)}")
                
        # Direct file URL
        file_match = re.match(URL_PATTERNS["huggingface"]["file_pattern"], url)
        if file_match:
            return url, {}
            
        raise DownloadError("Invalid HuggingFace URL format")

    @staticmethod
    def process_gdrive_url(url: str) -> str:
        """Process Google Drive URLs to get direct download links."""
        file_id_match = re.search(URL_PATTERNS["google_drive"]["file_id_pattern"], url)
        if not file_id_match:
            raise DownloadError("Invalid Google Drive URL format")
            
        file_id = file_id_match.group(1)
        return URL_PATTERNS["google_drive"]["download_url"].format(file_id)

    @staticmethod
    def process_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process URLs based on their type and return direct download link."""
        for platform, pattern in URL_PATTERNS.items():
            if re.search(pattern["pattern"], url):
                if platform == "huggingface":
                    return URLProcessor.process_huggingface_url(url, config)
                elif platform == "google_drive":
                    return URLProcessor.process_gdrive_url(url), {}
                elif platform == "dropbox":
                    return url.replace("?dl=0", "?dl=1"), {}
                elif platform == "direct":
                    return url, {}
                    
        return url, {}  # Return as-is if no special processing needed

def get_file_name_from_url(url: str) -> Optional[str]:
    """Extract filename from URL or Content-Disposition header."""
    try:
        # Try to get filename from the URL first
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        filename = os.path.basename(path)
        
        if filename and '.' in filename:
            return filename
            
        # If no filename found, try to get it from headers
        response = requests.head(url, allow_redirects=True)
        if 'Content-Disposition' in response.headers:
            import cgi
            value, params = cgi.parse_header(response.headers['Content-Disposition'])
            if 'filename' in params:
                return params['filename']
                
        if filename:
            return filename
            
    except Exception as e:
        logging.error(f"Error extracting filename from URL: {str(e)}")
        
    return None

class DownloadManager:
    """Manages file downloads with advanced features."""
    
    def __init__(self):
        self.config = load_config()
        self.active_downloads = {}
        self.download_queue = queue.Queue()
        self.lock = threading.Lock()
        
        # Ensure temp directory exists
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def calculate_file_hash(self, filepath: Path, hash_type: str = 'sha256') -> str:
        """Calculate file hash using specified algorithm."""
        hash_functions = {
            'sha256': hashlib.sha256(),
            'sha1': hashlib.sha1(),
            'md5': hashlib.md5()
        }
        
        if hash_type not in hash_functions:
            raise ValueError(f"Unsupported hash type: {hash_type}")
            
        hash_obj = hash_functions[hash_type]
        
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file hash: {str(e)}")
            raise

    def create_download_entry(
        self,
        filename: str,
        url: str,
        size: int = 0,
        status: str = "pending"
    ) -> Dict:
        """Create a new download history entry with enhanced metadata."""
        entry = HISTORY_ENTRY.copy()
        entry.update({
            "id": hashlib.md5(f"{url}{time.time()}".encode()).hexdigest(),
            "filename": filename,
            "url": url,
            "timestamp_start": datetime.now().isoformat(),
            "status": status,
            "size": {
                "total": size,
                "downloaded": 0
            },
            "content_type": self._get_content_type(filename),
            "attempts": 0
        })
        return entry

    def _get_content_type(self, filename: str) -> str:
        """Determine content type based on file extension."""
        ext = Path(filename).suffix.lower()
        for content_type, extensions in CONTENT_TYPES.items():
            if ext in extensions:
                return content_type
        return "unknown"

    def verify_download(
        self,
        filepath: Path,
        expected_hash: Optional[str] = None,
        hash_type: str = 'sha256'
    ) -> bool:
        """Verify downloaded file integrity."""
        if not filepath.exists():
            return False
            
        actual_hash = self.calculate_file_hash(filepath, hash_type)
        
        if expected_hash:
            return actual_hash == expected_hash
            
        return True

    def download_file(
        self,
        remote_url: str,
        out_path: Path,
        chunk_size: int,
        callback=None
    ) -> Tuple[bool, Optional[str]]:
        """
        Download a file with advanced features.
        
        Args:
            remote_url: URL to download from
            out_path: Path to save the file
            chunk_size: Size of chunks to download
            callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        config = self.config["download"]
        max_retries = config["max_retries"]
        timeout = config["timeout"]
        
        # Process URL based on platform
        try:
            download_url, metadata = URLProcessor.process_url(remote_url, self.config)
        except DownloadError as e:
            return False, str(e)
        
        temp_path = TEMP_DIR / f"{out_path.name}.part"
        existing_size = temp_path.stat().st_size if temp_path.exists() else 0
        initial_hash = None

        if existing_size > 0 and config["verify_hash"]:
            initial_hash = self.calculate_file_hash(temp_path)
            logging.info(f"Resuming download from {existing_size} bytes")
            display_success(SUCCESS_MESSAGES["resume_success"].format(existing_size))

        session = requests.Session()
        retries = 0
        start_time = time.time()
        
        while retries < max_retries:
            try:
                headers = {
                    "Range": f"bytes={existing_size}-"
                } if existing_size else {}

                # Add user agent and other headers
                headers.update({
                    "User-Agent": "DownLord/1.2.0",
                    "Accept": "*/*",
                    "Connection": "keep-alive"
                })

                with session.get(
                    download_url,
                    stream=True,
                    headers=headers,
                    timeout=timeout,
                    verify=config["verify_ssl"]
                ) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    total_size += existing_size

                    mode = 'ab' if existing_size else 'wb'
                    with open(temp_path, mode) as out_file, \
                         tqdm(
                             total=total_size,
                             initial=existing_size,
                             unit='B',
                             unit_scale=True,
                             unit_divisor=1024,
                             desc=out_path.name
                         ) as progress_bar:

                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:
                                # Apply bandwidth limit if configured
                                if config["bandwidth_limit"]:
                                    time.sleep(len(chunk) / config["bandwidth_limit"])

                                out_file.write(chunk)
                                progress_bar.update(len(chunk))
                                
                                if callback:
                                    callback(progress_bar.n, total_size)

                # Verify file integrity
                if config["verify_hash"] and initial_hash:
                    final_hash = self.calculate_file_hash(temp_path)
                    if initial_hash != final_hash:
                        raise ValueError(ERROR_MESSAGES["hash_mismatch"])

                # Verify against provided hash if available
                if metadata.get("sha") and config["verify_hash"]:
                    final_hash = self.calculate_file_hash(temp_path)
                    if final_hash != metadata["sha"]:
                        raise ValueError(ERROR_MESSAGES["hash_mismatch"])

                # Move temp file to final location
                temp_path.rename(out_path)
                
                # Update download statistics
                download_time = time.time() - start_time
                speed = total_size / download_time if download_time > 0 else 0
                logging.info(f"Download completed: {out_path.name}, "
                           f"Size: {total_size}, Speed: {speed:.2f} B/s")
                
                return True, None

            except Timeout:
                retries += 1
                delay = min(RETRY_STRATEGY["initial_delay"] * 
                          (RETRY_STRATEGY["backoff_factor"] ** retries),
                          RETRY_STRATEGY["max_delay"])
                logging.warning(f"Timeout occurred (attempt {retries}/{max_retries})")
                time.sleep(delay)
                
            except ConnectionError as e:
                retries += 1
                delay = min(RETRY_STRATEGY["initial_delay"] * 
                          (RETRY_STRATEGY["backoff_factor"] ** retries),
                          RETRY_STRATEGY["max_delay"])
                logging.error(f"Connection error: {str(e)} (attempt {retries}/{max_retries})")
                time.sleep(delay)
                
            except RequestException as e:
                retries += 1
                error_msg = ERROR_MESSAGES["download_error"].format(
                    str(e), retries, max_retries)
                logging.error(error_msg)
                
                if retries >= max_retries:
                    return False, error_msg
                    
                delay = min(RETRY_STRATEGY["initial_delay"] * 
                          (RETRY_STRATEGY["backoff_factor"] ** retries),
                          RETRY_STRATEGY["max_delay"])
                time.sleep(delay)
                
            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                return False, str(e)

        return False, "Maximum retries exceeded"

def download_file(url: str, out_path: Path, chunk_size: int) -> bool:
    """
    Convenience function for simple downloads.
    
    Args:
        url: URL to download from
        out_path: Path to save the file
        chunk_size: Size of chunks to download
        
    Returns:
        bool: True if download successful, False otherwise
    """
    manager = DownloadManager()
    success, error = manager.download_file(url, out_path, chunk_size)
    
    if not success and error:
        display_error(error)
        
    return success