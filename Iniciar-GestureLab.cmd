@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Prepare o ambiente primeiro. Veja docs\INSTALACAO.md.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" launcher.py
if errorlevel 1 (
    pause
    exit /b 1
)
