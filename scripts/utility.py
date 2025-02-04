# .\scripts\utility.py

import os
import re
import cgi
import time
import json
import hashlib
import requests
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Tuple
from urllib.parse import urlparse, parse_qs, unquote
from requests.exceptions import RequestException, Timeout, ConnectionError
from tqdm import tqdm
from .interface import load_config, save_config, display_error, display_success, ERROR_MESSAGES, SUCCESS_MESSAGES
from .manage import cleanup_orphaned_files
from .temporary import (
    URL_PATTERNS, CONTENT_TYPES, TEMP_DIR, LOG_FILE, RUNTIME_CONFIG,
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
       self.config = self._load_config()
       self.persistent = load_config()
       TEMP_DIR.mkdir(parents=True, exist_ok=True)
       cleanup_orphaned_files()

   def _load_config(self) -> Dict:
       config = RUNTIME_CONFIG.copy()
       persistent = load_config()
       config["download"]["chunk_size"] = persistent["chunk"]
       config["download"]["max_retries"] = persistent["retries"]
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
       
       self.persistent["filename_9"] = "Empty"
       self.persistent["url_9"] = ""
       save_config(self.persistent)

   def _register_download(self, filename: str, url: str, remote_info: Dict) -> None:
       for i in range(1, 10):
           if (self.persistent[f"url_{i}"] == url and 
               self.persistent[f"filename_{i}"] == filename):
               return

       for i in range(9, 1, -1):
           self.persistent[f"filename_{i}"] = self.persistent[f"filename_{i-1}"]
           self.persistent[f"url_{i}"] = self.persistent[f"url_{i-1}"]

       self.persistent["filename_1"] = filename
       self.persistent["url_1"] = url
       save_config(self.persistent)
       logging.info(f"Registered download: {filename} ({url})")

   def verify_download(self, filepath: Path, remote_info: Dict) -> bool:
       if not filepath.exists():
           return False
           
       local_size = filepath.stat().st_size
       return local_size == remote_info.get('size', 0)

   def download_file(self, remote_url: str, out_path: Path, chunk_size: int) -> Tuple[bool, Optional[str]]:
       try:
           # Process URL and get metadata
           download_url, metadata = URLProcessor.process_url(remote_url, self.config)
           
           # Check existing download
           exists, existing_path, state = self._check_existing_download(remote_url, out_path.name)
           if exists and existing_path:
               if self.verify_download(existing_path, metadata):
                   display_success(f"File already exists and is complete: {out_path.name}")
                   return True, None
                   
               if state.get('has_temp', False):
                   temp_path = state['temp_path']
               else:
                   temp_path = TEMP_DIR / f"{out_path.name}.part"
                   if existing_path.exists():
                       existing_path.rename(temp_path)
           else:
               temp_path = TEMP_DIR / f"{out_path.name}.part"

           # Setup download
           existing_size = temp_path.stat().st_size if temp_path.exists() else 0
           session = requests.Session()
           retries = 0
           written_size = existing_size
           download_registered = False

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
                       display_name = out_path.name[:22] + "..." + Path(out_path.name).suffix if len(out_path.name) > 25 else out_path.name
                       
                       with open(temp_path, 'ab' if existing_size else 'wb') as out_file, \
                            tqdm(total=total_size, initial=existing_size,
                                 unit='B', unit_scale=True, unit_divisor=1024,
                                 desc=display_name,
                                 bar_format='{desc:<25}: {percentage:3.0f}%| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as progress_bar:

                           for chunk in response.iter_content(chunk_size=chunk_size):
                               if chunk:
                                   written_size += len(chunk)
                                   if not download_registered and written_size >= self.config["download"]["file_tracking"]["min_register_size"]:
                                       self._register_download(out_path.name, remote_url, metadata)
                                       download_registered = True
                                       
                                   if self.config["download"]["bandwidth_limit"]:
                                       time.sleep(len(chunk) / self.config["download"]["bandwidth_limit"])
                                       
                                   out_file.write(chunk)
                                   progress_bar.update(len(chunk))

                       if self.config["security"]["hash_verification"] and metadata.get("sha"):
                           final_hash = self.calculate_file_hash(temp_path)
                           if final_hash != metadata["sha"]:
                               raise DownloadError(ERROR_MESSAGES["hash_mismatch"])

                       temp_path.rename(out_path)
                       return True, None

               except (Timeout, ConnectionError, RequestException) as e:
                   retries += 1
                   if retries >= self.config["download"]["max_retries"]:
                       return False, ERROR_MESSAGES["download_error"].format(str(e), retries, self.config["download"]["max_retries"])
                   
                   time.sleep(calculate_retry_delay(retries))
                   logging.warning(f"Retry {retries}/{self.config['download']['max_retries']}: {str(e)}")

       except Exception as e:
           logging.error(f"Download error: {str(e)}")
           return False, str(e)

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
   def process_huggingface_url(url: str, config: Dict) -> Tuple[str, Dict]:
       if "cdn-lfs" in url:
           try:
               logging.info("Processing CDN URL")
               # Get remote file info first
               headers = DEFAULT_HEADERS.copy()
               remote_info = URLProcessor.get_remote_file_info(url, headers)
               
               if "filename=" in url:
                   if "filename*=UTF-8''" in url:
                       start = url.find("filename*=UTF-8''") + 17
                       end = url.find("&", start)
                       if end == -1:
                           end = url.find(";", start)
                       if end == -1:
                           end = len(url)
                       filename = unquote(url[start:end])
                   else:
                       start = url.find("filename=") + 9
                       end = url.find("&", start)
                       if end == -1:
                           end = url.find(";", start)
                       if end == -1:
                           end = len(url)
                       filename = unquote(url[start:end]).replace('"', '')
                   
                   if filename:
                       logging.info(f"Found filename: {filename}")
                       return url, {**remote_info, "filename": filename, "is_cdn": True}
               
               parts = url.split('/')
               for part in parts:
                   if len(part) >= 32 and all(c in '0123456789abcdef' for c in part):
                       hash_name = f"hf_download_{part[:8]}.bin"
                       logging.info(f"Using hash-based filename: {hash_name}")
                       return url, {**remote_info, "filename": hash_name, "is_cdn": True}
               
               logging.warning("Using default filename")
               return url, {**remote_info, "filename": "huggingface_download.bin", "is_cdn": True}
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
                   "sha": target_file.get("sha", ""),
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
       for platform, pattern in URL_PATTERNS.items():
           if not re.search(pattern["pattern"], url):
               continue
               
           if platform == "huggingface":
               return URLProcessor.process_huggingface_url(url, config)
           elif platform == "dropbox":
               processed_url = url.replace("?dl=0", "?dl=1")
               remote_info = URLProcessor.get_remote_file_info(processed_url, DEFAULT_HEADERS.copy())
               return processed_url, remote_info
               
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
                persistent["filename_9"] = "Empty"
                persistent["url_9"] = ""
    
    save_config(persistent)

def download_file(url: str, out_path: Path, chunk_size: int) -> bool:
    """Convenience function for simple downloads."""
    manager = DownloadManager()
    success, error = manager.download_file(url, out_path, chunk_size)
    if not success and error:
        display_error(error)
    return success