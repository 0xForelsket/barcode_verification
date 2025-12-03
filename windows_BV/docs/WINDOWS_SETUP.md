# Windows Setup Guide

This application is fully compatible with Windows. Since Windows desktops don't have GPIO pins, the application will automatically run in **Simulation Mode**, meaning it will work without any hardware (lights/buzzers) but fully support scanning and data logging.

## Prerequisites
*   **None!** The setup script handles everything (Python, dependencies, etc).

## Installation

1.  **Copy the Project**: Copy the `barcode_verification` folder to your Windows machine.

## Running the Application

1.  **Double-Click `run.bat`**.
2.  That's it.
    *   It will automatically install **uv** (Package Manager).
    *   It will automatically install **Python 3.12**.
    *   It will install all libraries.
    *   It will start the server.

*(The first run may take 2-3 minutes to download everything. Subsequent runs are instant.)*

## Running the Application

### Option 1: Double-Click Script (Recommended)
We have provided a `run.bat` script. Just double-click it to start the server!

### Option 2: Manual Start
In your command prompt (inside the project folder), run:
```cmd
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Accessing the App
Once running, open your browser (Chrome/Edge) and go to:
*   **Local**: [http://localhost:8000](http://localhost:8000)
*   **Network**: Find your computer's IP address (`ipconfig`) and use `http://YOUR_IP:8000` from other devices.

## Simulation Mode
On Windows, you will see `[GPIO] RPi.GPIO not available - running in simulation mode` in the console. This is normal.
*   **Pass/Fail Lights**: Simulated in the console logs.
*   **Buzzer**: Simulated in the console logs.
*   **Scanning**: Works exactly the same (USB scanners act as keyboards).

## Kiosk Mode (Auto-Start)

To make the PC boot directly into the app:

1.  **Enable Auto-Login**:
    *   Press `Win + R`, type `netplwiz`, and uncheck "Users must enter a user name and password".
2.  **Add to Startup**:
    *   Press `Win + R`, type `shell:startup`, and press Enter.
    *   **Right-click** inside the folder > **New** > **Shortcut**.
    *   Browse to your `C:\barcode_verification\kiosk.bat` file.
    *   Click **Next** and **Finish**.

**Important**: Do NOT try to run `kiosk.bat` as a Windows Service. Services run in the background and cannot show the application window. You must use the **Startup Folder** method above so the window appears on the desktop.

Now, whenever you restart the PC, it will automatically log in and launch the Barcode System in a clean, full-screen window!

## Strict Kiosk Mode (Block Alt+F4)

If you need to prevent users from closing the app with `Alt+F4`, you have two options:

### Option A: Use the "Lite Kiosk" (Recommended)
The `kiosk.bat` method above uses a custom window that is harder to close than a browser, but **Alt+F4 still works**. This is usually fine for trusted operators.

### Option B: Windows Assigned Access (Maximum Security)
If you need to **block** Alt+F4 and Ctrl+Alt+Del, you must use Windows Assigned Access with **Microsoft Edge** (not our custom window).

1.  **Create a Standard User**: Go to Settings > Accounts > Family & other users > Add someone else to this PC. Name it `KioskUser`.
2.  **Set up Assigned Access**:
    *   Go to Settings > Accounts > Access work or school > **Set up a kiosk**.
    *   Choose `KioskUser`.
    *   Select **Microsoft Edge** as the app.
    *   Set the URL to `http://localhost:8000`.
    *   Select "As a digital sign or interactive display".
3.  **Auto-Start Server**: You still need the Python server running. Add `run.bat` to the **System Startup** (Task Scheduler) so it runs before the user logs in.
4.  **Auto-Login**:
    *   Press `Win + R`, type `netplwiz`.
    *   Select `KioskUser`.
    *   Uncheck "Users must enter a user name and password".
    *   Click **Apply**.

*Note: This locks the PC completely to Edge. You will lose the "Native App" look of pywebview, but gain OS-level security.*

### Admin Override
To exit Kiosk mode as an Administrator:
1.  Press **Ctrl + Alt + Delete**.
2.  This bypasses the lock and shows the system security screen.
3.  Click **Sign out**.
4.  Log in with your **Administrator** account.

## Multi-Line Deployment

If you are setting this up on multiple lines (e.g., Line 1, Line 2):

1.  **Clone**: Set up one PC completely (Python, Code, Kiosk Mode). Then just copy the entire `barcode_verification` folder to the other PCs.
2.  **Name the Line**:
    *   Open `run.bat` (Right-click > Edit).
    *   Uncomment and change the line: `set LINE_NAME=Line 2 - Packing`.
    *   Restart the app.
    *   Restart the app.
    *   The header will now show "Line 2 - Packing" instead of the default title.

## Troubleshooting & Logs

If something isn't working:

1.  **Check the Console**: The black window that opens shows real-time logs.
2.  **Check Log File**: A detailed log is saved to `logs/barcode_verification.log`.
3.  **Database Error**: If you see "database locked", make sure no other instance of the app is running.

