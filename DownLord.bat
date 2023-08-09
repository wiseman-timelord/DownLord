@echo off
mode 70,30
setlocal enabledelayedexpansion

echo.
echo "________                      .____                    .___"
echo "\______ \   ______  _  ______ |    |    ___________  __| _/"
echo " |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ | "
echo " |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ | "
echo "/_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ | "
echo "        \/                  \/        \/                \/ "
echo.

:: Read max_retries from config.json
for /f "tokens=2 delims=:" %%a in ('findstr /c:"\"retries\":" config.json') do set max_retries=%%a
set max_retries=%max_retries:~1,-1%
set "message=We will now insist upon downloading your files %max_retries% times..."
set "delay=1"
for %%a in (%message%) do (
    echo|set /p="%%a "
    timeout /t %delay% /nobreak >nul
)
echo.
echo.

@echo on
python.exe downlord.py
@echo off
echo.
echo.

set "message=Remember to move completed files to intended destinations..."
set "delay=1"
for %%a in (%message%) do (
    echo|set /p="%%a "
    timeout /t %delay% /nobreak >nul
)
echo.
echo.

set /p input=(Press enter to finish..)
