@echo off
setlocal

:: Change to script's directory
cd /d "%~dp0"

echo ============================================================
echo      Barcode Verification System - Kiosk Mode
echo ============================================================
echo.

:: 1. Ensure Environment is Ready (Re-use logic from run.bat)
if not exist ".venv" (
    echo [Setup] First run detected. Initializing...
    call run.bat
    exit /b
)

:: 2. Launch Kiosk Wrapper
echo [System] Launching Kiosk Interface...
".venv\Scripts\python.exe" kiosk.py

pause
