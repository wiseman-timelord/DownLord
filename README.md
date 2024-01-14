# DownLord-Py
## Status:
Working(ish). The batches for this program may only run on Windows 10 due to the different PowerShell launch commands required for various OS versions, that microsoft have bizarly chosen to use for each OS, and may cause endless launch loop on other systems.
* HuggingFace downloads have stopped working. Currently priority is my other repositry Llama2Robot. Will need to investigate later, currently priority is Llama2Robot.

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

### DISCLAIMER
Read "License.Txt", its, what its there for and why its supplied with the package.
