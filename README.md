# DownLord
```
=======================================================================================================================
"                             ________                      .____                    .___                             "
"                             \______ \   ______  _  ______ |    |    ___________  __| _/                             "
"                              |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |                              "
"                              |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |                              "
"                             /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |                              "
"                                     \/                  \/        \/                \/                              "
-----------------------------------------------------------------------------------------------------------------------
```
## Status: Beta
- Re-visited 2025/02. Remaining issue(s) detailed in `Development` section below.

## Description
DownLord is a more dedicated approach to downloading large and important files, such as language models, especially on unreliable connections. It offers a customizable options menu with persistent settings, supports download resumption. The program automatically maintains 9 slots, auto-removing items from its list when, manually moved from the downloads folder or selected to be deleted. Unlike browser-based downloads, DownLord ensures that dpwnloads continue until complete. It's tailored for substantial downloads on a bad line, and where the best alternative `lfs` would otherwise produce no progress information. The program remembers the url, so as for the user to be able to continue incomplete downloads, resuming where possible. 

### Preview

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
- Download Initialization (using HuggingFace url)...
```
========================================================================================================================
    DownLord: Initialize Download
========================================================================================================================

Enter download URL (Q to cancel): http://ipv4.download.thinkbroadband.com/50MB.zip
Connection established in 0.2s                                                                                          Registering download: 50MB.zip (http://ipv4.download.thinkbroadband.com/50MB.zip) size=52428800
Successfully registered new download: 50MB.zip (http://ipv4.download.thinkbroadband.com/50MB.zip) with size 52428800

Initializing download for user-provided URL: http://ipv4.download.thinkbroadband.com/50MB.zip
Resolved final download endpoint: http://ipv4.download.thinkbroadband.com/50MB.zip
Initializing download for: http://ipv4.download.thinkbroadband.com/50MB.zip
Processing download URL...

Connection established in 0.2s                                                                                          Done
Resolved download URL: http://ipv4.download.thinkbroadband.com/50MB.zip
Found filename: 50MB.zip
Connecting to server...
(Ignore Certificate Warnings)
Registered early metadata for: 50MB.zip (Size: 52428800)
Setting up download...


```
- Download display...
```
========================================================================================================================
    DownLord: Download Active
========================================================================================================================





    Filename:
        200MB.zip

    Progress:
        11.7%

    Speed:
        637.74 KB/s

    Received/Total:
        23.44 MB/200.00 MB

    Elapsed/Remaining:
        00:00:39<00:04:43




========================================================================================================================
Download in progress...


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
Press any key to return to Main Menu...
```


### Features
- Reduced Calculations = 1s display refresh, with, 1s refresh of net stats and 5s refresh of file stats.
- Setup Menu - Configure maximum retries, and chunk speeds, and download dir.
- Reading of complex URLs such as on hugging face downloads, while correctly obtaining filenames.
- Configuration Persistence - Recent, URLs and settings, are saved in a Json configuration file.
- Platform support - HuggingFace, HTTP/HTTPS.
- Download Resume - If for some reason the computer or program crach, then downloads may resume (not working currently, see Development section).
- Anti-Server-Spam - Requests are not sent more than once per second to the server.
- Orphan Removal - Orphan files are, detected and indexed (not tested since revisit/refracture).
- Multi-Platform - Programming towards download from, Normal http/https, HuggingHace (indirect link), GoogleDrive (untested).

## Requirements
- Windows 7-10 - programing/testing is done on 10.
- Python 3.6-3.11 - Python 3.11 is recommended.
- Internet - Internet Connection and a valid URL to download.
- Storage - The large files being downloaded must be stored.

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
1. While initializing the download, when it has the complete information, it is supposed to be registering the, filename and url and total size, in a free key in the json, before or as, the actual file transfer begins, so that if, for example, the program somehow, crashes or is closed, then the user can resume the download by loading the program, and selecting the item from the menu, to continue the relevant download.   
2. While initializing download, you can see, that 2 lines are repeated twice, in various parts of the download initialization processes, `Initializing download for: http://ipv4.download.thinkbroadband.com/50MB.zip` and `Resolved download URL: http://ipv4.download.thinkbroadband.com/50MB.zip`, determine, if this is correct or are we actually repeating steps, and if it is correct, then we need more fitting text to each line, to distinguish them from one another.
3. regular download stats seem to work ok, but stats for huggingface downloads are wierd, possibly this affects the googledrive stats too.
4. While downloads through normal HTTP/HTTPs work fine, the huggingface downloads seem to not be registered on the menu at the end, and the file is missing. something is wrong either in the, registration and/or moving, of, huggingface and presumably googledrive, downloads. Additionally if the file was moved, and if there was no registered item in the json, then when it loaded the menu, it should have registered the file with an unknown, filesize and url, not deleted it. 
4. After everything else, but, Linux and Windows, compatibility.

### File Structure
- Packaged files
```
├── DownLord.bat          # Batch menu installer/launcher
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
