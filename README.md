# DownLord
## Status:
- Release versions mostly work, but need update. The batches for this program may only run on Windows 10. HuggingFace downloads have stopped working.
- Update on the way, conformed to my new structure format, and improved. Huggingface fix attempt will be made.

## File Structure
- Packaged files
```
.\

├── scripts\                # Core application scripts
│   ├── interface.py        # UI and user interaction
│   ├── utility.py          # Download functionality
│   └── temporary.py        # Constants and configurations
├── DownLord-Py.bat        # Windows batch launcher
├── installer.py           # Installation script
├── launcher.py           # Main application entry
├── LICENSE.txt           # License information
└── README.md            # Project documentation
```
- Files created by installer/program.
```
├── data\                     # Data related, Created by installer
│   ├── persistent.json       # persistent settings, Created by installer
│   ├── requirements.txt      # Python requirements, Created by installer
│   └── downlord.log         # Log file, created by main program
├── scripts\                 # Already part of package
│   ├── __init__.py          # to fix scripts in `.\scripts`, created by installer.
├── downloads\               # Default download directory, created by installer
├── temp\                   # Temporary download storage, created by installer
```

## Description
DownLord is a streamlined tool designed for downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption, and automatically maintains a history, removing items from its list when manually deleted from the folder. Unlike browser-based downloads, DownLord ensures that users don't return hours later to find incomplete downloads or accidentally cancel them. It's tailored for substantial downloads rather than smaller files that can be handled by the browser.

## Preview
- Installer is comprehensive...
```
Installing Requirements...

Installing DownLord...
--------------------------------------------------
>> Python version check passed [OK]
>> Platform check passed: windows [OK]
>> Created directory: C:\Program_Filez\Downlord\DownLord-main\data [OK]
>> Created directory: C:\Program_Filez\Downlord\DownLord-main\downloads [OK]
>> Created directory: C:\Program_Filez\Downlord\DownLord-main\scripts [OK]
>> Created directory: C:\Program_Filez\Downlord\DownLord-main\temp [OK]
>> Created scripts/__init__.py [OK]
>> Created requirements.txt [OK]
>> Installed Python dependencies [OK]
>> Created default config [OK]

========================================================================================================================
Installation Complete!
```


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
2. Run the script, using `python main.py` or double click "DownLord.bat".
3. Take a look in the settings menu, make sure everything is optimal.
4. On Main Menu press 0 then enter the URL to download.
5. The file will be downloaded to the `Downloads` directory.
6. Edit folder properties in "DownLord.lnk", for batch launch on taskbar.

## DISCLAIMER
This software is subject to the terms in License.Txt, covering usage, distribution, and modifications. For full details on your rights and obligations, refer to License.Txt..
