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

- Main menu looking sleek...
```
========================================================================================================================
    DownLord: Main Menu
------------------------------------------------------------------------------------------------------------------------
    #.    Filename                                           Progress     Size
========================================================================================================================


    1     1GB.bin                                            100.0%       1.00 GB

    2     512MB.zip                                          100.0%       512.00 MB

    3     100MB.bin                                          100.0%       100.00 MB

    4     Empty                                              -            -

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

Enter download URL (Q to cancel): https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54ba7cd4b1c839b9f032c269075534e6b4f01988460ea615/bb9487edfa40bef4af3aae0644883b6f0081397d2ce34e6da660858012b86176?response-content-disposition=attachment%3B+filename*%3DUTF-8%27%27Lamarckvergence-14B.i1-Q3_K_M.gguf%3B+filename%3D%22Lamarckvergence-14B.i1-Q3_K_M.gguf%22%3B&Expires=1740162855&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTc0MDE2Mjg1NX19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy11cy0xLmhmLmNvL3JlcG9zLzY0LzM3LzY0Mzc4MGY4NWRiMjI5N2M1NGJhN2NkNGIxYzgzOWI5ZjAzMmMyNjkwNzU1MzRlNmI0ZjAxOTg4NDYwZWE2MTUvYmI5NDg3ZWRmYTQwYmVmNGFmM2FhZTA2NDQ4ODNiNmYwMDgxMzk3ZDJjZTM0ZTZkYTY2MDg1ODAxMmI4NjE3Nj9yZXNwb25zZS1jb250ZW50LWRpc3Bvc2l0aW9uPSoifV19&Signature=JJ7LNcr64wcW%7EdU0oGEg5-ZC2jrjAgMDQmVG2hd%7EZGeOnzli1Ys2WEn9ZirQhLFs97doVLM5kqP6MfbgmzBy8PK54pjxDRfN3vZnvppgZklw50nexc63GrDOCJJnxzUZ1WNd3FTGyLfWabrWcZ521taFwsZsl8W9VA2O7y-Fl6nAjsdO9yyuyLP%7EzopY8uEDH5ZaG0%7E2uet9TsfpjgEHXvi8Pix2u0nZ4otIAlsTR206DDJICK9v8w5f86T-Fc-LRdchrGbdOG7n6TkcLmMdNWOeYjotQiz%7E9CKfyuESCTW24gYSTWNDxZGWlnPelgw1KgYq2rFJMiBNr%7E9jKETxDw__&Key-Pair-Id=K24J24Z295AEI9

Processing CDN URL
Verifying URL accessibility (60s timeout): Completed in 0.5s
Connection established in 0.3s                                                                                          Found filename: Lamarckvergence-14B.i1-Q3_K_M.gguf

Initializing download for: https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...
Resolved download URL: https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...
Registering download: Lamarckvergence-14B.i1-Q3_K_M.gguf (https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...) size=0
Successfully registered new download: Lamarckvergence-14B.i1-Q3_K_M.gguf (https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...) with size 0
Initializing download for: https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...
Processing download URL...

Retrieving file metadata:
Processing CDN URL
Verifying URL accessibility (120s timeout): Completed in 0.3s
Connection established in 0.2s                                                                                          Found filename: Lamarckvergence-14B.i1-Q3_K_M.gguf
Done
Resolved download URL: https://cdn-lfs-us-1.hf.co/repos/64/37/643780f85db2297c54...
Found filename: Lamarckvergence-14B.i1-Q3_K_M.gguf
Connecting to server...
(Ignore Certificate Warnings)
C:\Users\mastar\AppData\Local\Programs\Python\Python311\Lib\site-packages\urllib3\connectionpool.py:1097: InsecureRequestWarning: Unverified HTTPS request is being made to host 'cdn-lfs-us-1.hf.co'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
  warnings.warn(

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
1. While initializing the download, when it has the complete information, it is supposed to be registering the, filename and url and total size, in a free key in the json, before or as, the actual file transfer begins, so that if, for example, the program somehow, crashes or is closed, then the user can resume the download by loading the program, and selecting the item from the menu, to continue the relevant download.   
2. While initializing download, you can see, that 2 lines are repeated twice, in various parts of the download initialization processes...
```
Initializing download for: http://ipv4.download.thinkbroadband.com/50MB.zip
```
...and...
```
Resolved download URL: http://ipv4.download.thinkbroadband.com/50MB.zip
```
...determine, if this is correct or are we actually repeating steps, and if it is correct, then we need more fitting text to each line, to distinguish them from one another.

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
