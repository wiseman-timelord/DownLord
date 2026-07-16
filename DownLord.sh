#!/bin/bash
# Script: `.\DownLord.sh` - Linux Bash Menu For DownLord

# Error handling and strict mode
set -euo pipefail
trap 'echo "Error: Script failed at line $LINENO"; sleep 3; exit 1' ERR

# Constants
TITLE="DownLord"
MIN_TERMINAL_WIDTH=120
MIN_TERMINAL_HEIGHT=30

# Initialize script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || {
    echo "Error: Failed to change to script directory"
    sleep 3
    exit 1
}

# Virtual environment paths
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# Set terminal title
echo -ne "\033]0;$TITLE\007"

# Check terminal size and resize if needed
check_terminal_size() {
    local current_width current_height
    current_width=$(tput cols 2>/dev/null || echo "$MIN_TERMINAL_WIDTH")
    current_height=$(tput lines 2>/dev/null || echo "$MIN_TERMINAL_HEIGHT")
    
    if [ "$current_width" -lt "$MIN_TERMINAL_WIDTH" ] || [ "$current_height" -lt "$MIN_TERMINAL_HEIGHT" ]; then
        echo "Adjusting terminal size for optimal display..."
        sleep 1
        echo -e "\033[8;${MIN_TERMINAL_HEIGHT};${MIN_TERMINAL_WIDTH}t"
        sleep 0.5  # Allow time for terminal to resize
    fi
}

# Check privileges
# DownLord does NOT need root on Linux, and running it as root is actively
# harmful: everything it creates (.venv/, data/persistent.json, downloads/,
# incomplete/) ends up owned by root, so afterwards the normal user cannot
# write to their own downloads or config, and every later run needs sudo too.
# It also means a bug in the program runs with full system privileges.
# The Windows batch asks for Administrator because it always has; on Linux the
# only thing needed is write access to this directory, so check exactly that.
# (scripts/temporary.py agrees: PLATFORM_SETTINGS["linux"]["admin_required"] is False.)
check_permissions() {
    if [ ! -w "$SCRIPT_DIR" ]; then
        echo "Error: No write access to $SCRIPT_DIR"
        echo "Move DownLord somewhere you own, e.g. ~/DownLord"
        sleep 3
        exit 1
    fi
    if [ "$(id -u)" -eq 0 ]; then
        echo "Warning: running as root. Files created will be owned by root,"
        echo "which usually causes permission problems later. Prefer a normal user."
        sleep 3
    fi
    echo "Status: Write access confirmed"
    sleep 1
}

# Terminal display functions
# `tput cols` fails when TERM is unset or dumb (plain `sudo`, a pipe, some
# terminal emulators, cron).  Under `set -e` + the ERR trap that killed the whole
# menu with "Script failed at line N", so fall back to the 120 the UI assumes.
get_terminal_width() {
    TERMINAL_WIDTH=$(tput cols 2>/dev/null || echo "$MIN_TERMINAL_WIDTH")
    [ -z "$TERMINAL_WIDTH" ] && TERMINAL_WIDTH=$MIN_TERMINAL_WIDTH
    SEPARATOR_WIDTH=$((TERMINAL_WIDTH - 1))
    [ "$SEPARATOR_WIDTH" -lt 1 ] && SEPARATOR_WIDTH=$((MIN_TERMINAL_WIDTH - 1))
}

create_separator() {
    SEPARATOR=$(printf '=%.0s' $(seq 1 "$SEPARATOR_WIDTH"))
}

display_title() {
    clear
    check_terminal_size
    get_terminal_width
    create_separator
    
    # Print header
    echo "$SEPARATOR"
	echo "                             ________                      .____                    .___                             "
	echo "                             \______ \   ______  _  ______ |    |    ___________  __| _/                             "
	echo "                              |    |  \ /  _ \ \/ \/ /    \|    |   /  _ \_  __ \/ __ |                              "
	echo "                              |    \   (  <_> )     /   |  \    |__(  <_> )  | \/ /_/ |                              "
	echo "                             /_______  /\____/ \/\_/|___|  /_______ \____/|__|  \____ |                              "
	echo "                                     \/                  \/        \/                \/                              "         
    echo "$SEPARATOR"
}

display_separator() {
    get_terminal_width
    create_separator
    echo "$SEPARATOR"
}

# Menu functions
launch_downlord() {
    display_title
    echo
    echo "Starting $TITLE..."
    sleep 1

    # Parity with DownLord.bat, which checks for this and the venv before
    # launching.  Without it the user gets a Python traceback from
    # check_environment instead of a plain "run the installer first".
    if [ ! -f "$SCRIPT_DIR/data/persistent.json" ]; then
        echo "Error: Configuration file not found"
        echo "Please run the installer first (option 2)"
        sleep 3
        return 1
    fi

    # Check if virtual environment exists
    if [ ! -f "$VENV_PYTHON" ]; then
        echo "Error: Virtual environment not found"
        echo "Please run the installer first"
        sleep 3
        return 1
    fi
    
    # Launch using venv Python
    export PYTHONUNBUFFERED=1
    if ! "$VENV_PYTHON" -u ./launcher.py linux; then
        echo "Error: Failed to launch $TITLE"
        sleep 3
        return 1
    fi
    unset PYTHONUNBUFFERED
    sleep 2
}

run_installer() {
    echo "Running Installer..."
    sleep 1
    clear
    
    # Installer uses system Python with platform argument
    if ! python3 ./installer.py linux; then
        echo "Error: Installation failed"
		read -n 1 -s -r -p $'\nPress any key to continue...\n'        
		sleep 1
        return 1
    fi
    sleep 2
}

main_menu() {
    while true; do
        display_title
        echo "    Bash Menu"
        display_separator
        
        # Menu layout with padding
        printf "\n\n\n\n\n\n"
        echo "     1. Launch $TITLE"
        printf "\n"
        echo "     2. Install Requirements"
        printf "\n\n\n\n\n\n\n"
        display_separator
        
        # `|| { ...; }`: under `set -e` a failing read (EOF / Ctrl-D) would
        # otherwise fire the ERR trap and print a bogus "Script failed" error.
        read -rp "Selection; Options = 1-2, Exit = X: " choice || {
            echo
            echo "Input closed. Exiting..."
            exit 0
        }
        
        case "${choice,,}" in
            1)
                if launch_downlord; then
                    read -n 1 -s -r -p $'\nPress any key to continue...\n'
                    sleep 1
                else
                    read -n 1 -s -r -p $'\nPress any key to return to menu...\n'
                    sleep 1
                fi
                ;;
            2)
                if run_installer; then
                    read -n 1 -s -r -p $'\nPress any key to continue...\n'
                    sleep 1
                else
                    read -n 1 -s -r -p $'\nPress any key to return to menu...\n'
                    sleep 1
                fi
                ;;
            x)
                clear
                display_title
                echo "Closing $TITLE..."
                sleep 2
                exit 0
                ;;
            *)
                echo
                echo "Invalid selection. Please try again."
                sleep 2
                ;;
        esac
    done
}

# Main execution
echo "Initializing $TITLE..."
sleep 1
check_terminal_size
check_permissions

# Start main menu
main_menu

exit 0