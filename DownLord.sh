#!/bin/bash
# Script: `.\DownLord.sh`

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
    current_width=$(tput cols)
    current_height=$(tput lines)
    
    if [ "$current_width" -lt "$MIN_TERMINAL_WIDTH" ] || [ "$current_height" -lt "$MIN_TERMINAL_HEIGHT" ]; then
        echo "Adjusting terminal size for optimal display..."
        sleep 1
        echo -e "\033[8;${MIN_TERMINAL_HEIGHT};${MIN_TERMINAL_WIDTH}t"
        sleep 0.5  # Allow time for terminal to resize
    fi
}

# Check for root privileges
check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "Error: Administrator privileges required!"
        echo "Please run with: sudo $0"
        sleep 3
        exit 1
    fi
    echo "Status: Administrator"
    sleep 1
}

# Terminal display functions
get_terminal_width() {
    TERMINAL_WIDTH=$(tput cols)
    SEPARATOR_WIDTH=$((TERMINAL_WIDTH - 1))
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
        
        read -rp "Selection; Options = 1-2, Exit = X: " choice
        
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
check_root

# Start main menu
main_menu

exit 0