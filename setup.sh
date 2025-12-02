#!/bin/bash

# Barcode Verification System - Auto Setup Script
# For reTerminal / Raspberry Pi

set -e

echo "🚀 Starting Barcode Verification System Setup..."

# Check if running as root (we need sudo for some parts, but script should be run as pi user)
if [ "$EUID" -eq 0 ]; then
  echo "Please run as normal user (pi), not root."
  exit 1
fi

APP_DIR=$(pwd)
USER_HOME=$HOME

echo "📂 Working directory: $APP_DIR"

# 1. System Updates & Dependencies
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y git unclutter chromium-browser

# 2. Install uv
echo "⚡ Installing uv package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $USER_HOME/.local/bin/env
else
    echo "uv is already installed."
fi

# 3. Install Python Dependencies
echo "🐍 Installing Python dependencies..."
$USER_HOME/.local/bin/uv sync
# Ensure RPi.GPIO is installed (it might be skipped on non-Pi systems during sync if not in lockfile correctly for that platform)
$USER_HOME/.local/bin/uv pip install RPi.GPIO

# 4. Setup Service
echo "⚙️ Setting up systemd service..."
SERVICE_FILE="barcode-verifier.service"

# Update paths in service file to match current location
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$APP_DIR|g" $SERVICE_FILE
sed -i "s|ExecStart=.*|ExecStart=$USER_HOME/.local/bin/uv run uvicorn main:app --host 0.0.0.0 --port 5000|g" $SERVICE_FILE
sed -i "s|User=.*|User=$USER|g" $SERVICE_FILE
sed -i "s|Group=.*|Group=$USER|g" $SERVICE_FILE

sudo cp $SERVICE_FILE /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable barcode-verifier
sudo systemctl restart barcode-verifier

echo "✅ Service started!"

# 5. Setup Kiosk Mode
echo "🖥️ Setting up Kiosk mode..."
AUTOSTART_DIR="$USER_HOME/.config/autostart"
mkdir -p $AUTOSTART_DIR

cat > $AUTOSTART_DIR/kiosk.desktop <<EOL
[Desktop Entry]
Type=Application
Name=Barcode Verifier Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://localhost:5000
X-GNOME-Autostart-enabled=true
EOL

# 6. GPIO Permissions
echo "🔌 Configuring GPIO permissions..."
sudo usermod -a -G gpio $USER || true
sudo usermod -a -G dialout $USER || true

echo "🎉 Setup Complete!"
echo "The system will auto-start on boot."
echo "You can manually check the service with: sudo systemctl status barcode-verifier"
echo "Rebooting is recommended to apply all changes."
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    sudo reboot
fi
