# DownLord
Status: Working.

## Description

DownLord is a robust and user-friendly tool that allows users to download files from URLs. It provides options to select different internet connection speeds, supports download resumption, and retains the last used URL and chunk size in a configuration file. The primary purpose is to download language models on bad connections, and not return hours later to find only a tiny bit downloaded or double click retry to accidentally cancel the download. Downlord can also be used in combination with my other application "Netformance", to provide additional feedback during the download process.

## Features

* **Download Resumption:** If a download is interrupted, it can be resumed from where it left off.
* **Connection Speed Selection:** Choose from, Slow, Okay, Good, Fast, Uber, connection speeds.
* **Configuration Persistence:** The last used URL and chunk size are saved in a configuration file for convenience.
* **Reading of Complex URLs:** Such as found on, NexusMods or HuggingFace, to correctly obtain, filenames and files.

## Usage

1. Clone the repository or download the script.
2. Run `Install.bat` to install requirements in `requirements.txt`.
3. Run the script, using `python download.py` or double click `DownLord.bat`.
4. Follow the prompts to select your internet connection type and enter the URL to download.
5. The file will be downloaded to the `downloads` directory.
6) The "Downlord.lnk" shortcut provided with preset arguements to run ".bat" on taskbar.

## Output

Output looks like this...

```

                           Main Menu
                           -=-=-=-=-

Recent Downloads:

    1. largemodel-13b-8bit-GGML.bin
    2. Empty
    3. Empty
    4. Empty
    5. Empty
    6. Empty
    7. Empty
    8. Empty
    9. Empty


Press, 0 To Enter A New URL or 1-9 to Continue or s for Setup:

```
```

Enter the URL to download (or 'q' to quit): http://www.somewebsite.com/files/largemodel-13b-8bit-GGML.bin
Detected filename from URL: largemodel-13b-8bit-GGML.bin

Existing file size: 4907008000
Remote file size: 13831029888
Accept-Ranges: bytes
Resuming download of largemodel-13b-8bit-GGML.bin...
Headers: {'Range': 'bytes=4907008000-'}
Response status code: 206
36% ██████████████▍                          4.98G/13.8G 02:14/5:09:03

```
```

                        Setup Menu
                        -=-=--=-=-

            1. Slow  ~1MBit/s (Chunk Size  1024KB)
            2. Okay  ~5MBit/s (Chunk Size  4096KB)
            3. Good ~10MBit/s (Chunk Size  8192KB)
            4. Fast ~25MBit/s (Chunk Size 20480KB)
            5. Uber ~50MBit/s (Chunk Size 40960KB)


Enter your internet connection type (Press 1-5, or ENTER for 2):

```

## Requirements

- Python 3.4-3.10
- Windows (soft requirement)

## Disclaimer

DownLord is designed to facilitate file downloads, and while it aims to provide a smooth experience, interruptions or issues may occur based on the user's internet connection or other factors. Use at your own discretion and risk.
