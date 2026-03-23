@echo off
cd /d "%~dp0"

:LOOP
echo [%date% %time%] Starting invoice daily scan... >> invoice_scan.log
python main.py scan-all --schedule >> invoice_scan.log 2>&1
echo [%date% %time%] Process stopped. Restarting in 10 seconds... >> invoice_scan.log
timeout /t 10 /nobreak > nul
goto LOOP
