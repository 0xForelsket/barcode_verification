# AGENT.md - Barcode Verification System Context

## 🚀 Project Overview
The **Barcode Verification System v3.0** is a production-ready web application designed for scanning master shipper labels on automatic carton sealers. It ensures that the correct labels are applied by verifying scanned barcodes against a job-specific target.

**Key Features:**
- **Web-based UI**: Accessible via browser for operators (`/`) and supervisors (`/monitor`, `/history`).
- **Real-time Feedback**: Audio and visual cues for PASS/FAIL scans.
- **Hardware Integration**: Supports GPIO for stack lights, buzzers, and line stops (Raspberry Pi).
- **Reliability**: SQLite database, auto-restart watchdog, and offline capability.

## 🛠️ Tech Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI
- **Database**: SQLite with SQLModel (ORM)
- **Frontend**: HTML/CSS/JS (Jinja2 templates)
- **Package Manager**: `uv` (Astral)
- **Platform**: Linux (Raspberry Pi preferred) / Windows compatible

## 📂 Project Structure
- `main.py`: Entry point, FastAPI app, API routes, and SSE endpoints.
- `services.py`: Business logic, GPIO control, and hardware interactions.
- `models.py`: SQLModel database schema definitions.
- `database.py`: Database connection and session management.
- `templates/`: Jinja2 HTML templates for UI (`index.html`, `monitor.html`, `history.html`).
- `static/`: CSS and JavaScript files.
- `tests/`: Pytest test suite.

## ⚡ Key Commands

### Setup & Run
```bash
# Install dependencies
uv sync

# Run application (Auto-reloads on change)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run application (Production)
uv run python main.py
```

### Testing & Maintenance
```bash
# Run all tests
uv run pytest tests/

# Run database migration (if needed)
uv run python migrate_add_cached_counts.py

# Backup database
curl -H "X-Backup-Token: <TOKEN>" http://localhost:8000/api/backup -o backup.json
```

## 📏 Development Rules
1.  **Dependency Management**: Always use `uv` for adding/removing packages.
2.  **Database**: Use SQLModel for all database interactions. Ensure migrations are created for schema changes.
3.  **Hardware Safety**: When modifying `services.py`, ensure GPIO cleanup is handled to prevent hardware lockups.
4.  **Frontend**: Keep the UI lightweight. Use vanilla JS/CSS where possible to maintain performance on low-power devices (Pi).
5.  **Logging**: Use the configured logger in `main.py` for debugging and audit trails.

## 🔍 Common Tasks
- **Adding a new route**: Add to `main.py` and create a corresponding template in `templates/` if needed.
- **Modifying database schema**: Update `models.py` and create a migration script.
- **Adjusting hardware logic**: Edit `services.py`. Check `PIN_*` constants for GPIO mappings.

## 📚 References
- [README.md](file:///home/sdhui/projects/barcode_verification/README.md): General project documentation.
- [QUICK_REFERENCE.md](file:///home/sdhui/projects/barcode_verification/QUICK_REFERENCE.md): Production patches and deployment guide.
