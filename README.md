# DownLord
## Status: Beta
- Revisited 2025/02. Improved, Fixed, and Upgraded.

## Description
DownLord is a more personal approach to downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption. The program automatically maintains 9 slots, removing items from its list when, manually moved from the downloads folder or selected to be deleted. Unlike browser-based downloads, DownLord ensures that dpwnloads continue until complete. It's tailored for substantial downloads on a bad line, and where the best alternative `lfs` would otherwise produce no progress information. The program remembers the url, so as for the user to be able to continue incomplete downloads, resuming where possible. 

### Preview
- Main menu...
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
- Download display...
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
- Setup menu is functional...
```
===============================================================================
    DownLord: Setup Menu
===============================================================================






    1. Connection Speed       (2.5Mbps)

    2. Maximum Retries        (100)

    3. Screen Refresh         (2s)

    4. Downloads Location     (C:\Program_Filez\DownLord\DownLord-v0.18\downloads)





===============================================================================
Selection; Options = 1-4, Return = B:
```
- Installation processes...
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
- Download Resumption - If a download is interrupted, it can be resumed from where it left off.
- Setup Menu - Configure maximum retries, and chunk speeds suited for, Sub1MB, Mobile, Line, Fibre.
- Reading of complex URLs such as on hugging face downloads, while correctly obtaining filenames.
- Configuration Persistence - Recent, URLs and settings, are saved in a Json configuration file.
- Platform support - HuggingFace, Google Drive, Dropbox, GitHub, Direct HTTP/HTTPS.

## Requirements
- Windows 7-10, testing is done on 10.
- Python 3.6-3.11, 3.11 recommended.
- Internet Connection and a URL to download.

### Install
1. Clone the repository or download the release/pre-release then unpack, to a suitable location, ie `C:\Program_Files\DownLord` or `C:\Programs\Downlord`, (generally you should not install github projects to locations with spaces such as `Program Files`).
2. Run the batch by right click then `Run As Administrator` on `DownLord.bat`. 
3. Select the Installer option, to, install python requirements and unpack/create program files.

### Usage
1. Run the script "DownLord.bat", and press 1 to launch main program.
2. Take a look in the settings menu, make sure everything is optimal.
3. On Main Menu press 0 then enter the URL to download, ensure it is a working URL.
4. The complete download will be in `.\downloads`, move completed files out.

### Notation
- It works for regular larger http/https download, but but its made it for downloading GGUF files from Huggingface, otherwise done on, browser or `lfs`. Currently untested on pladforms such as GoogleDrive, etc, it likely wont work with every format of url.
- On sites such as Huggingface, the user starts the download in browser, then copy the link from the download manager in browser (not the one from the page), then use that for the download URL. This is because of the design of the website.
- On a slow connection DownLord will hog the bandwidth, this is deemed to be optimal to the task. Try playing the offline games, such as, `RimWorld` or `Fallout 4`, while you wait, that are especially good with my mod(s) found on the Nexus under the same UserName. 

## Development
- After the `Revisit`, the code now needs a going over, such as, optimization, and also code logically re-distributing among scripts in the optimal method, mainly, manager script is light, maybe we can shift some relevantly themed functions over.

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
