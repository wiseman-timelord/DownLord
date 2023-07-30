@echo off
setlocal enabledelayedexpansion

set "message=Installing requirements.txt..."
set "delay=1"
for %%a in (%message%) do (
    echo|set /p="%%a "
    timeout /t %delay% /nobreak >nul
)
echo.
echo.

@echo on
pip install -r requirements.txt
@echo off
echo.
echo.


set /p input=(Press enter to finish..)