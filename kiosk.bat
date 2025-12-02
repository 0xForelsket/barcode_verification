@echo off
echo Starting Barcode Verification System (Kiosk Mode)...

:: 1. Start the Server in the background (minimized)
start /min cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

:: 2. Wait 3 seconds for server to boot
timeout /t 3 /nobreak >nul

:: 3. Launch Chrome in Kiosk Mode
:: Try standard Chrome paths. If Chrome isn't installed, this might fail.
:: You can change this to "msedge" for Microsoft Edge.

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:8000 --incognito --disable-pinch --no-user-gesture-required
) else (
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:8000 --incognito --disable-pinch --no-user-gesture-required
    ) else (
        echo Chrome not found! Trying Edge...
        start msedge --kiosk http://localhost:8000 --edge-kiosk-type=fullscreen
    )
)
