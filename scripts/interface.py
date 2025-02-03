# .\scripts\interface.py

import json
import os
from pathlib import Path
from typing import Dict, Optional, Union
from scripts.temporary import (
    CONFIG_FILE,
    DOWNLOADS_DIR,
    DEFAULT_CONFIG,
    DEFAULT_CHUNK_SIZES,
    APP_TITLE,
    ERROR_TYPES
)

# ASCII Art
ASCII_LOGO = '''===============================================================================
          ________                      .____                    .___
          \______ \   ______  _  ______ |    |    ___________  __| _/
           |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ | 
           |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ | 
          /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ | 
                  \/                  \/        \/                \/ 
-------------------------------------------------------------------------------
    %s
==============================================================================='''

# Menu Templates
MENU_SEPARATOR = "-" * 80

MAIN_MENU = """
Recent Downloads:"""

MAIN_MENU_FOOTER = """
Selection; New URL = 0, Continue = 1-9, Setup = S, Quit = Q: """

SETUP_MENU = """
    1. Connection Speed
    2. Maximum Retries
    3. Security Settings
    4. Return to Main

"""

SPEED_MENU = """
            1. Slow  ~1MBit/s (Chunk Size  1024KB)
            2. Okay  ~5MBit/s (Chunk Size  4096KB)
            3. Good ~10MBit/s (Chunk Size  8192KB)
            4. Fast ~25MBit/s (Chunk Size 20480KB)
            5. Uber ~50MBit/s (Chunk Size 40960KB)

"""

SECURITY_MENU = """
                1. Toggle SSL Verification
                2. Toggle Hash Verification
                3. Manage Blocked Extensions
                4. HuggingFace Authentication
                5. Return to Setup

"""

# Error Messages
ERROR_MESSAGES = {
    "invalid_choice": "Invalid choice. Please try again.",
    "invalid_url": "Invalid URL. Please enter a valid URL starting with http:// or https://",
    "download_error": "An error occurred while downloading: {}. Retrying ({}/{})",
    "config_error": "Error reading configuration file. Using default settings.",
    "save_config_error": "Error saving configuration: {}",
    "filename_error": "Unable to extract filename from the URL. Please try again.",
    "invalid_number": "Invalid input. Please enter a number.",
    "hash_mismatch": "File hash verification failed. File may be corrupt.",
    "resume_error": "Cannot resume download. Starting from beginning.",
    "auth_error": "Authentication failed. Please check your credentials."
}

# Success Messages
SUCCESS_MESSAGES = {
    "config_updated": "Configuration updated successfully.",
    "download_complete": "Download complete for file: {}",
    "retries_updated": "Maximum retries updated successfully.",
    "connection_updated": "Connection speed updated successfully.",
    "hash_verified": "File integrity verified successfully.",
    "resume_success": "Resuming download from {} bytes",
    "auth_success": "Authentication configured successfully."
}

def clear_screen(title="Main Menu"):
    """Clear the screen and display the logo with dynamic title."""
    print("\033[H\033[J", end="")  # ANSI escape sequence for clear screen
    print(ASCII_LOGO % title)

def display_separator():
    """Display a menu separator line."""
    print(MENU_SEPARATOR)

def display_main_menu(config: Dict):
    """Display the main menu with download history."""
    clear_screen("Main Menu")
    print(MAIN_MENU)
    
    # Display download history
    for i in range(1, 10):
        filename_key = f"filename_{i}"
        filename = config.get(filename_key, "Empty")
        print(f"    {i}. {filename}")
    
    print(MAIN_MENU_FOOTER, end='')

def setup_menu():
    """Display and handle the setup menu."""
    while True:
        clear_screen("Setup Menu")
        print(SETUP_MENU)
        choice = input("Selection; Options = 1-4, Return = B: ").strip().lower()
        
        if choice == '1':
            internet_options_menu()
        elif choice == '2':
            max_retries_menu()
        elif choice == '3':
            security_menu()
        elif choice == 'b':
            return
        else:
            print(ERROR_MESSAGES["invalid_choice"])
            input("\nPress Enter to continue...")

