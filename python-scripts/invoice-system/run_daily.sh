#!/bin/zsh
# Invoice system daily scan — run by macOS LaunchAgent at 8 AM
cd /Users/graydavis28/Desktop/my-project/python-scripts/invoice-system
/usr/bin/python3 main.py scan-all >> tracker.log 2>> tracker-error.log
