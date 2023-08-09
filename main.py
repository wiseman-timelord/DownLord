import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from manager import download_file, get_file_name_from_url
from setup import setup_menu, load_config, save_config  # Import setup_menu instead of internet_options_menu
import time

file_path = Path("Downloads")

def prompt_for_download():
    config = load_config()
    while True:
        display_main_menu(config)
        choice = input().strip()
        if choice.lower() == 's':
            setup_menu()
            continue
        if choice.lower() == 'q':
            print("Quitting...")
            return
        if choice.isdigit() and 0 <= int(choice) <= 9:
            if int(choice) == 0:
                url = input("\nEnter the URL to download (or 'q' to quit): ")
                if url.lower() == "q":
                    print("Quitting...")
                    return
            else:
                url_key = f"url_{choice}"
                url = config.get(url_key, "")
            if validate_input(url):
                filename = get_file_name_from_url(url)
                if not filename:
                    print("Unable to extract filename from the URL. Please try again.")
                    continue
                update_config(config, filename, url)
                out_path = file_path / filename
                download_file(url, out_path, config["chunk"])
                print(f"Download complete for file: {filename}")
                continue
        print("Invalid choice. Please try again.")

def display_main_menu(config):
    print("\n\n                           Main Menu")
    print("                           -=-=-=-=-\n")
    print("Recent Downloads:\n")
    for i in range(1, 10):
        filename_key = f"filename_{i}"
        filename = config.get(filename_key, "Empty")
        print(f"    {i}. {filename}")
    print("\n\nPress, 0 for New URL or 1-9 to Continue or s for Setup or q for Quit:")

def validate_input(url):
    return url.startswith("http")

def update_config(config, filename, url):
    existing_entry_index = None
    for i in range(1, 10):
        if config.get(f"filename_{i}") == filename and config.get(f"url_{i}") == url:
            existing_entry_index = i
            break
    if existing_entry_index is not None:
        print(f"Entry for {filename} already exists at position {existing_entry_index}.")
        return

    # Find the first empty slot and update it
    for i in range(1, 10):
        if config.get(f"filename_{i}") == "Empty":
            config[f"filename_{i}"] = filename
            config[f"url_{i}"] = url
            break
    else:
        # If no empty slot found, shift everything down and insert at the top
        for i in range(9, 1, -1):
            config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
            config[f"url_{i}"] = config.get(f"url_{i-1}", "")
        config["filename_1"] = filename
        config["url_1"] = url

    save_config(config)

def main():
    if not file_path.exists():
        file_path.mkdir(parents=True, exist_ok=True)

    prompt_for_download()

if __name__ == "__main__":
    main()