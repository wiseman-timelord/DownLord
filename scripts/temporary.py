# .\scripts\temporary.py

from pathlib import Path
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

# Application Metadata
APP_TITLE = "DownLord"
APP_VERSION = "1.2.0"  # Updated version for HuggingFace support
CONFIG_VERSION = "1.2"

# Directory Structure
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = BASE_DIR / "downloads"
SCRIPTS_DIR = BASE_DIR / "scripts"
TEMP_DIR = BASE_DIR / "temp"
BACKUP_DIR = DATA_DIR / "backups"

# File Paths
CONFIG_FILE = DATA_DIR / "config.json"
REQUIREMENTS_FILE = DATA_DIR / "requirements.txt"
LOG_FILE = DATA_DIR / "downlord.log"

# Configuration Defaults
DEFAULT_CHUNK_SIZES = {
    "slow": 1024000,      # ~1MBit/s
    "okay": 4096000,      # ~5MBit/s
    "good": 8192000,      # ~10MBit/s
    "fast": 16384000,     # ~25MBit/s
    "uber": 40960000,     # ~50MBit/s
    "custom": None        # User-defined
}

# Enhanced default configuration
DEFAULT_CONFIG = {
    "version": CONFIG_VERSION,
    "last_updated": datetime.now().isoformat(),
    "download": {
        "chunk_size": DEFAULT_CHUNK_SIZES["okay"],
        "max_retries": 100,
        "timeout": 30,
        "verify_hash": True,
        "parallel_downloads": False,
        "max_parallel": 3,
        "bandwidth_limit": None,  # In bytes per second, None for unlimited
        "auto_resume": True,
        "huggingface": {
            "use_auth": False,
            "token": None,
            "mirror": None,
            "prefer_torch": True
        }
    },
    "storage": {
        "temp_dir": str(TEMP_DIR),
        "download_dir": str(DOWNLOADS_DIR),
        "backup_dir": str(BACKUP_DIR),
        "keep_incomplete": True,
        "organize_by_type": False,
        "auto_extract": False
    },
    "security": {
        "verify_ssl": True,
        "allowed_domains": [],  # Empty means all allowed
        "blocked_extensions": [".exe", ".bat", ".sh", ".dll"],
        "scan_downloads": False,
        "hash_verification": True,
        "hash_algorithm": "sha256"
    },
    "interface": {
        "show_progress": True,
        "show_speed": True,
        "show_eta": True,
        "dark_mode": False,
        "detailed_logging": False,
        "notification_sound": False,
        "progress_bar_style": "tqdm"
    },
    "history": {
        "max_entries": 9,
        "entries": [],
        "auto_clean": True,
        "clean_after_days": 30,
        "track_failed": True
    },
    "platform": {
        "windows_version": None,  # Detected at runtime
        "admin_required": True,
        "path_length_limit": 260,
        "encoding": "utf-8"
    }
}

# File Types and Extensions (Expanded)
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
    "id": "",  # Unique identifier for the download
    "filename": "",
    "url": "",
    "timestamp_start": "",
    "timestamp_end": "",
    "status": "pending",  # pending, downloading, paused, complete, error
    "size": {
        "total": 0,
        "downloaded": 0
    },
    "hash": {
        "type": "sha256",
        "value": ""
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
    "source": "",  # e.g., "huggingface", "direct", etc.
    "metadata": {}  # Additional source-specific metadata
}

# URL Patterns (Expanded with HuggingFace)
URL_PATTERNS = {
    "huggingface": {
        "pattern": r"huggingface.co|hf.co",
        "direct_download": False,
        "requires_auth": False,
        "api_pattern": r"^https://huggingface.co/api/.*",
        "model_pattern": r"^https://huggingface.co/([^/]+/[^/]+)(?:/tree/main)?/?$",
        "file_pattern": r"^https://huggingface.co/([^/]+/[^/]+)/resolve/main/(.+)$",
        "download_headers": {
            "user-agent": f"DownLord/{APP_VERSION}",
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

# HTTP Status Codes and Messages
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

# Platform-specific settings
PLATFORM_SETTINGS = {
    "windows": {
        "path_max_length": 260,
        "forbidden_chars": '<>:"/\\|?*',
        "admin_required": True,
        "default_encoding": "utf-8",
        "version_support": {
            "min_version": "10.0",  # Windows 10
            "recommended": "10.0.19041"  # Windows 10 2004 or later
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

# Error Types and Messages
ERROR_TYPES = {
    "network": {
        "connection_lost": "Connection lost during download",
        "timeout": "Connection timed out",
        "dns_error": "Could not resolve hostname",
        "ssl_error": "SSL certificate verification failed"
    },
    "file": {
        "access_denied": "Access denied to file or directory",
        "disk_full": "Insufficient disk space",
        "already_exists": "File already exists",
        "invalid_name": "Invalid filename or path"
    },
    "auth": {
        "token_invalid": "Invalid authentication token",
        "token_expired": "Authentication token has expired",
        "permission_denied": "Permission denied to resource"
    },
    "platform": {
        "windows_version": "Unsupported Windows version",
        "admin_required": "Administrator privileges required",
        "path_too_long": "File path exceeds maximum length"
    }
}

# Retry Strategy Configuration
RETRY_STRATEGY = {
    "max_attempts": 5,
    "initial_delay": 1,  # seconds
    "max_delay": 60,     # seconds
    "backoff_factor": 2, # exponential backoff multiplier
    "jitter": True,      # add randomness to delay
    "retry_on_status": [408, 429, 500, 502, 503, 504],
    "retry_on_exceptions": [
        "ConnectionError",
        "Timeout",
        "TooManyRedirects"
    ]
}