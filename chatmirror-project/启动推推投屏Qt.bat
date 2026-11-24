@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Please see README-QT.md
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" main.py
