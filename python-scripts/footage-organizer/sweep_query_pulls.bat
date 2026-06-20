@echo off
REM Daily query-pull sweep — deletes 07_QUERY_PULLS/ folders untouched for 7+ days.
REM Only removes the duplicate pull folders; originals in 05_FOOTAGE_LIBRARY are never touched.
REM Registered as Windows Task Scheduler job "Footage Query-Pull Sweep" (daily).
cd /d "C:\Users\Gray Davis\my-project\python-scripts\footage-organizer"
echo ---------------------------------------------------------------- >> ".query-sweep.log"
echo [%date% %time%] running pull-cleanup --older-than 7 >> ".query-sweep.log"
"C:\Users\Gray Davis\AppData\Local\Programs\Python\Python313\python.exe" cli_index.py --client sai pull-cleanup --older-than 7 >> ".query-sweep.log" 2>&1
