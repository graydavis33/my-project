#!/bin/bash
# Mac/Linux equivalent of sweep_query_pulls.bat.
# Daily query-pull sweep — deletes 07_QUERY_PULLS/ folders untouched for 7+ days.
# Only removes the duplicate pull folders; originals in 05_FOOTAGE_LIBRARY are never touched.
# Safely no-ops if the footage drive isn't mounted.
# Run from launchd (see com.graydient.footage-query-sweep.plist) or cron.

# cd into this script's own folder so the relative cli_index.py + .env resolve
cd "$(dirname "$0")" || exit 1

echo "----------------------------------------------------------------" >> .query-sweep.log
echo "[$(date)] running pull-cleanup --older-than 7" >> .query-sweep.log
python3 cli_index.py --client sai pull-cleanup --older-than 7 >> .query-sweep.log 2>&1
