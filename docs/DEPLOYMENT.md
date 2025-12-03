# Production Deployment Guide (reTerminal / Raspberry Pi)

This guide covers setting up the Barcode Verification System on a Seeed Studio reTerminal or reTerminal DM (powered by Raspberry Pi CM4).

## 1. Quick Setup (Recommended)
We provide an automated script to handle installation, dependencies, and configuration.

1. **Clone the Repo**:
   ```bash
   cd /home/pi
   git clone <your-repo-url> barcode_verification
   cd barcode_verification
   ```

2. **Run Setup**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   Follow the prompts. The system will reboot when finished.

## 2. Manual Setup
If you prefer to set up manually, follow these steps:

### Hardware Setup
- **Device**: reTerminal or reTerminal DM
- **OS**: Raspberry Pi OS (Bullseye or Bookworm) - 64-bit recommended.
- **Network**: Connect via Ethernet or Wi-Fi.

### System Preparation
Update the system and install necessary tools:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git unclutter
```

## 3. Application Installation
We use `uv` for fast, reliable Python package management.

### Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### Clone & Setup
```bash
cd /home/pi
git clone <your-repo-url> barcode_verification
cd barcode_verification

# Install dependencies
uv sync
```

## 4. Service Setup (Auto-start)
Run the application as a systemd service to ensure it starts on boot and restarts on failure.

1. **Edit Service File** (if paths differ):
   Check `barcode-verifier.service` and ensure `WorkingDirectory` and `ExecStart` match your setup.
   
   *Recommended `ExecStart` using `uv`:*
   ```ini
   ExecStart=/home/pi/.local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Install Service**:
   ```bash
   sudo cp barcode-verifier.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable barcode-verifier
   sudo systemctl start barcode-verifier
   ```

3. **Check Status**:
   ```bash
   sudo systemctl status barcode-verifier
   ```

## 5. Kiosk Mode (Touchscreen)
To launch the interface automatically on the reTerminal screen:

1. **Create Autostart Entry**:
   ```bash
   mkdir -p /home/pi/.config/autostart
   nano /home/pi/.config/autostart/kiosk.desktop
   ```

2. **Add Content**:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Barcode Verifier Kiosk
   Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://localhost:5000
   X-GNOME-Autostart-enabled=true
   ```

3. **Hide Cursor** (Optional but recommended):
   Ensure `unclutter` is installed (`sudo apt install unclutter`). It will auto-hide the mouse cursor.

## 6. GPIO Configuration (reTerminal)
The reTerminal exposes GPIO pins via the 40-pin header (if accessible) or the industrial connector on the DM version.

- **Standard reTerminal**: The 40-pin header is compatible with standard RPi GPIO numbering.
- **reTerminal DM**: May require specific drivers or mapping depending on the IO board.

Ensure the `pi` user is in the `gpio` group:
```bash
sudo usermod -a -G gpio pi
```

Enable GPIO in the app by setting `USE_GPIO=true` in `barcode-verifier.service` or environment.

## 7. Maintenance
- **Logs**: `sudo journalctl -u barcode-verifier -f`
- **Update**: 
  ```bash
  cd /home/pi/barcode_verification
  git pull
  uv sync
  sudo systemctl restart barcode-verifier
  ```
