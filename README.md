# DownLord-Py
Status: Working
* HuggingFace downloads have stopped working, will need to investigate, currently priority is Llama2Robot.

## Description
DownLord-Py is a streamlined tool designed for downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption, and automatically maintains a history, removing items from its list when manually deleted from the folder. Unlike browser-based downloads, DownLord-Py ensures that users don't return hours later to find incomplete downloads or accidentally cancel them. It's tailored for substantial downloads rather than smaller files that can be handled by the browser.

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
- Internet connection
- URL linked to file

## Usage
1. Clone the repository or download the script.
2. Run the script, using `python main.py` or double click "DownLord-Py.bat".
3. Take a look in the settings menu, make sure everything is optimal.
4. On Main Menu press 0 then enter the URL to download.
5. The file will be downloaded to the `Downloads` directory.
6. Edit folder properties in "DownLord-Py.lnk", for batch launch on taskbar.

## Disclaimer
"DownLord-Py" is provided "as is," and the creators make no warranties regarding its use. Users are solely responsible for the content they download and any potential damages to their equipment. The use of "DownLord-Py" for unauthorized activities is strictly at the user's own risk, and all legal responsibilities lie with the user.
