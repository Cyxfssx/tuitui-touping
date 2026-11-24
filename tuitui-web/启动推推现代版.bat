@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Python environment missing. See README-webview.md.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -c "import webview, PIL" >nul 2>&1
if errorlevel 1 (
  echo Missing dependencies. Run: .venv\Scripts\python.exe -m pip install -r requirements-webview.txt
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" tuitui_web_main.py