def security_menu():
    """Handle security settings menu."""
    config = load_config()
    
    while True:
        clear_screen("Security Settings")
        print(SECURITY_MENU)
        
        ssl_status = "Enabled" if config["security"]["verify_ssl"] else "Disabled"
        hash_status = "Enabled" if config["security"]["hash_verification"] else "Disabled"
        print(f"\nCurrent Settings:")
        print(f"SSL Verification: {ssl_status}")
        print(f"Hash Verification: {hash_status}")
        
        choice = input("\nSelection; Options = 1-5, Return = B: ").strip().lower()
        
        if choice == '1':
            config["security"]["verify_ssl"] = not config["security"]["verify_ssl"]
            save_config(config)
            print(SUCCESS_MESSAGES["config_updated"])
        elif choice == '2':
            config["security"]["hash_verification"] = not config["security"]["hash_verification"]
            save_config(config)
            print(SUCCESS_MESSAGES["config_updated"])
        elif choice == '3':
            manage_blocked_extensions(config)
        elif choice == '4':
            configure_huggingface_auth(config)
        elif choice == 'b':
            return
        else:
            print(ERROR_MESSAGES["invalid_choice"])
        
        input("\nPress Enter to continue...")

def configure_huggingface_auth(config: Dict):
    """Configure HuggingFace authentication settings."""
    clear_screen("HuggingFace Authentication")
    print("\nCurrent Status:", "Enabled" if config["download"]["huggingface"]["use_auth"] else "Disabled")
    
    choice = input("\nSelection; Enable Auth = Y, Disable = N, Return = B: ").strip().lower()
    
    if choice == 'y':
        token = input("Enter your HuggingFace token (or press Enter to skip): ").strip()
        if token:
            config["download"]["huggingface"]["use_auth"] = True
            config["download"]["huggingface"]["token"] = token
            save_config(config)
            print(SUCCESS_MESSAGES["auth_success"])
        else:
            config["download"]["huggingface"]["use_auth"] = False
            config["download"]["huggingface"]["token"] = None
            save_config(config)
            print("Authentication disabled.")
    elif choice == 'n':
        config["download"]["huggingface"]["use_auth"] = False
        config["download"]["huggingface"]["token"] = None
        save_config(config)
        print("Authentication disabled.")
    elif choice == 'b':
        return
    else:
        print(ERROR_MESSAGES["invalid_choice"])
    
    input("\nPress Enter to continue...")

def manage_blocked_extensions(config: Dict):
    """Manage blocked file extensions."""
    while True:
        clear_screen("Blocked Extensions")
        print("\nCurrently blocked extensions:")
        for i, ext in enumerate(config["security"]["blocked_extensions"], 1):
            print(f"{i}. {ext}")
        
        print("\nOptions:")
        print("1. Add extension")
        print("2. Remove extension")
        print("3. Return to Security Menu")
        
        choice = input("\nSelection; Options = 1-3, Return = B: ").strip().lower()
        
        if choice == '1':
            ext = input("Enter extension to block (include dot, e.g. '.exe'): ").strip()
            if ext and ext not in config["security"]["blocked_extensions"]:
                config["security"]["blocked_extensions"].append(ext)
                save_config(config)
                print(SUCCESS_MESSAGES["config_updated"])
        elif choice == '2':
            idx = input("Enter number of extension to remove: ").strip()
            try:
                idx = int(idx) - 1
                if 0 <= idx < len(config["security"]["blocked_extensions"]):
                    del config["security"]["blocked_extensions"][idx]
                    save_config(config)
                    print(SUCCESS_MESSAGES["config_updated"])
            except ValueError:
                print(ERROR_MESSAGES["invalid_number"])
        elif choice == '3' or choice == 'b':
            return
        else:
            print(ERROR_MESSAGES["invalid_choice"])
        
        input("\nPress Enter to continue...")

