# DownLord
Status: Working.

## Description

DownLord is a robust and user-friendly tool that allows users to download files from URLs. It provides options to select different internet connection speeds, supports download resumption, and retains the last used URL and chunk size in a configuration file. The primary purpose is to download language models on bad connections, and not return hours later to find only a tiny bit downloaded or double click retry to accidentally cancel the download.

## Features

1. **Connection Speed Selection:** Choose from Mobile, Wired, or Super-fast connection speeds.
2. **Download Resumption:** If a download is interrupted, it can be resumed from where it left off.
3. **Configuration Persistence:** The last used URL and chunk size are saved in a configuration file for convenience.
4. **Reading of Complex URLs:** Such as found on hugging face download, to correctly obtain filenames.

## Usage

1. Clone the repository or download the script.
2. Run `Install.bat` to install requirements in `requirements.txt`.
3. Run the script, using `python download.py` or double click `DownLord.bat`.
4. Follow the prompts to select your internet connection type and enter the URL to download.
5. The file will be downloaded to the `downloads` directory.

## Output

Output looks like this...

```

                  Netformancer


Adapter: vEthernet (WSL) - Idle Time: 01:45:46

Data In Rate: 0.00 KB/s, Data In Total: 0.00 GB
Pauses In:0, Discards In: 0, Errors In: 0.
Data Out Rate: 0.00 KB/s, Data Out Total: 0.03 GB
Pauses Out:0, Discards Out: 0, Errors Out: 0.


Adapter: Ethernet - Idle Time: 00:14:25

Data In Rate: 0.06 KB/s, Data In Total: 33.45 GB
Pauses In:0, Discards In: 0, Errors In: 0.
Data Out Rate: 0.04 KB/s, Data Out Total: 0.66 GB
Pauses Out:0, Discards Out: 0, Errors Out: 0.


Adapter: vEthernet (Default Switch) - Idle Time: 04:49:47

Data In Rate: 0.00 KB/s, Data In Total: 0.00 GB
Pauses In:0, Discards In: 0, Errors In: 0.
Data Out Rate: 0.00 KB/s, Data Out Total: 0.00 GB
Pauses Out:0, Discards Out: 0, Errors Out: 0.
```
## Requirements

- Python 3.x

## Disclaimer

DownLord is designed to facilitate file downloads, and while it aims to provide a smooth experience, interruptions or issues may occur based on the user's internet connection or other factors. Use at your own discretion and risk.
