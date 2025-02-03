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
├── DownLord.bat          # Batch menu installer/launcher
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
- Launcher is downloading compitently...
```
========================================================================================================================
     ________                      .____                    .___
     \______ \   ______  _  ______ |    |    ___________  __| _/
      |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |
      |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |
     /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |
             \/                  \/        \/                \/
------------------------------------------------------------------------------------------------------------------------
    Main Menu
========================================================================================================================

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
Selection; Enter URL or Q to Quit: https://cdn-lfs-us-1.hf.co/repos/2a/54/2a542629da76ab0ae02eb2b4375fb6c63ff8b5c9cb284a32e885d1f9453eb6ab/18d1d1b9f9a19d128eda5c456331bb136738ee06d53f4f5a2c5701f9b4065e2e?response-content-disposition=attachment%3B+filename*%3DUTF-8%27%27deepseek-r1-distill-qwen-14b-uncensored-q6_k.gguf%3B+filename%3D%22deepseek-r1-distill-qwen-14b-uncensored-q6_k.gguf%22%3B&Expires=1738587851&Policy=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTczODU4Nzg1MX19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy11cy0xLmhmLmNvL3JlcG9zLzJhLzU0LzJhNTQyNjI5ZGE3NmFiMGFlMDJlYjJiNDM3NWZiNmM2M2ZmOGI1YzljYjI4NGEzMmU4ODVkMWY5NDUzZWI2YWIvMThkMWQxYjlmOWExOWQxMjhlZGE1YzQ1NjMzMWJiMTM2NzM4ZWUwNmQ1M2Y0ZjVhMmM1NzAxZjliNDA2NWUyZT9yZXNwb25zZS1jb250ZW50LWRpc3Bvc2l0aW9uPSoifV19&Signature=Z1IYKrTEOlhviVdhGyFlTout4o3opRB9Rmyx7dYscUpJ9TNYFwKPwNW18parPfC2gxj7rpI6L2gFwYQt2FFV9llM-ipnISY81vN3ovjFols4-W2Wut3j7c0gkJ1vIiMaJ6AJFOrQSz2Be7PLpkg5FlOPDznQ1%7E7GrisL-QAjE4E2bhjMa2zeYsYTDfanvkw16XeD4gjX-KL-J1epwRYBAr6JsPVbmubwjN6buWYiotfplXB7mKoWrBq-UzdFSA9QNPnt0p%7EMBgAvF%7EZEi4NbeMGXWgeMpYaEy4temfSUgzmil8kbsGDQsStVg7e4%7EyG9Wn%7EkwFXpL6qKdPtGvwyQJA__&Key-Pair-Id=K24J24Z295AEI9
deepseek-r1-distill-qwen-14b-uncensored-q6_k.gguf:   0%|                         | 11.7M/11.3G [00:31<8:03:08, 418kB/s]
```
- Installer is comprehensive...
```
Installing Requirements...

Installing DownLord...
--------------------------------------------------
>> Python version check passed [OK]
>> Platform check passed: windows [OK]
>> Checked directory: .\data [OK]
>> Checked directory: .\downloads [OK]
>> Checked directory: .\scripts [OK]
>> Checked directory: .\temp [OK]
>> Created .\scripts\__init__.py [OK]
>> Created .\data\requirements.txt [OK]
>> Installed Python dependencies [OK]
Config file already exists at: C:\Program_Filez\Downlord\DownLord-main\data\config.json
Do you want to overwrite it? (y/n): y
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
