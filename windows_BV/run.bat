@echo off
setlocal

:: Change to script's directory
cd /d "%~dp0"

echo ============================================================
echo      Barcode Verification System - Auto Setup
echo ============================================================
echo.

:: 1. Check for uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [Setup] 'uv' not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    :: Correct path for uv on Windows
    set "PATH=%LOCALAPPDATA%\uv\bin;%PATH%"
)

:: Verify uv is accessible
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [Error] 'uv' not found after installation.
    echo Please close this window and run the script again.
    pause
    exit /b 1
)

:: 2. Sync environment
echo [Setup] Syncing environment...
uv sync
if %errorlevel% neq 0 (
    echo [Error] Failed to sync environment.
    pause
    exit /b 1
)

:: 3. Run application
echo.
echo [System] Starting Barcode Verification System...
echo.

uv run uvicorn main:app --host 0.0.0.0 --port 8000

pause
endlocal