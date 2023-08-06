import os
import time
import requests
from requests.exceptions import RequestException
from tqdm import tqdm
from pathlib import Path

max_retries = 100  # Maximum number of retries if download fails

def download_file(remote_url, out_path, chunk_size):
    file_name = os.path.basename(out_path)
    existing_file_size = 0  # Initialize existing_file_size to 0

    if Path(out_path).exists():
        # File already exists, check file size
        existing_file_size = os.path.getsize(out_path)
        with requests.head(remote_url) as response:
            remote_file_size = int(response.headers.get('content-length', 0))
            print(f"Existing file size: {existing_file_size}")
            print(f"Remote file size: {remote_file_size}")
            print(f"Accept-Ranges: {response.headers.get('Accept-Ranges')}")
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
                progress_bar = tqdm(total=total_size, initial=existing_file_size, unit='B', unit_scale=True, desc=f'', bar_format='{desc}: {percentage:3.0f}% {bar} {n_fmt}/{total_fmt} {elapsed}/{remaining}')
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

def get_file_name_from_url(url):
    from urllib.parse import urlparse, parse_qs, unquote
    import cgi
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
