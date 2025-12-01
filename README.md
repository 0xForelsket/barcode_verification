# Barcode Verification System v3.0

A production-ready web-based barcode verification system for scanning master shipper labels on automatic carton sealers.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux%20%7C%20Windows-orange.svg)

## 🚀 What's New in v3.0

- **Web-based UI** - Access from any device on your network
- **Remote monitoring** - Supervisors can watch from their desk
- **SQLite database** - Reliable data storage (no more CSV corruption)
- **Supervisor PIN** - Require authentication to end jobs
- **Audio feedback** - Beeps on every scan (high=pass, double-low=fail)
- **Real-time updates** - All connected screens update instantly
- **Auto-restart watchdog** - Recovers from crashes automatically
- **Job history** - View and search past jobs

---

## 📋 Features

| Feature | Description |
|---------|-------------|
| **Operator UI** | Clean, touch-friendly interface for line operators |
| **Monitor View** | Read-only dashboard for supervisors |
| **Pieces Tracking** | Track pieces per master shipper (1, 2, 3, or custom) |
| **Hourly Counts** | Shows shippers/pieces in last hour for production boards |
| **Target Progress** | Visual progress bar toward target quantity |
| **GPIO Alarms** | Trigger relays for lights, buzzers, line stops |
| **Shift Totals** | Cumulative counts across all jobs |
| **Job History** | Searchable history of all past jobs |

---

## 🖥️ Quick Start

### 1. Install uv (Python Package Manager)

```bash
# Install uv (fast, modern Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or run:
source ~/.bashrc
```

### 2. Install Dependencies

```bash
cd barcode_verification

# Install Python packages with uv
uv pip install -r requirements.txt

# For GPIO support on Raspberry Pi
uv pip install RPi.GPIO
```

### 3. Run the Application

```bash
uv run python app.py
```

Or if you prefer without uv run:

```bash
python3 app.py
```

### 3. Open in Browser

| URL | Purpose |
|-----|---------|
| `http://localhost:5000` | Operator screen (local) |
| `http://<pi-ip>:5000` | Operator screen (network) |
| `http://<pi-ip>:5000/monitor` | Supervisor monitoring |
| `http://<pi-ip>:5000/history` | Job history |

---

## 📱 Screen Guide

### Operator Screen (`/`)
The main interface for line operators:
1. Enter job ID and expected barcode
2. Select pieces per shipper (1, 2, 3, or custom)
3. Optionally set a target quantity
4. Click **START JOB**
5. Scan barcodes - screen shows PASS/FAIL
6. Click **END JOB** (requires supervisor PIN)

### Monitor Screen (`/monitor`)
Read-only dashboard showing:
- Current job status and stats
- Real-time scan results
- Hourly production counts
- Today's shift totals
- Recent completed jobs

### History Screen (`/history`)
View all past jobs with:
- Job ID, date/time, barcode
- Shipper/piece counts
- Pass rate and duration

---

## 🔧 Configuration

Edit `app.py` or set environment variables:

```python
# In app.py - Config class
SUPERVISOR_PIN = '1234'      # Change this!
USE_GPIO = False             # Set True on Raspberry Pi

# GPIO Pin Assignments
PIN_ALARM_RELAY = 17
PIN_PASS_LIGHT = 27
PIN_FAIL_LIGHT = 22
PIN_LINE_STOP = 23
```

Or via environment variables:
```bash
export SUPERVISOR_PIN="5678"
export USE_GPIO="true"
python3 app.py
```

---

## 🔌 Hardware Wiring

### GPIO Connections (Raspberry Pi)

```
Raspberry Pi          Relay Module          Device
───────────────────────────────────────────────────
GPIO 17  ──────────►  IN1  ──────────►  Alarm Buzzer
GPIO 27  ──────────►  IN2  ──────────►  Green Light
GPIO 22  ──────────►  IN3  ──────────►  Red Light
GPIO 23  ──────────►  IN4  ──────────►  Line Stop
5V       ──────────►  VCC
GND      ──────────►  GND
```

### Recommended Hardware

