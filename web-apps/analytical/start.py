"""
Analytical — start both servers with one command.
Run from: web-apps/analytical/
  python start.py
"""
import subprocess
import sys
import os
import time
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, 'backend')
FRONTEND = os.path.join(BASE, 'frontend')

print("Starting Analytical...")
print()

# Start backend
print("[1/2] Starting backend (FastAPI on port 8000)...")
backend_proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--port', '8000'],
    cwd=BACKEND,
)

# Start frontend file server
print("[2/2] Starting frontend (http.server on port 3000)...")
frontend_proc = subprocess.Popen(
    [sys.executable, '-m', 'http.server', '3000'],
    cwd=FRONTEND,
)

# Wait a moment then open browser
time.sleep(2)
print()
print("Opening http://localhost:3000 ...")
webbrowser.open('http://localhost:3000/dashboard.html')

print()
print("Both servers are running.")
print("  Frontend: http://localhost:3000")
print("  Backend:  http://localhost:8000")
print()
print("Press Ctrl+C to stop everything.")

try:
    backend_proc.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    backend_proc.terminate()
    frontend_proc.terminate()
