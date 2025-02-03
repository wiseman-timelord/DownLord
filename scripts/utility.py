# .\scripts\utility.py

import os
import re
import cgi
import time
import hashlib
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
from tqdm import tqdm

from scripts.interface import (
    load_config, display_error, display_success,
    ERROR_MESSAGES, SUCCESS_MESSAGES
)
from scripts.temporary import (
    URL_PATTERNS, CONTENT_TYPES, TEMP_DIR, LOG_FILE, 
    RETRY_STRATEGY, DEFAULT_HEADERS, calculate_retry_delay,
    get_download_headers, extract_filename_from_disposition
)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class DownloadManager:
    def __init__(self):
        self.config = load_config()
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

    def verify_download(self, filepath: Path, expected_hash: Optional[str] = None,
                       hash_type: str = 'sha256') -> bool:
        """Verify downloaded file integrity."""
        if not filepath.exists():
            return False
            
        actual_hash = self.calculate_file_hash(filepath, hash_type)
        return actual_hash == expected_hash if expected_hash else True

    def _get_content_type(self, filename: str) -> str:
        """Determine content type based on file extension."""
        ext = Path(filename).suffix.lower()
        for content_type, extensions in CONTENT_TYPES.items():
            if ext in extensions:
                return content_type
        return "unknown"

    def _register_download(self, filename: str, url: str) -> None:
        """Register a download in the configuration file."""
        # Check if entry already exists
        for i in range(1, 10):
            if self.config.get(f"filename_{i}") == filename and self.config.get(f"url_{i}") == url:
                return  # Already registered
        
        # Shift entries down
        for i in range(9, 1, -1):
            self.config[f"filename_{i}"] = self.config.get(f"filename_{i-1}", "Empty")
            self.config[f"url_{i}"] = self.config.get(f"url_{i-1}", "")
        
        # Add new entry at top
        self.config["filename_1"] = filename
        self.config["url_1"] = url
        
        # Save configuration using imported function
        from scripts.interface import save_config
        save_config(self.config)
        print(f"\nRegistered download for: {filename}")
        
        # Update instance config
        self.config = load_config()

    def download_file(self, remote_url: str, out_path: Path, chunk_size: int) -> Tuple[bool, Optional[str]]:
            """Download a file with retry support."""
            try:
                download_url, metadata = URLProcessor.process_url(remote_url, self.config)
            except DownloadError as e:
                return False, str(e)

            temp_path = TEMP_DIR / f"{out_path.name}.part"
            existing_size = temp_path.stat().st_size if temp_path.exists() else 0
            initial_hash = None
            download_registered = False
            written_size = existing_size
            
            if existing_size > 0 and self.config["download"]["verify_hash"]:
                initial_hash = self.calculate_file_hash(temp_path)
                logging.info(f"Resuming download from {existing_size} bytes")
                display_success(SUCCESS_MESSAGES["resume_success"].format(existing_size))

            session = requests.Session()
            retries = 0
            start_time = time.time()
            
            while retries < self.config["download"]["max_retries"]:
                try:
                    headers = get_download_headers(existing_size)
                    with session.get(
                        download_url,
                        stream=True,
                        headers=headers,
                        timeout=self.config["download"]["timeout"],
                        verify=self.config["security"]["verify_ssl"]
                    ) as response:
                        response.raise_for_status()
                        total_size = int(response.headers.get('content-length', 0)) + existing_size

                        # Truncate filename for display
                        display_name = out_path.name
                        name_part, ext = os.path.splitext(display_name)
                        if len(display_name) > 25:
                            display_name = name_part[:22] + "..." + ext

                        with open(temp_path, 'ab' if existing_size else 'wb') as out_file, \
                             tqdm(total=total_size, initial=existing_size,
                                  unit='B', unit_scale=True, unit_divisor=1024,
                                  desc=display_name,
                                  bar_format='{desc:<25}: {percentage:3.0f}%| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as progress_bar:

                            for chunk in response.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    written_size += len(chunk)
                                    # Register after 1MB written
                                    if not download_registered and written_size >= 1024*1024:
                                        self._register_download(out_path.name, remote_url)
                                        download_registered = True
                                    
                                    # Apply bandwidth limit if configured
                                    if self.config["download"]["bandwidth_limit"]:
                                        time.sleep(len(chunk) / self.config["download"]["bandwidth_limit"])
                                        
                                    out_file.write(chunk)
                                    progress_bar.update(len(chunk))

                    # Verify file integrity
                    if self.config["download"]["verify_hash"] and initial_hash:
                        final_hash = self.calculate_file_hash(temp_path)
                        if initial_hash != final_hash:
                            raise ValueError(ERROR_MESSAGES["hash_mismatch"])

                    # Verify against provided hash if available
                    if metadata.get("sha") and self.config["download"]["verify_hash"]:
                        final_hash = self.calculate_file_hash(temp_path)
                        if final_hash != metadata["sha"]:
                            raise ValueError(ERROR_MESSAGES["hash_mismatch"])

                    temp_path.rename(out_path)
                    download_time = time.time() - start_time
                    speed = total_size / download_time if download_time > 0 else 0
                    logging.info(f"Download completed: {out_path.name}, "
                               f"Size: {total_size}, Speed: {speed:.2f} B/s")
                    return True, None

                except (Timeout, ConnectionError, RequestException) as e:
                    retries += 1
                    if isinstance(e, RequestException) and retries >= self.config["download"]["max_retries"]:
                        return False, ERROR_MESSAGES["download_error"].format(str(e), retries, self.config["download"]["max_retries"])
                    
                    time.sleep(calculate_retry_delay(retries))
                    logging.warning(f"Retry {retries}/{self.config['download']['max_retries']}: {str(e)}")
                    
                except Exception as e:
                    logging.error(f"Unexpected error: {str(e)}")
                    return False, str(e)

            return False, "Maximum retries exceeded"
            
class URLProcessor:
    @staticmethod
    def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process HuggingFace URLs."""
        if "cdn-lfs" in url:
            try:
                logging.info("Processing CDN URL")
                # Simple filename extraction from content-disposition
                if "filename=" in url:
                    # Try to find UTF-8 filename first
                    if "filename*=UTF-8''" in url:
                        start = url.find("filename*=UTF-8''") + 17
                        end = url.find("&", start)
                        if end == -1:
                            end = url.find(";", start)
                        if end == -1:
                            end = len(url)
                        filename = unquote(url[start:end])
                    else:
                        # Try regular filename
                        start = url.find("filename=") + 9
                        end = url.find("&", start)
                        if end == -1:
                            end = url.find(";", start)
                        if end == -1:
                            end = len(url)
                        filename = unquote(url[start:end]).replace('"', '')
                    
                    if filename:
                        logging.info(f"Found filename: {filename}")
                        return url, {"filename": filename, "is_cdn": True}
                
                # Fallback to hash-based name
                parts = url.split('/')
                for part in parts:
                    if len(part) >= 32 and all(c in '0123456789abcdef' for c in part):
                        hash_name = f"hf_download_{part[:8]}.bin"
                        logging.info(f"Using hash-based filename: {hash_name}")
                        return url, {"filename": hash_name, "is_cdn": True}
                
                logging.warning("Using default filename")
                return url, {"filename": "huggingface_download.bin", "is_cdn": True}
            except Exception as e:
                logging.error(f"Error processing CDN URL: {str(e)}")
                return url, {"filename": "huggingface_download.bin", "is_cdn": True}
        
        hf_config = config["download"]["huggingface"]
        headers = DEFAULT_HEADERS.copy()
        if hf_config["use_auth"] and hf_config["token"]:
            headers["authorization"] = f"Bearer {hf_config['token']}"
        
        if model_match := re.match(URL_PATTERNS["huggingface"]["model_pattern"], url):
            try:
                model_id = model_match.group(1)
                response = requests.get(f"https://huggingface.co/api/models/{model_id}/files", 
                                     headers=headers)
                response.raise_for_status()
                files = response.json()
                
                if hf_config["prefer_torch"]:
                    if torch_files := [f for f in files if f["rfilename"].endswith((".pt", ".pth", ".safetensors"))]:
                        files = torch_files
                
                target_file = max(files, key=lambda x: x.get("size", 0))
                return (f"https://huggingface.co/{model_id}/resolve/main/{target_file['rfilename']}",
                        {"size": target_file.get("size", 0), "sha": target_file.get("sha", "")})
            except Exception as e:
                raise DownloadError(f"Failed to process HuggingFace URL: {str(e)}")
        
        if re.match(URL_PATTERNS["huggingface"]["file_pattern"], url):
            return url, {}
            
        raise DownloadError("Invalid HuggingFace URL format")

    @staticmethod
    def process_url(url: str, config: Dict) -> Tuple[str, Dict]:
        """Process URLs based on their type."""
        for platform, pattern in URL_PATTERNS.items():
            if not re.search(pattern["pattern"], url):
                continue
                
            if platform == "huggingface":
                return URLProcessor.process_huggingface_url(url, config)
            elif platform == "dropbox":
                return url.replace("?dl=0", "?dl=1"), {}
                
        return url, {}

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


def download_file(url: str, out_path: Path, chunk_size: int) -> bool:
    """Convenience function for simple downloads."""
    manager = DownloadManager()
    success, error = manager.download_file(url, out_path, chunk_size)
    if not success and error:
        display_error(error)
    return success