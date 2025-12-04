# Barcode Verification System v3.0

A production-ready web-based barcode verification system for scanning master shipper labels on automatic carton sealers.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![SQLModel](https://img.shields.io/badge/SQLModel-0.0.14+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux%20%7C%20Windows-orange.svg)

## 🚀 What's New in v3.0

- **Web-based UI** - Access from any device on your network
- **Remote monitoring** - Supervisors can watch from their desk
- **SQLite database** - Reliable data storage (no more CSV corruption)
- **Supervisor PIN** - Require authentication to end jobs
- **Audio feedback** - Beeps on every scan (high=pass, double-low=fail)
- **Job history** - View and search past jobs
- **Health monitoring** - `/health` endpoint for ops monitoring

## 📚 Documentation

### For Operators
*   [**Operator Guide**](docs/OPERATOR_GUIDE.md) - Step-by-step usage instructions for line operators

### For IT / Deployment
*   [**Windows Setup Guide**](docs/WINDOWS_SETUP.md) - For deploying on Windows PCs
*   [**Linux/Pi Deployment**](docs/DEPLOYMENT.md) - For Raspberry Pi setup
*   [**Network Configuration**](docs/NETWORK_CONFIG.md) - Static IP, firewall, and network setup
*   [**IT Operations Guide**](docs/IT_OPERATIONS.md) - Daily operations, backup, monitoring

### Reference
*   [**FAQ**](docs/FAQ.md) - Common questions and quick answers
*   [**Hardware Shopping List**](docs/hardware.md) - Components and pricing
*   [**Engineering Handover**](docs/ENGINEERING_HANDOVER.md) - Technical details for developers

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
| **Input Validation** | Protects against invalid characters and XSS attacks |
| **High Performance** | Cached counts for instant dashboard loading (10k+ scans) |

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
uv sync
```

### 3. Run the Application

```bash
uv run python main.py
```

Or if you prefer without uv run:

```bash
python3 main.py
```

### 3. Open in Browser

| URL | Purpose |
|-----|---------|
| `http://localhost:8000` | Operator screen (local) |
| `http://<pi-ip>:8000` | Operator screen (network) |
| `http://<pi-ip>:8000/monitor` | Supervisor monitoring |
| `http://<pi-ip>:8000/history` | Job history |
| `http://<pi-ip>:8000/health` | Health check endpoint |

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

Set environment variables to configure the application:

```bash
export SUPERVISOR_PIN="5678"
export BACKUP_TOKEN="YourRandom32CharToken12345678"
export USE_GPIO="true"
export LOG_LEVEL="INFO"
uv run python main.py
```

**GPIO Pin Assignments** (in `services.py`):
- `PIN_ALARM_RELAY`: 17
- `PIN_PASS_LIGHT`: 27
- `PIN_FAIL_LIGHT`: 22
- `PIN_LINE_STOP`: 23

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

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on setting up:
- Raspberry Pi / reTerminal
- Systemd Service (Auto-start)
- Kiosk Mode (Touchscreen)

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

> ⚠️ **CRITICAL: Change Default PIN Before Production!**
> 
> The default supervisor PIN is `1234`. You **MUST** change this before deploying to production.
> Set `SUPERVISOR_PIN` environment variable in your `run.bat`, `barcode-verifier.service`, or system environment.

1. **Change the default PIN** - Edit `SUPERVISOR_PIN` in config
2. **Set BACKUP_TOKEN** - Required for `/api/backup` and `/api/restore` endpoints
3. **Rate Limiting** - PIN entry is locked for 15 minutes after 5 failed attempts
4. **Network access** - The app listens on all interfaces by default. Use firewall rules if needed
5. **No authentication for viewing** - Monitor and history pages are publicly accessible on your network

For production, consider adding:
- HTTPS with a reverse proxy (nginx)
- Network-level access controls
- Regular database backups

---

## 📁 File Structure

```
barcode_verification/
├── main.py                # Main FastAPI application
├── database.py            # Database connection
├── models.py              # SQLModel definitions
├── services.py            # GPIO and business logic
├── requirements.txt       # Python dependencies
├── barcode-verifier.service  # systemd service file
├── barcode_verification.db   # SQLite database
├── migrate_add_cached_counts.py # Migration script
├── logs/                  # Application logs
│   └── barcode_verification.log
├── tests/                 # Test suite
├── templates/             # HTML Templates
│   ├── index.html
│   ├── monitor.html
│   └── history.html
└── static/                # Static assets (CSS/JS)
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
