# Engineering Handover Documentation

## 1. Project Overview
**Barcode Verification System v3.0** is a FastAPI-based application designed for industrial environments. It verifies that the barcode scanned on a master shipper matches the expected job barcode.

### Tech Stack
*   **Backend**: Python 3.12+, FastAPI, Uvicorn
*   **Database**: SQLite (via SQLModel/SQLAlchemy)
*   **Frontend**: Jinja2 Templates, Vanilla JS, CSS (No build step required)
*   **Kiosk**: pywebview (WebView2 wrapper)
*   **Hardware**: Raspberry Pi (GPIO) or Windows (Simulation Mode)

## 2. Architecture
The application follows a monolithic structure but separates concerns:
*   `main.py`: Entry point, API routes, WebSocket/SSE logic.
*   `kiosk.py`: Wrapper script for launching the app in a native WebView2 window.
*   `models.py`: Database schema definitions (SQLModel).
*   `services.py`: Hardware abstraction layer (`GPIOController`). Handles both real RPi.GPIO and Simulation.
*   `database.py`: Database connection and session management.

### Key Concepts
*   **Simulation Mode**: If `RPi.GPIO` cannot be imported (e.g., on Windows), the app automatically falls back to printing "GPIO" actions to the console. This allows development on any machine.
*   **Server-Sent Events (SSE)**: The frontend listens to `/api/events` for real-time updates (scans, job changes). No polling is used.

## 3. Development Setup

### Prerequisites
*   None (The `run.bat` script handles Python & uv installation automatically).

### Local Run (Windows)
```cmd
run.bat
```

### Local Run (Linux/Mac)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run
uv run uvicorn main:app --reload
```

### API Documentation
Once running, full interactive docs are available at:
*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

## 4. Configuration
Environment variables control the app behavior.

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERVISOR_PIN` | `1234` | PIN required to end jobs or unlock line. |
| `USE_GPIO` | `false` | Set to `true` to attempt loading RPi.GPIO. |
| `LINE_NAME` | `Master Shipper Verify` | Display name in the header (e.g., "Line 1"). |

## 5. Database Schema
The SQLite database (`barcode_verification.db`) contains three main tables:

### `Job`
Represents a production run.
*   `job_id` (PK): User-defined string (e.g., "WO-123").
*   `expected_barcode`: The target barcode.
*   `is_active`: Boolean, only one job can be active at a time.

### `Scan`
Represents a single scan event.
*   `id` (PK): Auto-increment.
*   `job_id` (FK): Links to `Job`.
*   `status`: "PASS" or "FAIL".
*   `timestamp`: DateTime.

### `ShiftStats`
Daily aggregation for dashboard performance.
*   `date` (PK): The shift date.
*   `total_shippers`: Count of completed shippers.

## 6. Deployment
*   **Windows**: See `docs/WINDOWS_SETUP.md`. Uses `run.bat` and `kiosk.bat`.
*   **Linux/Pi**: Uses systemd. Service file: `barcode-verifier.service`.

## 7. Troubleshooting & Maintenance

### Common Issues
*   **"Address already in use"**: Another instance is running. Kill it or change port.
*   **Database Locked**: SQLite handles concurrency well, but ensure no manual `sqlite3` shell is holding a write lock.
*   **GPIO Errors**: Ensure the user has permission to access GPIO (usually `gpio` group on Pi).

### Extending the App
*   **MES Integration**: Add HTTP requests in `main.py` inside `process_scan()` (outbound) or add new API endpoints (inbound).
*   **New Hardware**: Update `services.py` to add methods to `GPIOController`.

## 8. Backup & Restore
*   **Backup**: The `/api/backup` endpoint dumps the full state to JSON.
*   **Restore**: The `/api/restore` endpoint **WIPES** the database and re-imports from JSON. Use with caution.
