#!/bin/bash
# Mac/Linux equivalent of sweep_query_pulls.bat.
# Daily footage cleanup sweep (two jobs, both 7-day idle rule):
#   1) 07_QUERY_PULLS/      — delete pull folders untouched 7+ days (originals never touched)
#   2) 03_DELIVERED/drafts/ — delete ANY review item (video or project file) untouched
#      7+ days. drafts/ holds only disposable versions, never finals or originals.
# Safely no-ops if the footage drive isn't mounted.
# Run from launchd (see com.graydient.footage-query-sweep.plist) or cron.

# cd into this script's own folder so the relative cli_index.py + .env resolve
cd "$(dirname "$0")" || exit 1

echo "----------------------------------------------------------------" >> .query-sweep.log
echo "[$(date)] running pull-cleanup + drafts-cleanup --older-than 7" >> .query-sweep.log
python3 cli_index.py --client sai pull-cleanup --older-than 7 >> .query-sweep.log 2>&1
python3 cli_index.py --client sai drafts-cleanup --older-than 7 >> .query-sweep.log 2>&1
