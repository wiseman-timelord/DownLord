# .\scripts\temporary.py

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import unquote

# Application Metadata
APP_TITLE = "DownLord"

# Directory Structure
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = BASE_DIR / "downloads"
SCRIPTS_DIR = BASE_DIR / "scripts"
TEMP_DIR = BASE_DIR / "data/temp"

# File Paths
PERSISTENT_FILE = DATA_DIR / "persistent.json"
REQUIREMENTS_FILE = DATA_DIR / "requirements.txt"
LOG_FILE = DATA_DIR / "downlord.log"

# Configuration Defaults
DEFAULT_CHUNK_SIZES = {
   "slow": 1024000,      # ~1MBit/s
   "mobile": 2048000,    # ~2.5MBit/s
   "line": 4096000,      # ~5MBit/s
   "fibre": 8192000,     # ~10MBit/s
   "custom": None        # User-defined
}

FILE_STATES = {
   "new": "new",
   "partial": "partial",
   "complete": "complete",
   "error": "error",
   "orphaned": "orphaned"
}

FILE_STATE_MESSAGES = {
   "new": "Starting new download",
   "partial": "Resuming partial download ({size_done}/{size_total} bytes)",
   "complete": "File already downloaded",
   "error": "Previous download failed, retrying",
   "orphaned": "Found orphaned file, cleaning up"
}

DOWNLOAD_STATUS = {
   "pending": "Pending",
   "downloading": "Downloading",
   "paused": "Paused",
   "complete": "Complete",
   "error": "Error",
   "cancelled": "Cancelled",
   "verifying": "Verifying",
   "cleaning": "Cleaning up"
}

DOWNLOAD_VALIDATION = {
   "size_mismatch": "size_mismatch", 
   "incomplete": "incomplete",
   "complete": "complete",
   "unknown": "unknown"
}

DISPLAY_FORMATS = {
   "progress": "{filename}: {status} [{done}/{total}] {speed}/s",
   "status": "{filename}: {status}",
   "error": "Error: {message}",
   "success": "Success: {message}"
}

# Runtime Configuration
RUNTIME_CONFIG = {
   "download": {
       "timeout": 30,
       "parallel_downloads": False,
       "max_parallel": 3,
       "bandwidth_limit": None,
       "auto_resume": True,
       "huggingface": {
           "use_auth": False,
           "token": None,
           "mirror": None,
           "prefer_torch": True
       },
       "file_tracking": {
           "track_partial": True,
           "verify_existing": True,
           "cleanup_orphans": True,
           "min_register_size": 1048576  # 1MB in bytes
       }
   },
   "storage": {
       "temp_dir": str(TEMP_DIR),
       "download_dir": str(DOWNLOADS_DIR),
       "keep_incomplete": True,
       "organize_by_type": False,
       "auto_extract": False
   },
   "interface": {
       "show_progress": True,
       "show_speed": True,
       "show_eta": True,
       "dark_mode": False,
       "detailed_logging": False,
       "notification_sound": False,
       "progress_bar_style": "tqdm"
   }
}

# Content Types and Extensions
CONTENT_TYPES = {
   "model": [".ckpt", ".pt", ".pth", ".safetensors", ".bin", ".onnx", ".h5"],
   "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp"],
   "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma", ".alac", ".aiff"],
   "document": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xlsx", ".pptx", ".csv", ".epub"],
   "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
   "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"],
   "code": [".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".md"]
}

# Enhanced Download History Entry
HISTORY_ENTRY = {
   "id": "",
   "filename": "",
   "url": "",
   "timestamp_start": "",
   "timestamp_end": "",
   "status": "pending",
   "size": {
       "total": 0,
       "downloaded": 0
   },
   "speed": {
       "average": 0,
       "peak": 0
   },
   "attempts": 0,
   "error_log": [],
   "content_type": "",
   "headers": {},
   "resume_position": 0,
   "source": "",
   "metadata": {}
}

