@echo off
setlocal enabledelayedexpansion

echo.
echo "________                      .____                    .___"
echo "\______ \   ______  _  ______ |    |    ___________  __| _/"
echo " |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ | "
echo " |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ | "
echo "/_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ | "
echo "        \/                  \/        \/                \/ "
echo.

set "message=We will now insist upon downloading your files.."
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

set "message=Check for any errors, and run again as required."
set "delay=1"
for %%a in (%message%) do (
    echo|set /p="%%a "
    timeout /t %delay% /nobreak >nul
)
echo.
echo.

set /p input=(Press enter to finish..)