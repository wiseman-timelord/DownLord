# DownLord

## Description
DownLord is a robust and user-friendly tool that allows users to download files from URLs. It provides options to select different internet connection speeds, supports download resumption, and retains the last used URL and chunk size in a configuration file. Primary purpose, to download language models on bad connections, and not, return hours later to find only a tiny bit downloaded or double click retry to accidentally cancel the download. 

## Features
- Connection Speed Selection - Choose from Mobile, Wired, or Super-fast connection speeds.
- Download Resumption - If a download is interrupted, it can be resumed from where it left off.
- Configuration Persistence - The last used URL and chunk size are saved in a configuration file for convenience.
- Reading of complex URLs such as found on hugging face download, to correctly obtain filenames.

INTERFACE:
Output looks like this...

```

                           Main Menu
                           -=-=-=-=-

Recent Downloads:

    1. Empty
    2. Empty
    3. Empty
    4. Empty
    5. Empty
    6. Empty
    7. Empty
    8. Empty
    9. Empty


Press, 0 for New URL or 1-9 to Continue or s for Setup or q for Quit:

```

## Requirements
- Python 3.x
- `requests` library
- `tqdm` library

## Usage
1. Clone the repository or download the script.
2. Run the script, using `python download.py` or double click "DownLord.bat".
3. Follow the prompts to select your internet connection type and enter the URL to download.
4. The file will be downloaded to the `downloads` directory.

## Disclaimer
Its a downloader, I don't know...don't use it to download things you should not be downloading in your country, or the boogyman will hackcually gechu! *serious look*
