# Python Download Manager

## Description
Python Download Manager is a robust and user-friendly tool that allows users to download files from URLs. It provides options to select different internet connection speeds, supports download resumption, and retains the last used URL and chunk size in a configuration file. Primary purpose, to download language models on bad connections, and not return hours later to find only a tiny bit downloaded. 

## Features
- **Connection Speed Selection**: Choose from Mobile, Wired, or Super-fast connection speeds.
- **Download Resumption**: If a download is interrupted, it can be resumed from where it left off.
- **Configuration Persistence**: The last used URL and chunk size are saved in a configuration file for convenience.

## Requirements
- Python 3.x
- `requests` library
- `tqdm` library

## Usage
1. Clone the repository or download the script.
2. Run the script using `python download.py`.
3. Follow the prompts to select your internet connection type and enter the URL to download.
4. The file will be downloaded to the `downloads` directory.

## Configuration
The configuration file `config.json` stores the last used URL and chunk size. You can manually edit this file if needed.
