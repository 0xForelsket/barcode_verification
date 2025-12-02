@echo off
echo Starting Barcode Verification System...
echo.
echo Access the app at http://localhost:8000
echo Press Ctrl+C to stop.
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
