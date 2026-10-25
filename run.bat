@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Jalankan python setup_project.py terlebih dahulu.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m genshin_research serve %*
if errorlevel 1 pause
