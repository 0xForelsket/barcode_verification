@echo off
setlocal

echo ============================================================
echo      Barcode Verification System - Auto Setup
echo ============================================================
echo.

:: 1. Check for uv (The Python Package Manager)
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [Setup] 'uv' not found. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    :: Add uv to PATH for this session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo [Setup] 'uv' is already installed.
)

:: Verify uv is accessible
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [Error] 'uv' command not found even after installation.
    echo Please restart the script or add %USERPROFILE%\.cargo\bin to your PATH.
    pause
    exit /b 1
)

:: 2. Ensure Python 3.12 is installed (Managed by uv)
echo [Setup] Ensuring Python 3.12 is installed...
uv python install 3.12

:: 3. Create Virtual Environment (if missing)
if not exist ".venv" (
    echo [Setup] Creating Virtual Environment...
    uv venv .venv --python 3.12
)

:: 4. Install Dependencies
echo [Setup] Syncing dependencies...
uv pip install -r requirements.txt

:: 5. Run Application
echo.
echo [System] Starting Barcode Verification System...
echo.

:: Set the Line Name here (Optional)
:: set LINE_NAME=Line 1 - Packing

uv run uvicorn main:app --host 0.0.0.0 --port 8000

pause