def internet_options_menu():
    """Display and handle the internet speed options menu."""
    config = load_config()
    clear_screen("Connection Speed")
    print(SPEED_MENU)
    connection_choice = input("Selection; Speed = 1-5, Return = B: ").strip().lower()

    if connection_choice == 'b':
        return

    chunk_sizes = {
        "1": DEFAULT_CHUNK_SIZES["slow"],
        "2": DEFAULT_CHUNK_SIZES["okay"],
        "3": DEFAULT_CHUNK_SIZES["good"],
        "4": DEFAULT_CHUNK_SIZES["fast"],
        "5": DEFAULT_CHUNK_SIZES["uber"]
    }

    if connection_choice in chunk_sizes:
        config["download"]["chunk_size"] = chunk_sizes[connection_choice]
        save_config(config)
        print(SUCCESS_MESSAGES["connection_updated"])
    else:
        print(ERROR_MESSAGES["invalid_choice"])
    
    input("\nPress Enter to continue...")

def max_retries_menu():
    """Display and handle the maximum retries menu."""
    config = load_config()
    clear_screen("Maximum Retries")
    print(f"\nCurrent Maximum Retries: {config['download']['max_retries']}\n")
    
    retries = input("Selection; Enter Number or Back = B: ").strip().lower()
    
    if retries == 'b':
        return

    try:
        retries = int(retries)
        if retries > 0:
            config["download"]["max_retries"] = retries
            save_config(config)
            print(SUCCESS_MESSAGES["retries_updated"])
        else:
            print(ERROR_MESSAGES["invalid_number"])
    except ValueError:
        print(ERROR_MESSAGES["invalid_number"])
    
    input("\nPress Enter to continue...")

def display_download_prompt() -> str:
    """Display the download URL prompt."""
    return input("Selection; Enter URL or Q to Quit: ")

def print_progress(message: str):
    """Print a progress message."""
    print(f">> {message}")

def load_config() -> Dict:
    """Load configuration from file."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as file:
                config = json.load(file)
                
            # Validate download history
            entries = []
            for i in range(1, 10):
                filename = config.get(f"filename_{i}", "Empty")
                url = config.get(f"url_{i}", "")
                if filename != "Empty" and (DOWNLOADS_DIR / filename).exists():
                    entries.append((filename, url))

            # Fill remaining slots
            while len(entries) < 9:
                entries.append(("Empty", ""))

            # Update config
            for i, (filename, url) in enumerate(entries, 1):
                config[f"filename_{i}"] = filename
                config[f"url_{i}"] = url

            save_config(config)
            return config
        return create_default_config()
    except json.JSONDecodeError:
        print(ERROR_MESSAGES["config_error"])
        return create_default_config()

def create_default_config() -> Dict:
    """Create a new default configuration."""
    config = DEFAULT_CONFIG.copy()
    for i in range(1, 10):
        config[f"filename_{i}"] = "Empty"
        config[f"url_{i}"] = ""
    save_config(config)
    return config

def save_config(config: Dict) -> bool:
    """Save configuration to file."""
    try:
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)
        return True
    except Exception as e:
        print(ERROR_MESSAGES["save_config_error"].format(str(e)))
        return False

def display_error(message: str):
    """Display an error message."""
    print(f"Error: {message}")

def display_success(message: str):
    """Display a success message."""
    print(f"Success: {message}")

def update_history(config: Dict, filename: str, url: str) -> None:
    """Update the download history in config."""
    # Check if entry already exists
    for i in range(1, 10):
        filename_key = f"filename_{i}"
        url_key = f"url_{i}"
        if config.get(filename_key) == filename and config.get(url_key) == url:
            return  # Entry already exists

    # Shift entries down and add new entry at top
    for i in range(9, 1, -1):
        config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
        config[f"url_{i}"] = config.get(f"url_{i-1}", "")
    
    config["filename_1"] = filename
    config["url_1"] = url
    save_config(config)