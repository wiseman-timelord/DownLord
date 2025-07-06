# Script: `.\launcher.py`

# Imports
print("Starting `launcher` Imports.")
import os, sys, time
from pathlib import Path
from typing import Dict

# Set platform from command line argument FIRST
from scripts import temporary
if len(sys.argv) > 1:
    temporary.PLATFORM = sys.argv[1].lower()

# Now import other modules
from scripts.configure import Config_Manager, get_downloads_path, check_environment
from scripts.interface import prompt_for_download, display_error, clear_screen  # Explicitly include clear_screen
from scripts.manage import handle_orphaned_files
from scripts.temporary import DOWNLOADS_DIR, APP_TITLE, BASE_DIR, TEMP_DIR
print("`launcher` Imports Complete.")

# Initialize
def initialize_startup(platform: str) -> Dict:
    """Initialize the application with platform-specific settings"""
    temporary.PLATFORM = platform.lower()
    print(f"Initializing {APP_TITLE} for {temporary.PLATFORM}...")
    
    if not check_environment():
        print("Environment issues detected. Exiting...")
        time.sleep(3)
        sys.exit(1)
        
    config = Config_Manager.load()
    handle_orphaned_files(config)
    
    # Resolve downloads location
    downloads_location_str = config.get("downloads_location", "downloads")
    downloads_path = Path(downloads_location_str)
    if not downloads_path.is_absolute():
        downloads_path = BASE_DIR / downloads_path
    downloads_path = downloads_path.resolve()
    
    try:
        downloads_path.mkdir(parents=True, exist_ok=True)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {str(e)}")
        sys.exit(1)
        
    print("Startup initialization complete.")
    return config

def main():
    """Main application entry point with platform handling"""
    print("Starting DownLord...")
    try:
        if len(sys.argv) > 1:
            platform = sys.argv[1].lower()
            if platform not in ['windows', 'linux']:
                print(f"Warning: Unknown platform '{platform}', defaulting to 'windows'")
                platform = 'windows'
        else:
            platform = 'windows'  # Default
            
        config = initialize_startup(platform)
        if not config:
            display_error("Failed to initialize application")
            time.sleep(3)
            return
            
        prompt_for_download()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        display_error(f"Unexpected error: {str(e)}")
        time.sleep(3)

if __name__ == "__main__":
    main()