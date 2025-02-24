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
- Re-visited 2025/02. Currently needs fixing, see development.

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
- Download Initialization (HuggingFace url)...
```
========================================================================================================================
    DownLord: Initialize Download
========================================================================================================================

Enter download URL (Q to cancel): https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGUF/resolve/main/Nxcode-CQ-7B-orpo.Q3_K_M.gguf?download=true
Connection established in 0.9s                                                                                          Registering download: Nxcode-CQ-7B-orpo.Q3_K_M.gguf (https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...) size=3808626784
Successfully registered new download: Nxcode-CQ-7B-orpo.Q3_K_M.gguf (https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...) with size 3808626784
Initializing download for user-provided URL: https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...
Resolved final download endpoint: https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...
Initializing download for: https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...
Processing download URL...
Connection established in 0.6s                                                                                          Done
Resolved download URL: https://huggingface.co/QuantFactory/Nxcode-CQ-7B-orpo-GGU...
Found filename: Nxcode-CQ-7B-orpo.Q3_K_M.gguf
Connecting to server...
(Ignore Certificate Warnings)
C:\Users\mastar\AppData\Local\Programs\Python\Python311\Lib\site-packages\urllib3\connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'huggingface.co'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
  warnings.warn(
C:\Users\mastar\AppData\Local\Programs\Python\Python311\Lib\site-packages\urllib3\connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'cdn-lfs-us-1.hf.co'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
  warnings.warn(
Registered early metadata for: Nxcode-CQ-7B-orpo.Q3_K_M.gguf (Size: 3808626784)
Setting up download...


```
- Download display...
```
========================================================================================================================
    DownLord: Download Active (resumed)
========================================================================================================================




    Filename:
        Nxcode-CQ-7B-orpo.Q3_K_M.gguf

    Progress:
        35.9%

    Speed:
        719.94 KB/s

    Received/Total:
        1.27 GB/3.55 GB

    Elapsed/Remaining:
        00:01:05<00:55:10





========================================================================================================================
Downloading your file... (Press P to Pause)

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


### Features
- Reduced Calculations = 1s display refresh, with, 1s refresh of net stats and 5s refresh of file stats.
- Setup Menu - Configure maximum retries, and chunk speeds, and download dir.
- Reading of complex URLs such as on hugging face downloads, while correctly obtaining filenames.
- Configuration Persistence - Recent, URLs and settings, are saved in a Json configuration file.
- Platform support - HuggingFace, HTTP/HTTPS.
- Download Resume - If for some reason the computer or program crach, then downloads may resume.
- Anti-Server-Spam - Requests are not sent more than once per second to the server.
- Orphan Removal - Orphan files are, detected and indexed (not tested since revisit/refracture).
- Multi-Platform - Programming towards download from, Normal http/https, HuggingHace, GoogleDrive (untested).
- Download Initialization - Tested and Improved, connection processes, handling direct links from HuggingFace.   

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
- It works for regular http/https download, but its intended for downloading GGUFs from Huggingface, that would otherwise be done on, browser or `lfs`, less effectively.
- On a slow connection DownLord will hog the bandwidth, this is deemed to be optimal to the task, but if this becomes an issue, there is now a `Press P to Pause Download` feature.

## Development
1. I downloaded the vulkansdk, and upon completion, the summary screen seemed all ok, but when I press enter, I return to the menu, and in slot 1 it says "Empty", while in, `.\incomplete` and `.\downloads\`, there is no file for the download. I have tried to fix this multiple times; this needs fixing on one-shot, and if it fails then only investigate a little further, and if no luck then revert, keep doing til its correctly fixed, try different AI systems.
1. At some point a bash script and modify scripts a little, to enable Linux compatibility also.
2. Needs testing LLM to make sure it works correctly as regular downloads are at this point.
3. An interface on it, but I dont want it OS specific, and I dont want a browser interface.
4. Currently untested on pladform GoogleDrive.

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
