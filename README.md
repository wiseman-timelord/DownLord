# DownLord
```
===============================================================================
"         ________                      .____                    .___         "
"         \______ \   ______  _  ______ |    |    ___________  __| _/         "
"          |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |          "
"          |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |          "
"         /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |          "
"                 \/                  \/        \/                \/          "
===============================================================================
```
## Status: Beta
- Most recent versions are Working, but currently being made compatible with both linux and windows.  

## Description
DownLord is a more dedicated approach to downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption. The program automatically maintains 9 slots, auto-removing items from its list when, manually moved from the downloads folder or selected to be deleted. Unlike browser-based downloads, DownLord ensures that dpwnloads continue until complete. It's tailored for substantial downloads on a bad line, and where the best alternative `lfs` would otherwise produce no progress information. The program remembers the url, so as for the user to be able to continue incomplete downloads, resuming where possible. 

### Preview
- The Batch/bash menu is, functional and well layed out...
```
===============================================================================
"         ________                      .____                    .___         "
"         \______ \   ______  _  ______ |    |    ___________  __| _/         "
"          |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |          "
"          |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |          "
"         /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |          "
"                 \/                  \/        \/                \/          "
===============================================================================
    Batch Menu
===============================================================================




    1. Launch DownLord

    2. Install Requirements




===============================================================================
Selection; Options = 1-2, Exit = X:


``` 
- Main Menu (with test files)...
```
========================================================================================================================
    DownLord: Main Menu
------------------------------------------------------------------------------------------------------------------------
    #.    Filename                                           Progress     Size
========================================================================================================================


    1     1GB.bin                                            100.0%       1.00 GB

    2     512MB.zip                                          100.0%       512.00 MB

    3     100MB.bin                                          100.0%       100.00 MB

    4     50MB.zip                                           7.8%         3.91 MB/50.00 MB

    5     Empty                                              -            -

    6     Empty                                              -            -

    7     Empty                                              -            -

    8     Empty                                              -            -

    9     Empty                                              -            -


========================================================================================================================
Selection; New URL = 0, Continue = 1-9, Refresh = R, Delete = D, Setup = S, Quit = Q:


```
- Ability to input, one or multiple, url(s) in CSV...
```
========================================================================================================================
    DownLord: Initialize Download
========================================================================================================================

Enter download URL(s) separated by commas (Q to cancel): http://ipv4.download.thinkbroadband.com/50MB.zip, http://ipv4.d
ownload.thinkbroadband.com/10MB.zip, http://ipv4.download.thinkbroadband.com/100MB.zip
Processing download 1/3
Connection established in 0.2s                                                                                          
Successfully registered new download: 50MB.zip (http://ipv4.download.thinkbroadband.com/50MB.zip) with size 52428800
Retrieving file metadata (attempt 1):
Connection established in 0.1s                                                                                          
Done









```
- Download display...
```
========================================================================================================================
    DownLord: Download Active
========================================================================================================================




    Filename:
        VulkanSDK-1.4.304.1-Installer.exe

    Progress:
        22.9%

    Speed:
        1.85 MB/s

    Received/Total:
        42.97 MB/187.81 MB

    Elapsed/Remaining:
        00:00:22<00:01:18





========================================================================================================================
Selection; Abandon Download = A, Wait for Completion = >_>:

```
- Download Summary...
```
========================================================================================================================
    DownLord: Download Summary
========================================================================================================================



    Filename:
        Lamarckvergence-14B.i1-Q3_K_M.gguf

    Completed:
        2025/02/21 23:14:57

    Total Size:
        6.83 GB

    Average Speed:
        366.01 KB/s

    Elapsed Time:
        05:26:15

    Locaton:
        C:\Program_Filez\DownLord\DownLord-v0.22\downloads\Lamarckvergence-14B.i1-Q3_K_M.gguf



========================================================================================================================
Press any key for Main Menu...
```
- The new install process (Windows install shown)...
```
====================================================================================

DownLord Installer
========================================
>> Platform: Windows [OK]
>> Python 3.6+ confirmed [OK]
>> Verified directory: data [OK]
>> Verified directory: downloads [OK]
>> Verified directory: scripts [OK]
>> Verified directory: incomplete [OK]
>> Created package marker: scripts/__init__.py [OK]
>> Created requirements file: data/requirements.txt [OK]
>> Virtual environment exists [OK]
>> Installing dependencies in virtual environment [OK]
>> Dependencies installed successfully [OK]
Config file exists: data/persistent.json
Overwrite? (y/n): y
>> Created configuration file: data/persistent.json [OK]

? Installation completed successfully
Note: Use the launcher script to run DownLord with the virtual environment
Press any key to continue . . .

```

