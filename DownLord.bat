REM Script: .\DownLord.bat - Windows Batch Menu For DownLord
@echo off
setlocal enabledelayedexpansion

REM title code
set "TITLE=DownLord"
title %TITLE%

:: Initialize console to 120x30 if too small
for /F "usebackq tokens=2* delims=: " %%W in (`mode con ^| findstr /C:"Columns"`) do set /A "current_width=%%W"
if %current_width% LSS 120 (
    mode con: cols=120 lines=30
)

:: DP0 TO SCRIPT BLOCK DO NOT MODIFY or MOVE START
set "ScriptDirectory=%~dp0"
set "ScriptDirectory=%ScriptDirectory:~0,-1%"
cd /d "%ScriptDirectory%"
echo Dp0'd to Script.
:: DP0 TO SCRIPT BLOCK DO NOT MODIFY or MOVE END

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Error: Admin Required!
    timeout /t 2 >nul
    echo Right Click, Run As Administrator.
    timeout /t 2 >nul
    goto :end_of_script
)
echo Status: Administrator
timeout /t 1 >nul

REM Functions
goto :SkipFunctions

:FindPython
REM Try to find Python in various locations
set "PYTHON_EXE="

REM Check if python is on PATH
where python >nul 2>&1
if %errorLevel% EQU 0 (
    set "PYTHON_EXE=python"
    goto :eof
)

REM Check default Python installation directories
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :eof
    )
)

REM Check Program Files
for /d %%D in ("%ProgramFiles%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :eof
    )
)

REM Check Program Files x86
for /d %%D in ("%ProgramFiles(x86)%\Python3*") do (
    if exist "%%D\python.exe" (
        set "PYTHON_EXE=%%D\python.exe"
        goto :eof
    )
)

REM Not found
goto :eof

:GetTerminalWidth
for /F "usebackq tokens=2* delims=: " %%W in (`mode con ^| findstr /C:"Columns"`) do set /A "TERMINAL_WIDTH=%%W"
set /A "SEPARATOR_WIDTH=TERMINAL_WIDTH-1"
exit /b

:CreateSeparator
set "SEPARATOR="
for /L %%i in (1,1,%SEPARATOR_WIDTH%) do set "SEPARATOR=!SEPARATOR!="
exit /b

:DisplayTitle
cls
call :GetTerminalWidth
call :CreateSeparator
echo %SEPARATOR%

REM Always use 120 width display
echo "                             ________                      .____                    .___                             "
echo "                             \______ \   ______  _  ______ |    |    ___________  __| _/                             "
echo "                              |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |                              "
echo "                              |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |                              "
echo "                             /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |                              "
echo "                                     \/                  \/        \/                \/                              "

echo %SEPARATOR%
goto :eof

:DisplaySeparator
call :GetTerminalWidth
call :CreateSeparator
echo %SEPARATOR%
goto :eof

:MainMenu
color 0B
call :DisplayTitle
echo     Batch Menu
call :DisplaySeparator

REM Always use expanded menu layout
echo.
echo.
echo.
echo.
echo.
echo.
echo     1. Launch %TITLE%
echo.
echo     2. Install Requirements
echo.
echo.
echo.
echo.
echo.
echo.
echo.

call :DisplaySeparator
set /p "choice=Selection; Options = 1-2, Exit = X: "

REM Process user input
if /i "%choice%"=="1" (
    REM Check if persistent.json exists
    if not exist "data\persistent.json" (
        echo.
        echo Error: Configuration file not found!
        echo Please run the installer first.
        timeout /t 3 >nul
        goto MainMenu
    )
    
    REM Check if virtual environment exists
    if not exist ".venv\Scripts\python.exe" (
        echo.
        echo Error: Virtual environment not found!
        echo Please run the installer first.
        timeout /t 3 >nul
        goto MainMenu
    )
    
    color 1B
    call :DisplayTitle
    echo.
    echo Starting %TITLE%...
    set PYTHONUNBUFFERED=1
    REM Use virtual environment Python
    ".venv\Scripts\python.exe" -u .\launcher.py windows
    if errorlevel 1 (
        echo Error launching %TITLE%
        pause
    )
    set PYTHONUNBUFFERED=0
    pause
    goto MainMenu
)

if /i "%choice%"=="2" (
    cls
    color 1B
    echo Running Installer...
    timeout /t 1 >nul
    cls
    call :DisplaySeparator
    
    REM Find Python for installer
    call :FindPython
    
    if "!PYTHON_EXE!"=="" (
        echo Error: Python not found!
        echo.
        echo Python was not found on PATH or in default locations:
        echo   - %%LOCALAPPDATA%%\Programs\Python\Python3##
        echo   - %%ProgramFiles%%\Python3##
        echo.
        set /p "PYTHON_PATH=Please enter full path to python.exe: "
        if exist "!PYTHON_PATH!" (
            set "PYTHON_EXE=!PYTHON_PATH!"
        ) else (
            echo Invalid path. Installation cancelled.
            pause
            goto MainMenu
        )
    ) else (
        echo Found Python: !PYTHON_EXE!
        timeout /t 1 >nul
    )
    
    REM Run installer with found Python
    "!PYTHON_EXE!" .\installer.py windows
    if errorlevel 1 (
        echo Error during installation
    )
    pause
    goto MainMenu
)

if /i "%choice%"=="X" (
    cls
    call :DisplayTitle
    echo Closing %TITLE%...
    timeout /t 2 >nul
    goto :end_of_script
)

REM Invalid input handling
echo.
echo Invalid selection. Please try again.
timeout /t 2 >nul
goto MainMenu

:SkipFunctions
goto MainMenu

:end_of_script
pause
cls
color 0B
call :DisplayTitle
echo. 
timeout /t 2 >nul
exit