@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Python environment is missing. Please see README-personal.md.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" tuitui_personal_main.py
