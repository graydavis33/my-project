@echo off
REM Daily footage cleanup sweep (two jobs, both 7-day, duplicates/drafts only):
REM   1) 07_QUERY_PULLS/  — delete pull folders untouched 7+ days (originals never touched)
REM   2) 03_DELIVERED/drafts/ — delete review drafts untouched 7+ days (NEVER deletes
REM      project files .prproj/.aep/.psd, finals, or originals)
REM Registered as Windows Task Scheduler job "Footage Query-Pull Sweep" (daily).
cd /d "C:\Users\Gray Davis\my-project\python-scripts\footage-organizer"
echo ---------------------------------------------------------------- >> ".query-sweep.log"
echo [%date% %time%] running pull-cleanup + drafts-cleanup --older-than 7 >> ".query-sweep.log"
"C:\Users\Gray Davis\AppData\Local\Programs\Python\Python313\python.exe" cli_index.py --client sai pull-cleanup --older-than 7 >> ".query-sweep.log" 2>&1
"C:\Users\Gray Davis\AppData\Local\Programs\Python\Python313\python.exe" cli_index.py --client sai drafts-cleanup --older-than 7 >> ".query-sweep.log" 2>&1
