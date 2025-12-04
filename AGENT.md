# Agent Guide

This file provides context for AI assistants working on this codebase.

## Project Overview

**Barcode Verification System v3.0** - A FastAPI production app for verifying master shipper barcodes on automatic carton sealers. Runs on Raspberry Pi (with GPIO) or Windows (simulation mode).

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, Uvicorn, SQLModel (SQLite)
- **Frontend**: Jinja2 templates, Vanilla JS, CSS (no build step)
- **Package Manager**: uv (astral)
- **Hardware**: GPIO via RPi.GPIO (optional)

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, all API routes, SSE events |
| `models.py` | SQLModel schemas (Job, Scan, ShiftStats) |
| `database.py` | Engine config, WAL mode, session helpers |
| `services.py` | GPIOController (pass/fail lights, buzzer) |
| `static/js/app.js` | Frontend JS with barcode scanner detection |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPERVISOR_PIN` | `1234` | PIN to end jobs/unlock line |
| `BACKUP_TOKEN` | None | Required for `/api/backup` and `/api/restore` |
| `USE_GPIO` | `false` | Enable RPi.GPIO hardware control |
| `LINE_NAME` | `Master Shipper Verify` | Displayed in header |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## API Endpoints

### Health & Monitoring
- `GET /health` - Full health check (DB, SSE count, stuck jobs)
- `GET /ready` - Simple readiness probe

### Jobs
- `POST /api/job/start` - Start a new verification job
- `POST /api/job/end` - End job (requires PIN)
- `GET /api/status` - Current job and shift stats

### Scanning
- `POST /api/scan` - Process a barcode scan
- `GET /api/events` - SSE stream for real-time updates

### Data
- `GET /api/backup` - Export state (requires `X-Backup-Token`)
- `POST /api/restore` - Restore from backup (destructive, requires token)
- `GET /api/export_csv` - Export 120-day history as CSV

## Running Tests

```bash
uv run pytest tests/ -v
```

## Common Tasks

### Adding a new API endpoint
1. Add route in `main.py`
2. Add Pydantic models in `models.py` if needed
3. Add tests in `tests/test_api.py`

### Modifying database schema
1. Update models in `models.py`
2. Create migration script if needed
3. Run migration before restarting app

## Security Features

- PIN rate limiting (5 attempts → 15 min lockout)
- Backup endpoints protected by `BACKUP_TOKEN`
- Input validation on all user inputs
- Client JS error boundary for graceful recovery

## Known Patterns

- **SSE queues**: Uses bounded `asyncio.Queue(maxsize=50)` per client
- **Cached counts**: `Job.cached_*` fields avoid counting scans on every request
- **Lock on fail**: Failed scans lock the line until supervisor PIN entered
