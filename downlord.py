import os
import time
from pathlib import Path
import requests
from requests.exceptions import RequestException
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs, unquote
from email.header import decode_header
import json
import cgi

file_path = Path("downloads")
config_file = "config.json"
max_retries = 100  # Maximum number of retries if download fails


def download_file(remote_url, out_path, chunk_size):
    file_name = os.path.basename(out_path)
    existing_file_size = 0  # Initialize existing_file_size to 0

    if Path(out_path).exists():
        # File already exists, check file size
        existing_file_size = os.path.getsize(out_path)
        with requests.head(remote_url) as response:
            remote_file_size = int(response.headers.get('content-length', 0))
            print(f"Existing file size: {existing_file_size}")  # Debug statement
            print(f"Remote file size: {remote_file_size}")      # Debug statement
            print(f"Accept-Ranges: {response.headers.get('Accept-Ranges')}") # Debug statement
        if existing_file_size == remote_file_size:
            print(f"File {file_name} already downloaded.")
            return
        else:
            print(f"Resuming download of {file_name}...")

    retries = 0
    while retries < max_retries:
        try:
            headers = {"Range": f"bytes={existing_file_size}-"}
            print(f"Headers: {headers}")  # Debug statement
            with requests.get(remote_url, stream=True, headers=headers) as response, open(out_path, 'ab') as out_file:
                print(f"Response status code: {response.status_code}") # Debug statement
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                if total_size == 0:
                    print(f"File {file_name} already downloaded.")
                    return
                total_size += existing_file_size
                progress_bar = tqdm(total=total_size, initial=existing_file_size, unit='B', unit_scale=True, desc=f'Downloading {file_name}', bar_format='Downloading {desc}: {percentage:3.0f}% {bar} {n_fmt}/{total_fmt} {elapsed}/{remaining}')
                start_time = time.time()
                downloaded_size = existing_file_size
                for chunk in response.iter_content(chunk_size=chunk_size):
                    out_file.write(chunk)
                    downloaded_size += len(chunk)
                    elapsed_time = time.time() - start_time
                    download_speed = (downloaded_size / elapsed_time) if elapsed_time > 0 else 0

                    hours_elapsed, remainder = divmod(int(elapsed_time), 3600)
                    minutes_elapsed, seconds_elapsed = divmod(remainder, 60)

                    hours_remaining, remainder = divmod(int(total_size - downloaded_size) * elapsed_time / downloaded_size, 3600)
                    minutes_remaining, seconds_remaining = divmod(remainder, 60)

                    progress_bar.set_postfix({'Progress': f"{downloaded_size / (1024**3):.2f}/{total_size / (1024**3):.2f} GB",
                                              'Speed': f"{download_speed:.2f} KB/s",
                                              'Time': f"D{int(hours_elapsed):02d}H{int(minutes_elapsed):02d}M{int(seconds_elapsed):02d}/D{int(hours_remaining):02d}H{int(minutes_remaining):02d}M{int(seconds_remaining):02d}"})
                    progress_bar.update(len(chunk))
                    time.sleep(1)  # Add a delay of 1 second
                progress_bar.close()
                break  # If download is successful, break the retry loop
        except RequestException as e:
            retries += 1
            print(f"An error occurred while downloading: {str(e)}. Retrying ({retries}/{max_retries})...")


def prompt_for_download():
    chunk_sizes = {1: 1024000, 2: 4096000, 3: 8192000}
    print()
    print()
    print("Internet Options:")
    print("-----------------")
    print()
    config = load_config()
    last_chunk_size = config.get("chunk_size", 1024)
    print(f"1. Mobile ~1  MBit/s (Chunk Size 1024KB)")
    print(f"2. Wired  >5  MBit/s (Chunk Size 4096KB)")
    print(f"3. Super >10  MBit/s (Chunk Size 8192KB)")
    print()

    # Determine the default value for chunk size
    default_chunk_size = next((chunk_size for chunk_size in chunk_sizes.values() if chunk_size == last_chunk_size), None)
    if default_chunk_size is not None:
        default_choice = str(next((key for key, value in chunk_sizes.items() if value == default_chunk_size), None))
        prompt_message = f"Enter your internet connection type (Press 1-3, or ENTER for {default_choice}): "
    else:
        prompt_message = "Enter your internet connection type (Press 1-3): "

    while True:
        connection_choice = input(prompt_message)
        if connection_choice == "":
            connection_choice = default_choice

        if connection_choice.isdigit() and int(connection_choice) in chunk_sizes:
            break
        print("Invalid choice. Please try again.")

    url = get_url_input("Enter the URL to download (or 'q' to quit): ", config)

    if url is None:
        print("Quitting...")
        return

    filename = get_file_name_from_url(url)
    if not filename:
        print("Unable to extract filename from the URL. Please try again.")
        return

    out_path = file_path / filename
    download_file(url, out_path, chunk_sizes[int(connection_choice)])

    # Save the last used URL and chunk size to the configuration file
    config["last_url"] = url
    config["chunk_size"] = chunk_sizes[int(connection_choice)]
    save_config(config)


def get_file_name_from_url(url):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if "response-content-disposition" in query_params:
            content_disposition = query_params["response-content-disposition"][0]
            _, params = cgi.parse_header(content_disposition)
            if 'filename*' in params:
                filename = params['filename*'].split("''")[-1]
                print("Detected filename from URL:", unquote(filename))
                print()
                return unquote(filename)
            elif 'filename' in params:
                filename = params['filename']
                print("Detected filename from URL:", unquote(filename))
                print()
                return unquote(filename)
        return os.path.basename(parsed_url.path)
    except Exception as e:
        print("Error extracting filename from the URL:", str(e))
        return None


def get_int_input(message, min_value, max_value):
    while True:
        try:
            value = int(input(message))
            if min_value <= value <= max_value:
                return value
        except ValueError:
            pass
        print("Invalid choice. Please try again.")


def get_url_input(message, config):
    last_url = config.get("last_url", "")
    if last_url:
        message = f"Enter the URL (or press enter for the last used URL: {last_url}): "
    else:
        print()
        message = "Enter the URL to download (or 'q' to quit): "

    while True:
        url = input(message)
        if url.lower() == "q":
            return None
        if not url and last_url:
            print(f"Using last URL: {last_url}")
            return last_url
        if validate_input(url):
            return url
        print("Invalid URL. Please try again.")


def validate_input(url):
    return url.startswith("http")


def load_config():
    if Path(config_file).exists():
        with open(config_file, "r") as file:
            config = json.load(file)
    else:
        config = {}
    return config


def save_config(config):
    with open(config_file, "w") as file:
        json.dump(config, file, indent=4)


def main():
    if not file_path.exists():
        file_path.mkdir(parents=True, exist_ok=True)

    prompt_for_download()


if __name__ == "__main__":
    main()
