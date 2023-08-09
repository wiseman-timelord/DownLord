# DownLord

## Description
DownLord is a robust and user-friendly tool that allows users to download files from URLs. It provides options to select different internet connection speeds, supports download resumption, and retains the last used URL and chunk size in a configuration file. Primary purpose, to download language models on bad connections, and not, return hours later to find only a tiny bit downloaded or double click retry to accidentally cancel the download. 

## Features
- Connection Speed Selection - Choose from speeds of 1MB/s, 5MB/s, 10MB/s, 25MB/s or 50MB/s.
- Download Resumption - If a download is interrupted, it can be resumed from where it left off.
- Setup Menu - Configure connection speed, maximum retries, and download settings.
- Reading of complex URLs such as found on hugging face download, to correctly obtain filenames.
- Configuration Persistence - The last used, URLs and settings, are saved in a configuration file.

## INTERFACE
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
- Python 2.6-3.11

## Usage
1. Clone the repository or download the script.
2. Run the script, using `python download.py` or double click "DownLord.bat".
3. Follow the prompts to select your internet connection type and enter the URL to download.
4. The file will be downloaded to the `downloads` directory.

## Disclaimer
"DownLord" is provided "as is," and the creators make no warranties regarding its use. Users are solely responsible for the content they download and any potential damages to their equipment. The use of "DownLord" for unauthorized activities is strictly at the user's own risk, and all legal responsibilities lie with the user.