| Component | Purpose | Est. Cost |
|-----------|---------|-----------|
| Raspberry Pi 4 (2GB+) | Main controller | $45-55 |
| 7" Touchscreen | Operator display | $55-75 |
| USB Barcode Scanner | Label scanning | $25-80 |
| 4-Channel Relay Module | Control alarms/lights | $10 |
| 12V Buzzer | Audible fail alert | $10 |
| LED Stack Light | Visual pass/fail | $25-35 |

---

## 🚀 Production Deployment

### Install uv System-Wide (on Pi)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install dependencies
cd /home/pi/barcode_verification
uv pip install -r requirements.txt
uv pip install RPi.GPIO
```

### Auto-Start on Boot

```bash
# Copy service file
sudo cp barcode-verifier.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/barcode-verifier.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable barcode-verifier
sudo systemctl start barcode-verifier

# Check status
sudo systemctl status barcode-verifier

# View logs
sudo journalctl -u barcode-verifier -f
```

### Launch Browser on Boot (Kiosk Mode)

Create `/home/pi/.config/autostart/browser.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Barcode Verifier Browser
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000
```

### Hide Mouse Cursor

```bash
sudo apt install unclutter
# Add to /etc/xdg/lxsession/LXDE-pi/autostart:
@unclutter -idle 0.5 -root
```

---

## 📊 Database

Data is stored in `barcode_verification.db` (SQLite):

### Tables

| Table | Contents |
|-------|----------|
| `jobs` | All job records (active and completed) |
| `scans` | Individual barcode scans |
| `shift_stats` | Daily shift totals |

### Backup

```bash
# Copy database file
cp barcode_verification.db backup_$(date +%Y%m%d).db
```

### Query Examples

```bash
# Open SQLite
sqlite3 barcode_verification.db

# Today's jobs
SELECT job_id, total_scans, pass_rate FROM jobs 
WHERE date(start_time) = date('now');

# Failed scans
SELECT * FROM scans WHERE status = 'FAIL' 
ORDER BY timestamp DESC LIMIT 20;
```

---

## 🔊 Audio Feedback

The system plays sounds through the browser:

| Event | Sound |
|-------|-------|
| **PASS** | Single high beep (800Hz) |
| **FAIL** | Double low beep (300Hz) |

Works on any device with speakers. No additional hardware needed.

---

## 🛡️ Reliability Features

### Auto-Restart Watchdog

The systemd service automatically restarts the app if it crashes or becomes unresponsive.

### Database Integrity

SQLite provides ACID compliance - no data loss even on power failure.

### Network Resilience

The UI continues working offline. Scans are processed locally and synced in real-time when connected.

---

## 🔐 Security Notes

1. **Change the default PIN** - Edit `SUPERVISOR_PIN` in config
2. **Network access** - The app listens on all interfaces by default. Use firewall rules if needed.
3. **No authentication for viewing** - Monitor and history pages are publicly accessible on your network

For production, consider adding:
- HTTPS with a reverse proxy (nginx)
- Network-level access controls
- Regular database backups

---

## 📁 File Structure

```
barcode_verification/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── barcode-verifier.service  # systemd service file
├── barcode_verification.db   # SQLite database (created on first run)
├── templates/
│   ├── index.html         # Operator screen
│   ├── monitor.html       # Supervisor monitor
│   └── history.html       # Job history
└── static/
    ├── css/
    │   └── style.css      # Styles
    └── js/
        └── app.js         # Client-side JavaScript
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Scanner not working | Ensure scanner is in "keyboard wedge" mode |
| GPIO not responding | Check `USE_GPIO=true` and run with sudo or gpio group |
| Page not loading | Check if app is running: `sudo systemctl status barcode-verifier` |
| Database locked | Stop app, check for zombie processes |
| No sound | Check browser audio permissions, try clicking page first |
| uv not found | Run `source ~/.bashrc` or restart terminal |
| Module not found | Run `uv pip install -r requirements.txt` again |

---

## 📈 Future Ideas

- Email alerts on high fail rates
- Integration with WMS/ERP systems
- Multi-line dashboard
- Barcode image capture on failures
- Shift reports export (PDF/Excel)

---

## 📄 License

MIT License - Use freely for your operations.
