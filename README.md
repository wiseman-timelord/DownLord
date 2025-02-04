# DownLord
## Status: Beta
- Re-visited 2025/02/03 - Fixed huggingface links, overhauled and upgraded, elsewhere. There is a problem with registering the downloads, this was due to duplicate jsons, this is being worked on. 1 session from completion.

## Description
DownLord is a streamlined tool designed for downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption, and automatically maintains a history, removing items from its list when manually deleted from the folder. Unlike browser-based downloads, DownLord ensures that users don't return hours later to find incomplete downloads or accidentally cancel from unresponsive resume action. It's tailored for substantial downloads, where, the browser may fail and lfs produce little/no information.

### Preview
- Launcher is downloading compitently...
```
===============================================================================
          ________                      .____                    .___
          \______ \   ______  _  ______ |    |    ___________  __| _/
           |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |
           |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |
          /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |
                  \/                  \/        \/                \/
-------------------------------------------------------------------------------
    Main Menu
===============================================================================

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

Selection; New URL = 0, Continue = 1-9, Setup = S, Quit = Q: 0
Selection; Enter URL or Q to Quit: https://cdn-lfs-us-1.hf.co/repos...Key-Pair-Id=K############
deepseek-r1-distill-... .gguf:   0%, 11.7M/11.3G [00:31<8:03:08, 418kB/s]
```
- Batch Launcher/Installer Menu...
```
===============================================================================
"         ________                      .____                    .___         "
"         \______ \   ______  _  ______ |    |    ___________  __| _/         "
"          |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |          "
"          |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |          "
"         /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |          "
"                 \/                  \/        \/                \/          "
-------------------------------------------------------------------------------
    Batch Menu
===============================================================================




    1. Launch DownLord

    2. Install Requirements




===============================================================================
Selection; Options = 1-2, Exit = X:
```
- Installer is comprehensive...
```
===============================================================================
"         ________                      .____                    .___         "
"         \______ \   ______  _  ______ |    |    ___________  __| _/         "
"          |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |          "
"          |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |          "
"         /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |          "
"                 \/                  \/        \/                \/          "
-------------------------------------------------------------------------------
    DownLord Install
===============================================================================
>> Python version check passed [OK]
>> Platform check passed: windows [OK]
>> Checked directory: .\data [OK]
>> Checked directory: .\downloads [OK]
>> Checked directory: .\scripts [OK]
>> Checked directory: .\temp [OK]
>> Created .\scripts\__init__.py [OK]
>> Created .\data\requirements.txt [OK]
>> Installed Python dependencies [OK]
Persistence file already exists at: C:\Program_Filez\Downlord\DownLord-main\data\persistent.json
Do you want to overwrite it? (y/n): y
>> Created default persistent [OK]
Press Enter to exit...
```


### Features
- Connection Speed Selection - Choose from speeds of 1MB/s, 5MB/s, 10MB/s, 25MB/s or 50MB/s.
- Download Resumption - If a download is interrupted, it can be resumed from where it left off.
- Setup Menu - Configure connection speed, maximum retries, and download settings.
- Reading of complex URLs such as found on hugging face download, to correctly obtain filenames.
- Configuration Persistence - The last used, URLs and settings, are saved in a configuration file.
- Platform support - HuggingFace, Google Drive, Dropbox, GitHub, Direct HTTP/HTTPS.

## Requirements
- Windows 7-10 
- Python 3.6-3.11
- Internet and URL to download.

### Usage
1. Clone the repository or download the script.
2. Run the script "DownLord.bat".
3. Select the Installer, to install requirements and setup files.
4. After install has finished, return to the menut, then press 1 to launch main program.
5. Take a look in the settings menu, make sure everything is optimal.
4. On Main Menu press 0 then enter the URL to download.
5. The file will be downloaded to the `Downloads` directory.

### File Structure
- Packaged files
```
├── DownLord.bat          # Batch menu installer/launcher
├── installer.py           # Installation script
├── launcher.py           # Main application entry
├── LICENSE.txt           # License information
└── README.md            # Project documentation
├── scripts\                # Core application scripts
│   ├── interface.py        # UI and user interaction
│   ├── utility.py          # Download functionality
│   └── temporary.py        # Constants and configurations
```
- Files created by installer/program.
```
├── downloads\               # Default download directory, created by installer
├── temp\                   # Temporary download storage, created by installer
├── data\                     # Data related, Created by installer
│   ├── persistent.json       # persistent settings, Created by installer
│   ├── requirements.txt      # Python requirements, Created by installer
│   └── downlord.log         # Log file, created by main program
├── scripts\                 # Already part of package
│   ├── __init__.py          # to fix scripts in `.\scripts`, created by installer.
```

## DISCLAIMER
This software is subject to the terms in License.Txt, covering usage, distribution, and modifications. For full details on your rights and obligations, refer to License.Txt..
