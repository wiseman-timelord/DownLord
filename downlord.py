import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from manager import download_file, get_file_name_from_url
import json
import time

file_path = Path("downloads")
config_file = "config.json"


def prompt_for_download():
    config = load_config()
    chunk_sizes = {1: 1024000, 2: 4096000, 3: 8192000, 3: 16384000, 4: 20480000, 3: 40960000}
    last_chunk_size = config.get("chunk", 1024)
    default_chunk_size = next((chunk_size for chunk_size in chunk_sizes.values() if chunk_size == last_chunk_size), None)
    if default_chunk_size is not None:
        default_choice = str(next((key for key, value in chunk_sizes.items() if value == default_chunk_size), None))
        prompt_message = f"Enter your internet connection type (Press 1-5, or ENTER for {default_choice}): "
    else:
        prompt_message = "Enter your internet connection type (Press 1-5): "

    while True:
        display_main_menu(config)
        choice = input().strip()
        if choice.lower() == 's':
            internet_options_menu()
            connection_choice = input(prompt_message)
            if connection_choice == "":
                connection_choice = default_choice
            if connection_choice.isdigit() and int(connection_choice) in chunk_sizes:
                config["chunk"] = chunk_sizes[int(connection_choice)]
                save_config(config)
                continue
            else:
                print("Invalid choice. Please try again.")
                continue

        if choice.isdigit() and 0 <= int(choice) <= 9:
            if int(choice) == 0:
                url = input("\nEnter the URL to download (or 'q' to quit): ")
            else:
                url_key = f"url_{choice}"
                url = config.get(url_key, "")
            if url.lower() == "q":
                print("Quitting...")
                return
            if validate_input(url):
                filename = get_file_name_from_url(url)
                if not filename:
                    print("Unable to extract filename from the URL. Please try again.")
                    continue
                update_config(config, filename, url)
                out_path = file_path / filename
                download_file(url, out_path, config["chunk"])
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
    print("\n\nPress, 0 To Enter A New URL or 1-9 to Continue or s for Setup:")

def internet_options_menu():
    print("\n                        Setup Menu")
    print("                        -=-=--=-=-\n")
    print("           1. Slow  ~1  MBit/s (Chunk Size  1024KB)")
    print("           2. Okay  ~5  MBit/s (Chunk Size  4096KB)")
    print("           3. Good ~10  MBit/s (Chunk Size  8192KB)")
    print("           4. Fast ~25  MBit/s (Chunk Size 20480KB)")
    print("           5. Uber ~50  MBit/s (Chunk Size 40960KB)\n\n")

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
    for i in range(9, 1, -1):
        config[f"filename_{i}"] = config.get(f"filename_{i-1}", "Empty")
        config[f"url_{i}"] = config.get(f"url_{i-1}", "")
    config["filename_1"] = filename
    config["url_1"] = url
    save_config(config)

def load_config():
    try:
        if Path(config_file).exists():
            with open(config_file, "r") as file:
                config = json.load(file)
            # Check for missing files and remove them
            for i in range(1, 10):
                filename_key = f"filename_{i}"
                filename = config.get(filename_key, "Empty")
                if filename != "Empty" and not (file_path / filename).exists():
                    config[filename_key] = "Empty"
                    config[f"url_{i}"] = ""
            return config
        else:
            config = {}
            for i in range(1, 10):
                config[f"filename_{i}"] = "Empty"
                config[f"url_{i}"] = ""
            return config
    except json.JSONDecodeError:
        print("Error reading configuration file. Using default settings.")
        return {}

def save_config(config):
    try:
        with open(config_file, "w") as file:
            json.dump(config, file, indent=4)
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")

def main():
    if not file_path.exists():
        file_path.mkdir(parents=True, exist_ok=True)

    prompt_for_download()

if __name__ == "__main__":
    main()