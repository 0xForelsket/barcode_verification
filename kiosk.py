import webview
import sys
import threading
import time
import urllib.request
import urllib.error
import uvicorn
from main import app

def start_server():
    """Starts the Uvicorn server in a separate thread."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

def wait_for_server():
    """Waits until the server is reachable."""
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=1)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionRefusedError):
            time.sleep(0.5)
    return False

if __name__ == '__main__':
    # 1. Start Server
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # 2. Wait for Boot
    if not wait_for_server():
        print("Error: Server failed to start.")
        sys.exit(1)

    # 3. Launch Kiosk Window
    # fullscreen=True makes it a kiosk
    # on_top=True keeps it above other windows
    webview.create_window(
        'Barcode Verification System', 
        'http://127.0.0.1:8000', 
        fullscreen=True,
        on_top=True,
        confirm_close=True
    )
    
    webview.start()