# URL Patterns
URL_PATTERNS = {
   "huggingface": {
       "pattern": r"huggingface.co|hf.co",
       "direct_download": False,
       "requires_auth": False,
       "api_pattern": r"^https://huggingface.co/api/.*",
       "model_pattern": r"^https://huggingface.co/([^/]+/[^/]+)(?:/tree/main)?/?$",
       "file_pattern": r"^https://huggingface.co/([^/]+/[^/]+)/resolve/main/(.+)$",
       "download_headers": {
           "user-agent": f"DownLord",
           "accept": "*/*"
       },
       "mirror_endpoints": {
           "default": "https://huggingface.co",
           "china": "https://hf-mirror.com"
       }
   },
   "google_drive": {
       "pattern": r"drive.google.com",
       "direct_download": False,
       "requires_auth": False,
       "file_id_pattern": r"\/d\/([-\w]+)",
       "download_url": "https://drive.google.com/uc?id={}&export=download"
   },
   "dropbox": {
       "pattern": r"dropbox.com",
       "direct_download": True,
       "download_param": "dl=1",
       "share_link_pattern": r"dropbox.com/s/([a-z0-9]+)/([^?]+)"
   },
   "github": {
       "pattern": r"github.com",
       "direct_download": True,
       "raw_domain": "raw.githubusercontent.com",
       "release_pattern": r"releases/download/([^/]+)/([^/]+)"
   },
   "direct": {
       "pattern": r"^https?://",
       "direct_download": True,
       "requires_auth": False
   }
}

# HTTP Status Codes
HTTP_CODES = {
   200: "OK",
   206: "Partial Content",
   301: "Moved Permanently",
   302: "Found",
   400: "Bad Request",
   401: "Unauthorized",
   403: "Forbidden",
   404: "Not Found",
   408: "Request Timeout",
   429: "Too Many Requests",
   500: "Internal Server Error",
   503: "Service Unavailable"
}

# Platform Settings
PLATFORM_SETTINGS = {
   "windows": {
       "path_max_length": 260,
       "forbidden_chars": '<>:"/\\|?*',
       "admin_required": True,
       "default_encoding": "utf-8",
       "version_support": {
           "min_version": "10.0",
           "recommended": "10.0.19041"
       }
   },
   "linux": {
       "path_max_length": 4096,
       "forbidden_chars": '/',
       "admin_required": False,
       "default_encoding": "utf-8"
   },
   "darwin": {
       "path_max_length": 1024,
       "forbidden_chars": ':/',
       "admin_required": False,
       "default_encoding": "utf-8"
   }
}

# Error Types
ERROR_TYPES = {
    "network": {
        "connection_lost": "Connection lost during download",
        "timeout": "Connection timed out",
        "dns_error": "Could not resolve hostname"
    },
    "file": {
        "access_denied": "Access denied to file or directory",
        "disk_full": "Insufficient disk space",
        "already_exists": "File already exists",
        "invalid_name": "Invalid filename or path"
    },
    "platform": {
        "windows_version": "Unsupported Windows version",
        "path_too_long": "File path exceeds maximum length"
    }
}

# Retry Strategy
RETRY_STRATEGY = {
    "max_attempts": 5,
    "initial_delay": 1,
    "max_delay": 60,
    "backoff_factor": 2,
    "jitter": True,
    "retry_on_status": [408, 429, 500, 502, 503, 504],
    "retry_on_exceptions": [
        "ConnectionError",
        "Timeout",
        "TooManyRedirects"
    ]
}

# Default Headers
DEFAULT_HEADERS = {
   "User-Agent": f"DownLord",
   "Accept": "*/*",
   "Connection": "keep-alive"
}

def calculate_retry_delay(retries: int) -> float:
   return min(
       RETRY_STRATEGY["initial_delay"] * (RETRY_STRATEGY["backoff_factor"] ** retries),
       RETRY_STRATEGY["max_delay"]
   )

def get_download_headers(existing_size: int = 0) -> Dict:
   headers = DEFAULT_HEADERS.copy()
   if existing_size:
       headers["Range"] = f"bytes={existing_size}-"
   return headers

def extract_filename_from_disposition(disposition: str) -> Optional[str]:
   if 'filename=' in disposition:
       filename_match = re.search(r'filename="([^"]+)"', disposition)
       if not filename_match:
           filename_match = re.search(r'filename\*=UTF-8\'\'([^;]+)', disposition)
       if filename_match:
           return unquote(filename_match.group(1)).strip('"')
   return None