### Features
- Reduced Calculations = 1s display refresh, with, 1s refresh of net stats and 5s refresh of file stats.
- Setup Menu - Configure maximum retries, and chunk speeds, and download dir.
- Reading of complex URLs such as on hugging face downloads, while correctly obtaining filenames.
- Configuration Persistence - Recent, URLs and settings, are saved in a Json configuration file.
- Platform support - HuggingFace, HTTP/HTTPS.
- Download Resume - If for some reason the computer or program crach, then downloads may resume.
- Anti-Server-Spam - Requests are not sent to the server too often, nor at the same intervals.
- Orphan Removal - Orphan files are, detected and indexed (not tested since revisit/refracture).
- Multi-Platform - Programming towards download from, Normal http/https, HuggingHace, GoogleDrive (untested).
- Download Initialization - Tested and Improved, connection processes, handling direct links from HuggingFace.   

## Requirements
- O.S. - Its designed to work on, Windows 7-10 AND Ubuntu 22-25, it may work on others.
- Python - Supposedly 3.6-3.13, recently tested in Python 3.13 and worked.
- Internet - Internet Connection (can be iffy one) and a valid URL to download.
- Storage - The files downloaded are stored in .\Downloads, but also can configure in setup menu.

### Usage (W = Windows, U = Ubuntu)
```
1.W. Clone the repository or download the release/pre-release then unpack, to a suitable location, ie `C:\Program_Files\DownLord` or `C:\Programs\Downlord`, (generally you should not install python/powershell projects to locations with spaces such as `Program Files`).
1.U. Clone the repository or download the release/pre-release then unpack, to a suitable location, ie `/media/**UserName**/**DriveName**/Programs/Downlord` (generally you should not install python/powershell projects to locations with spaces such as `/media/**UserName**/**DriveName**/My Programs/Downlord`).
2.W. Run the batch by right click then `Run As Administrator` on `DownLord.bat`. 
2.U. Make the `sudo ./DownLord.sh` file executable (right click, properties), then run the bash in terminal in the program folder through command, `sudo ./DownLord.sh` or `sudo bash ./DownLord.sh`. 
3. Select the Installer option, to, install python requirements and unpack/create program files.
4. Returning to the menu from successful install, press 1 to launch main program.
5. Take a look in the settings menu, make sure everything is optimal.
6. On Main Menu press 0 then enter the URL to download, ensure it is a working URL.
7. The complete download will be in `.\Downloads`, remember to move completed files out to intended locations.
```

### Notation
- It works for regular http/https download, but its intended for downloading GGUFs from Huggingface, that would otherwise be done on, browser or `lfs`, less effectively.
- On a slow connection DownLord will hog the bandwidth, this is deemed to be optimal to the task, but if this becomes an issue, there is now a `Press P to Pause Download` feature.
- Under Ubuntu it was possibly to install python 3.9.6. into wine with mono?/other?, then run the batch for downlord and it worked, at least its presumed thats how it worked.

## Development
1. Re-Testing on windows (may need bugfixing).
1. The planned new update, terminal size dependent modes, 69 dude11...
```
Slot Management:
    6-slot rotation in 80x24 mode
    9-slot rotation in 120x30 mode
    Automatic shifting between modes
```
2. Make all, 1/2 word Globals/Keys to safer three word globals/JsonKeys, such as `PROGRAM_BASE_DIR` instead of `BASE_DIR`.
3. At some point a bash script and modify scripts a little, to enable Linux compatibility also.
4. Currently untested on pladform GoogleDrive.
5. Re-Test Batch Download, ie `url1, url2, url3` pasted in one go to new download. 

### File Structure
- Packaged files
```
├── DownLord.bat          # Batch menu for installer/launcher
├── DownLord.ba          # Bash menu for installer/launcher
├── installer.py           # Installation script
├── launcher.py           # Main application entry
├── LICENSE.txt           # License information
└── README.md            # Project documentation
├── scripts\                # Core application scripts
│   ├── configure.py        # program configuration
│   ├── interface.py        # UI and user interaction
│   ├── manage.py          # management of files
│   └── temporary.py        # Global, constants and variables
```
- Files created by installer/program.
```
├── downloads\               # Default download directory, created by installer
├── data\                     # Data related, Created by installer
│   ├── persistent.json       # persistent settings, Created by installer
│   └── requirements.txt      # Python requirements, Created by installer             
├── incomplete\              # Storage of incomplete downloads.
├── scripts\                 # Already part of package
│   └── __init__.py          # to fix scripts in `.\scripts`, created by installer.
```

## DISCLAIMER
This software is subject to the terms in License.Txt, covering usage, distribution, and modifications. For full details on your rights and obligations, refer to License.Txt..
