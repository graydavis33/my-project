@echo off
cd /d "%~dp0"

:LOOP
echo [%date% %time%] Starting personal assistant... >> agent.log
python main.py >> agent.log 2>> agent-error.log
echo [%date% %time%] Agent stopped. Restarting in 5 seconds... >> agent.log
timeout /t 5 /nobreak > nul
goto LOOP
