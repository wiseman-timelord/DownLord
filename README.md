# DownLord
## Status: Beta
- Re-visiting 2025/02 - It is now as shown in the previews, but there is just a little more updating. Here is the remaining/current work...
1. its supposed to register the download in a slot, after downloading the first 1%, so as for the item to be shown on the menu as an incomplete download for the user to continue, should the program somehow close. currently if I terminate the window during download, then in the json there only the total size, but no filename or url, for the download. When I select 0 to enter a new url, and provide the same url, it does seem to be able to resume from the relating file in temp. After starting the download it needs to save, filename and url and the total size of the download, then on the menu the current size of the file is compared to the total size of download detailed in the json, to be able to display, filename, % complete, total size, on the menu. The user will be able to continue incomplete downloads, but files that are already compelte are, not able to be resumed and are automatically moved to the downloads folder, so if there is no relating `*.part` file, then it should check the downloads folder for the full file, and print the download is already compelte, and obviously if the file is in neither place then there is some kind of issue. The default Json was updated to contain, filename, url, total size, having removed the unneccessary % compelte; it can be worked out by comparing the, current and total, filesize.

## Description
DownLord is a streamlined tool designed for downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption, and automatically maintains 9 slots, removing items from its list when manually moved from the downloads folder to its intended folder. Unlike browser-based downloads, DownLord ensures that dpwnloads continue until they are done. It's tailored for substantial downloads, where, the browser may fail due to connecting on a bad line, and lfs would otherwise produce little/no information, such as ETA. The downloads are registered in up to 9 slots, when the downloads are complete, they appear in the downloads folder, and the user may move them to their intended destination. The program remembers the url, so as for the user to be able to continue incomplete downloads, resuming where possible. 

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
#     Filename                            Progress     Size
---------------------------------------------------------------------------
1     nsfw-i-hate-my-life-v2.Q3_K_M.gguf  100.0%       3.74 GB
2     Empty                               -            -
3     Empty                               -            -
4     Empty                               -            -
5     Empty                               -            -
6     Empty                               -            -
7     Empty                               -            -
8     Empty                               -            -
9     Empty                               -            -
===============================================================================
Selection; New URL = 0, Continue = 1-9, Delete = D, Setup = S, Quit = Q:

```
- Download screen is like this...
```
===============================================================================
          ________                      .____                    .___
          \______ \   ______  _  ______ |    |    ___________  __| _/
           |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |
           |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |
          /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |
                  \/                  \/        \/                \/
-------------------------------------------------------------------------------
    Download Active
===============================================================================

Filename:
    nsfw-i-hate-my-life-v2.Q6_K.gguf
Progress:
    2.9%
Speed:
    547.97 KB/s
Receive/Total:
    179.69 MB/6.14 GB
Elapse/Remain:
    00:00:48<03:10:19

===============================================================================

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
Json already exists: .\data\persistent.json
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
- Windows 7-10, testing is done on 10.
- Python 3.6-3.11, 3.11 recommended.
- Internet Connection and a URL to download.

### Install
1. Clone the repository or download the script.
2. Run the script "DownLord.bat".
3. Select the Installer, to install requirements and setup files.

### Usage
1. Run the script "DownLord.bat", and press 1 to launch main program.
2. Take a look in the settings menu, make sure everything is optimal.
3. On Main Menu press 0 then enter the URL to download, ensure it us a working URL.
4. The complete download will be in `.\downloads`, move completed files out.

## Notation
- Its intended to be the best method of downloading GGUF files from Huggingface, other download options will have limited testing. 

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
├── data\                     # Data related, Created by installer
│   ├── persistent.json       # persistent settings, Created by installer
│   ├── requirements.txt      # Python requirements, Created by installer
│   └── downlord.log         # Log file, created by main program
│   └── temp\                 # Storage of incomplete downloads
├── scripts\                 # Already part of package
│   ├── __init__.py          # to fix scripts in `.\scripts`, created by installer.
```

## DISCLAIMER
This software is subject to the terms in License.Txt, covering usage, distribution, and modifications. For full details on your rights and obligations, refer to License.Txt..
