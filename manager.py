import os
import time
import requests
from requests.exceptions import RequestException
from tqdm import tqdm
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import cgi

max_retries = 100

def download_file(remote_url, out_path, chunk_size):
    file_name = get_file_name_from_url(remote_url)
    existing_file_size = 0

    if Path(out_path).exists():
        existing_file_size = os.path.getsize(out_path)

    retries = 0
    while retries < max_retries:
        try:
            headers = {"Range": f"bytes={existing_file_size}-"} if existing_file_size else {}
            with requests.get(remote_url, stream=True, headers=headers) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0)) + existing_file_size
                with open(out_path, 'ab') as out_file, tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as progress_bar:
                    progress_bar.update(existing_file_size)  # Update the progress bar with the existing file size
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        out_file.write(chunk)
                        progress_bar.update(len(chunk))
                break
        except RequestException as e:
            retries += 1
            print(f"An error occurred while downloading: {str(e)}. Retrying ({retries}/{max_retries})...")

def get_file_name_from_url(url):
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Handle content-disposition header
        if "response-content-disposition" in query_params:
            content_disposition = query_params["response-content-disposition"][0]
            _, params = cgi.parse_header(content_disposition)
            if 'filename*' in params:
                filename = params['filename*'].split("''")[-1]
                return unquote(filename)
            elif 'filename' in params:
                filename = params['filename']
                return unquote(filename)
        
        # Handle Google Drive URLs
        if "format=" in url and "docs.google.com" in url:
            filename = parsed_url.path.split('/')[-1] + query_params.get("format")[0]
            return unquote(filename)
        
        # Handle Dropbox URLs
        if "www.dropbox.com" in url and "dl=1" in url:
            return os.path.basename(parsed_url.path)
        
        # Handle YouTube URLs
        if "www.youtube.com" in url:
            video_id = query_params.get("v")[0]
            return f"youtube_{video_id}.mp4"

        # Handle Vimeo URLs
        if "vimeo.com" in url:
            return os.path.basename(parsed_url.path) + ".mp4"

        # Handle URLs with filename in the path
        filename = os.path.basename(parsed_url.path)
        return unquote(filename)

    except Exception as e:
        print("Error extracting filename from the URL:", str(e))
        return None

