# DownLord
## Status: Beta
- Revisited 2025/02. Improved, Fixed, and Upgraded, but there are still issues...
1. It messed up the download, now testing the fix for this.
2. During initialize download, if I resume by selecting a menu item, but the link is dead, then it will delete the file and wipe the relevant item. it should instead ask the user if they wish to delete the item or try another url, and if they enter a new url, then it needs to try that one, and clear the screen and start over with the initialize download this time with the new url. but if it doesnt work again, then once again prompt the user `Selection; Delete the Download = D or Enter alternate URL = 0:`.
3. Initiate download text looks like this...
```
Initializing download sequence...
Processing URL...
Extracting filename...
Found file: unsloth.Q4_K_M.gguf

Checking for existing downloads...
Found incomplete previous download, will resume...
Resuming from: 54.69 MB
```
...it needs to be more like this...
```
Initializing download sequence...
Extracting filename...
Found file: unsloth.Q4_K_M.gguf
Found incomplete download, resuming...
Resuming from: 54.69 MB
```
...so as to be reporting rather than announcing actions.
4. The code needs, optimization and re-distributing, maybe this will be for the next revisit.

- Features needing testing...
1. Setup menu.
2. Platforms other than huggingface.

## Description
DownLord is a streamlined tool designed for downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption, and automatically maintains 9 slots, removing items from its list when manually moved from the downloads folder to its intended folder. Unlike browser-based downloads, DownLord ensures that dpwnloads continue until they are done. It's tailored for substantial downloads, where, the browser may fail due to connecting on a bad line, and lfs would otherwise produce little/no information, such as ETA. The downloads are registered in up to 9 slots, when the downloads are complete, they appear in the downloads folder, and the user may move them to their intended destination. The program remembers the url, so as for the user to be able to continue incomplete downloads, resuming when possible. 

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
2     nsfw-i-hate-my-life-v2.Q6_K.gguf    75.3%        4.62 GB/6.14 GB
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
- Initializing Download, after insert URL...
```
===============================================================================
    DownLord: Initiate Download
===============================================================================

Initializing download sequence...
Processing URL...
Extracting filename...
Found file: unsloth.Q4_K_M.gguf

Checking for existing downloads...
Found incomplete previous download, will resume...
Resuming from: 54.69 MB

Establishing connection...
Connecting to server...
C:\Users\mastar\AppData\Local\Programs\Python\Python311\Lib\site-packages\urllib3\connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'cdn-lfs-us-1.hf.co'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
  warnings.warn(

Starting download of unsloth.Q4_K_M.gguf...

```
- Download screen is like this...
```
===============================================================================
    DownLord: Download Active
===============================================================================

Filename:
    unsloth.Q4_K_M.gguf

Progress:
    1.5%

Speed:
    495.26 KB/s

Receive/Total:
    70.31 MB/4.58 GB

Elapse/Remain:
    00:00:30<02:39:17


```
- Installer is comprehensive...
```
===============================================================================
    DownLord: Install
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
1. Clone the repository or download the release/pre-release then unpack, to a suitable location, ie `C:\Program_Files\DownLord`.
2. Run the batch by right click then `Run As Administrator` on `DownLord.bat`.
3. Select the Installer option, to, install python requirements and unpack/create program files.

### Usage
1. Run the script "DownLord.bat", and press 1 to launch main program.
2. Take a look in the settings menu, make sure everything is optimal.
3. On Main Menu press 0 then enter the URL to download, ensure it is a working URL.
4. The complete download will be in `.\downloads`, move completed files out.

## Notation
- Its intended as a better solution to downloading GGUF files from Huggingface, other download options are untested, and suggested "improvements" from the ai.
- Sometimes such as on Huggingface, the user must start the download in browser, then copy the link from the download manager in browser (not the page), then paste that as URL for DownLord. This is because of the design of the website.


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
