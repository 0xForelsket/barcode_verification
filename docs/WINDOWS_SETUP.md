# Windows Setup Guide

This application is fully compatible with Windows. Since Windows desktops don't have GPIO pins, the application will automatically run in **Simulation Mode**, meaning it will work without any hardware (lights/buzzers) but fully support scanning and data logging.

## Prerequisites

1.  **Python 3.12+**: Download and install from [python.org](https://www.python.org/downloads/).
    *   **IMPORTANT**: Check the box **"Add Python to PATH"** during installation.

## Installation

1.  **Copy the Project**: Copy the `barcode_verification` folder to your Windows machine (e.g., to `C:\barcode_verification`).
2.  **Open Terminal**:
    *   Press `Win + R`, type `cmd`, and press Enter.
    *   Navigate to the folder:
        ```cmd
        cd C:\barcode_verification
        ```

3.  **Install Dependencies**:
    Run the following command to install the required libraries:
    ```cmd
    pip install -r requirements.txt
    ```

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

1.  **Create the Kiosk Script**: We provided `kiosk.bat`. This script starts the server and launches Chrome/Edge in full-screen Kiosk mode.
2.  **Enable Auto-Login**:
    *   Press `Win + R`, type `netplwiz`, and uncheck "Users must enter a user name and password".
3.  **Add to Startup**:
    *   Press `Win + R`, type `shell:startup`, and press Enter.
    *   **Right-click** inside the folder > **New** > **Shortcut**.
    *   Browse to your `C:\barcode_verification\kiosk.bat` file.
    *   Click **Next** and **Finish**.

Now, whenever you restart the PC, it will automatically log in and launch the Barcode System in full screen!
