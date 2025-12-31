#!/bin/bash
# KOC A.I. Digital Campus - macOS Launcher (double-clickable)
# This script automatically sets up and runs KOC A.I. Digital Campus

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Open terminal window (macOS specific)
osascript -e 'tell application "Terminal" to do script "cd \"'$SCRIPT_DIR'\" && python3 run_community.py"'
