import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, SQLModel, func, delete
from sqlalchemy.exc import IntegrityError, OperationalError
import time

from database import engine, get_session
from models import (
    Job, Scan, ShiftStats,
    JobRead, ScanRead, ShiftStatsRead, StatusResponse,
    JobStartRequest, JobEndRequest, JobEndResponse, ScanRequest, ScanResultResponse
)
from services import gpio_controller

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
import logging
from logging.handlers import RotatingFileHandler
import os

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
log_file = os.environ.get('LOG_FILE', 'barcode_verification.log')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        RotatingFileHandler(
            f'logs/{log_file}',
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 80)
logger.info("Barcode Verification System Starting")
logger.info(f"Log level: {log_level}")
logger.info("=" * 80)

# ============================================================
# APP SETUP
# ============================================================

from pydantic import ValidationError

SUPERVISOR_PIN = os.environ.get('SUPERVISOR_PIN', '1234')
USE_GPIO = os.environ.get('USE_GPIO', 'false').lower() == 'true'
LINE_NAME = os.environ.get('LINE_NAME', 'Master Shipper Verify')

# ============================================================
# LIFECYCLE
# ============================================================

# ============================================================
# PIN RATE LIMITING
# ============================================================

# Store PIN attempts: {ip_address: [timestamp1, timestamp2, ...]}
# Note: This is in-memory and resets on server restart
# For multi-process deployment, use Redis or database instead
pin_attempts: dict[str, list[datetime]] = defaultdict(list)

# Configuration
MAX_PIN_ATTEMPTS = 5
PIN_LOCKOUT_MINUTES = 15

def check_pin_rate_limit(ip: str) -> tuple[bool, str]:
    """
    Check if IP address is allowed to attempt PIN entry.
    
    Returns:
        (allowed: bool, message: str)
    """
    now = datetime.now()
    attempts = pin_attempts[ip]
    
    # Clean up old attempts (older than lockout period)
    cutoff_time = now - timedelta(minutes=PIN_LOCKOUT_MINUTES)
    attempts[:] = [t for t in attempts if t > cutoff_time]
    
    # Check if limit exceeded
    if len(attempts) >= MAX_PIN_ATTEMPTS:
        # Find when the lockout will expire
        oldest_attempt = min(attempts)
        unlock_time = oldest_attempt + timedelta(minutes=PIN_LOCKOUT_MINUTES)
        minutes_remaining = int((unlock_time - now).total_seconds() / 60) + 1
        
        logger.warning(
            f"PIN rate limit exceeded for IP: {ip} "
            f"({len(attempts)} attempts in last {PIN_LOCKOUT_MINUTES} minutes)"
        )
        
        return False, f"Too many PIN attempts. Try again in {minutes_remaining} minutes."
    
    return True, ""

def record_pin_attempt(ip: str, success: bool):
    """Record a PIN attempt for rate limiting."""
    now = datetime.now()
    pin_attempts[ip].append(now)
    
    if not success:
        logger.warning(
            f"Failed PIN attempt from {ip} "
            f"(attempt {len(pin_attempts[ip])} of {MAX_PIN_ATTEMPTS})"
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup initiated")
    shutdown_event.clear()
    
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}", exc_info=True)
        raise
    
    # Ensure ShiftStats for today exists
    with Session(engine) as session:
        today = datetime.now().date()
        stats = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
        if not stats:
            try:
                stats = ShiftStats(date=today)
                session.add(stats)
                session.commit()
                logger.info(f"Created ShiftStats for {today}")
            except IntegrityError:
                session.rollback()
                logger.debug("ShiftStats already exists (race condition)")
                # Another process created it, that's fine
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown
    logger.info("Application shutdown initiated")
    shutdown_event.set()
    gpio_controller.cleanup()
    logger.info("Application shutdown complete")

app = FastAPI(title="Barcode Verification System", version="3.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# SSE Queue
sse_queues: List[asyncio.Queue] = []
shutdown_event = asyncio.Event()

async def notify_clients(event_type: str, data: dict):
    """Send update to all connected clients"""
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    for queue in sse_queues:
        await queue.put(message)

# ============================================================
# LIFECYCLE
# ============================================================



# ============================================================
# ROUTES - PAGES
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    active_job = session.exec(select(Job).where(Job.is_active == True)).first()
    today = datetime.now().date()
    shift = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
    
    # Convert to Read models for template context if needed, or pass objects directly
    # Templates expect object access like active_job.job_id
    # We need to ensure computed properties are available on the object passed to Jinja
    
    return templates.TemplateResponse(
        request=request, name="index.html", context={
        "active_job": active_job,
        "shift": shift,
        "line_name": LINE_NAME,
        "gpio_enabled": USE_GPIO
    })

# ============================================================
# ROUTES - API
# ============================================================

@app.get("/api/status", response_model=StatusResponse)
async def get_status(session: Session = Depends(get_session)):
    active_job = session.exec(select(Job).where(Job.is_active == True)).first()
    today = datetime.now().date()
    shift = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
    
    return StatusResponse(
        active_job=JobRead.from_job(active_job) if active_job else None,
        shift=shift,
        gpio_enabled=USE_GPIO,
        server_time=datetime.now().strftime('%H:%M:%S')
    )

@app.get("/api/hourly_stats")
async def get_hourly_stats(session: Session = Depends(get_session)):
    today = datetime.now().date()
    # Simple implementation: fetch all scans for today and aggregate in python
    # For high volume, use SQL aggregation
    scans = session.exec(select(Scan).where(
        Scan.timestamp >= datetime.combine(today, datetime.min.time()),
        Scan.status == 'PASS'
    )).all()
    
    hourly_data = {h: {'shippers': 0, 'pieces': 0} for h in range(8, 21)}
    
    # We need job info for pieces calculation
    # Let's pre-fetch jobs to avoid N+1
    jobs = {j.id: j for j in session.exec(select(Job)).all()}
    
    for scan in scans:
        h = scan.timestamp.hour
        if 8 <= h <= 20:
            hourly_data[h]['shippers'] += 1
            job = jobs.get(scan.job_id)
            if job:
                hourly_data[h]['pieces'] += job.pieces_per_shipper
    
    # Calculate cumulative
    running_total = 0
    for h in range(8, 21):
        running_total += hourly_data[h]['pieces']
        hourly_data[h]['cumulative'] = running_total
                
    return hourly_data

@app.post("/api/job/start")
async def start_job(request: JobStartRequest, session: Session = Depends(get_session)):
    logger.info(f"Job start request: job_id={request.job_id}, barcode={request.expected_barcode[:20]}...")
    
    # Validate input
    if not request.expected_barcode.strip():
        logger.warning("Job start failed: empty barcode")
        return JSONResponse(status_code=400, content={'error': 'Expected barcode is required'})
    
    # Generate job_id if not provided
    job_id = request.job_id
    if not job_id or not job_id.strip():
        job_id = datetime.now().strftime('JOB_%Y%m%d_%H%M%S')
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Use nested transaction for atomic check-and-create
            session.begin_nested()
            
            # Check for active job with SELECT FOR UPDATE
            # This locks the row(s) to prevent race conditions
            active = session.exec(
                select(Job)
                .where(Job.is_active == True)
                .with_for_update()
            ).first()
            
            if active:
                session.rollback()
                logger.warning(f"Cannot start job - active job exists: {active.job_id}")
                return JSONResponse(
                    status_code=400, 
                    content={'error': f'A job is already active: {active.job_id}. End it first.'}
                )
            
            # No active job - create new one
            job = Job(
                job_id=job_id,
                expected_barcode=request.expected_barcode,
                pieces_per_shipper=max(1, request.pieces_per_shipper),
                target_quantity=max(0, request.target_quantity),
                start_time=datetime.now(),
                is_active=True
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            
            logger.info(f"Job started successfully: job_id={job.job_id}, id={job.id}")
            
            # Notify connected clients
            job_read = JobRead.from_job(job)
            await notify_clients('job_started', job_read.model_dump())
            
            return {'success': True, 'job': job_read}
            
        except OperationalError as e:
            # Handle database locked errors (SQLite specific)
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retry {attempt + 1}/{max_retries}")
                session.rollback()
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                continue
            else:
                logger.error(f"Failed to start job after {attempt + 1} attempts: {e}", exc_info=True)
                session.rollback()
                return JSONResponse(
                    status_code=500, 
                    content={'error': 'Database error. Please try again.'}
                )
        except Exception as e:
            logger.error(f"Unexpected error starting job: {e}", exc_info=True)
            session.rollback()
            return JSONResponse(
                status_code=500, 
                content={'error': 'Failed to start job. Please try again.'}
            )
    
    # Should never reach here, but just in case
    logger.error("Failed to start job after all retries")
    return JSONResponse(
        status_code=500, 
        content={'error': 'Failed to start job after multiple attempts'}
    )

@app.post("/api/verify_pin")
async def verify_pin(req_data: JobEndRequest, request: Request):
    """Verify supervisor PIN with rate limiting."""
    client_ip = request.client.host
    
    # Check rate limit
    allowed, message = check_pin_rate_limit(client_ip)
    if not allowed:
        logger.warning(f"PIN verification blocked for {client_ip}: rate limit exceeded")
        return JSONResponse(
            status_code=429,  # Too Many Requests
            content={'error': message}
        )
    
    # Verify PIN
    success = (req_data.pin == SUPERVISOR_PIN)
    record_pin_attempt(client_ip, success)
    
    if not success:
        logger.warning(f"Invalid PIN attempt from {client_ip}")
        return JSONResponse(
            status_code=403,
            content={'error': 'Invalid supervisor PIN'}
        )
    
    logger.info(f"PIN verified successfully from {client_ip}")
    return {'success': True}

@app.post("/api/job/end", response_model=JobEndResponse)
async def end_job(
    req_data: JobEndRequest, 
    request: Request,
    session: Session = Depends(get_session)
):
    """End the active job with PIN verification and rate limiting."""
    client_ip = request.client.host
    logger.info(f"Job end request from {client_ip}")
    
    # Check rate limit
    allowed, message = check_pin_rate_limit(client_ip)
    if not allowed:
        logger.warning(f"Job end blocked for {client_ip}: rate limit exceeded")
        return JSONResponse(
            status_code=429,
            content={'error': message}
        )
    
    # Verify PIN
    success = (req_data.pin == SUPERVISOR_PIN)
    record_pin_attempt(client_ip, success)
    
    if not success:
        logger.warning(f"Invalid PIN for job end from {client_ip}")
        return JSONResponse(
            status_code=403,
            content={'error': 'Invalid supervisor PIN'}
        )
    
    # PIN verified - proceed with ending job
    try:
        job = session.exec(select(Job).where(Job.is_active == True)).first()
        if not job:
            logger.error(f"Job end attempted with no active job from {client_ip}")
            return JSONResponse(status_code=400, content={'error': 'No active job'})
        
        job.is_active = False
        job.end_time = datetime.now()
        session.add(job)
        
        # Update shift
        today = datetime.now().date()
        shift = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
        if not shift:
            try:
                shift = ShiftStats(date=today)
                session.add(shift)
                session.flush()
            except IntegrityError:
                session.rollback()
                shift = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
        
        shift.total_shippers += job.total_scans
        shift.total_pieces += job.total_pieces
        shift.total_pass += job.pass_count
        shift.total_fail += job.fail_count
        shift.jobs_completed += 1
        session.add(shift)
        
        session.commit()
        session.refresh(job)
        
        logger.info(
            f"Job ended successfully: job_id={job.job_id}, "
            f"scans={job.total_scans}, pass_rate={job.pass_rate:.1f}%"
        )
        
        job_read = JobRead.from_job(job)
        await notify_clients('job_ended', {
            'job': job_read.model_dump(),
            'shift': shift.model_dump()
        })
        
        gpio_controller.all_off()
        
        return JobEndResponse(
            success=True,
            summary={
                'job_id': job.job_id,
                'total_scans': job.total_scans,
                'total_pieces': job.total_pieces,
                'pass_count': job.pass_count,
                'fail_count': job.fail_count,
                'pass_rate': round(job.pass_rate, 1),
                'elapsed': job.elapsed_formatted
            }
        )
        
    except Exception as e:
        logger.error(f"Job end failed: {e}", exc_info=True)
        session.rollback()
        raise

@app.post("/api/log_error")
async def log_client_error(request: Request):
    """Log JavaScript errors from client"""
    try:
        data = await request.json()
        error_msg = data.get('error', 'Unknown error')
        stack = data.get('stack', 'No stack trace')
        logger.error(f"Client-side error: {error_msg}\nStack: {stack}")
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Failed to log client error: {e}")
        return {"status": "failed"}

@app.post("/api/scan", response_model=ScanResultResponse)
async def process_scan(request: ScanRequest, session: Session = Depends(get_session)):
    barcode = request.barcode.strip()
    logger.debug(f"Scan request: barcode={barcode[:20]}...")
    
    try:
        if not barcode:
            logger.warning("Empty barcode received")
            return JSONResponse(status_code=400, content={'error': 'No barcode provided'})
        
        job = session.exec(select(Job).where(Job.is_active == True)).first()
        if not job:
            logger.error("Scan attempted with no active job")
            return JSONResponse(status_code=400, content={'error': 'No active job'})
        
        status = 'PASS' if barcode == job.expected_barcode else 'FAIL'
        logger.info(f"Scan processed: job={job.job_id}, status={status}, barcode={barcode[:20]}...")
        
        scan = Scan(
            job_id=job.id,
            barcode=barcode,
            expected=job.expected_barcode,
            status=status,
            timestamp=datetime.now()
        )
        session.add(scan)
        
        # UPDATE CACHED COUNTS - THIS IS THE KEY CHANGE
        job.cached_total_scans += 1
        if status == 'PASS':
            job.cached_pass_count += 1
        else:
            job.cached_fail_count += 1
        
        session.add(job)
        session.commit()
        session.refresh(scan)
        session.refresh(job)
        
        # Trigger GPIO
        if status == 'PASS':
            gpio_controller.trigger_pass()
        else:
            gpio_controller.trigger_fail()
            
        # Prepare response
        response_data = ScanResultResponse(
            scan=ScanRead.from_scan(scan),
            job=JobRead.from_job(job),
            recent_scans=[ScanRead.from_scan(s) for s in job.recent_scans(8)]
        )
        
        # Notify clients
        await notify_clients('scan', json.loads(response_data.model_dump_json()))
        
        return response_data
        
    except Exception as e:
        logger.error(f"Scan processing failed: {e}", exc_info=True)
        session.rollback()
        raise

@app.get("/monitor", response_class=HTMLResponse)
async def monitor(request: Request, session: Session = Depends(get_session)):
    active_job = session.exec(select(Job).where(Job.is_active == True)).first()
    today = datetime.now().date()
    shift = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
    recent_jobs = session.exec(select(Job).order_by(Job.start_time.desc()).limit(10)).all()
    
    return templates.TemplateResponse(
        request=request, name="monitor.html", context={
        "active_job": active_job,
        "shift": shift,
        "recent_jobs": recent_jobs
    })

@app.get("/history", response_class=HTMLResponse)
async def history(request: Request, page: int = 1, session: Session = Depends(get_session)):
    limit = 20
    offset = (page - 1) * limit
    total_jobs = session.exec(select(func.count(Job.id))).one()
    jobs = session.exec(select(Job).order_by(Job.start_time.desc()).offset(offset).limit(limit)).all()
    
    import math
    total_pages = math.ceil(total_jobs / limit)
    
    # Mock pagination object for Jinja
    class Pagination:
        def __init__(self, items, page, pages, has_next, has_prev, next_num, prev_num):
            self.items = items
            self.page = page
            self.pages = pages
            self.has_next = has_next
            self.has_prev = has_prev
            self.next_num = next_num
            self.prev_num = prev_num
            
            self.iter_pages = lambda: range(1, pages + 1) # Simplified
            
    pagination = Pagination(
        items=jobs,
        page=page,
        pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
        next_num=page + 1,
        prev_num=page - 1
    )

    return templates.TemplateResponse(
        request=request, name="history.html", context={
        "jobs": pagination, 
        "page": page
    })

@app.get("/api/job/{job_db_id}")
async def get_job(job_db_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_db_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job": JobRead.from_job(job),
        "scans": [ScanRead.from_scan(s) for s in job.recent_scans(100)]
    }

@app.get("/api/export_csv")
async def export_csv(session: Session = Depends(get_session)):
    import csv
    import io
    from datetime import timedelta
    
    # 120 Days Lookback
    cutoff_date = datetime.now() - timedelta(days=120)
    
    # Fetch all jobs (Active + History)
    jobs = session.exec(select(Job).where(Job.start_time >= cutoff_date).order_by(Job.start_time.desc())).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    
    # Header
    cw.writerow(['Job ID', 'Start Time', 'Expected Barcode', 'Scan Timestamp', 'Scanned Barcode', 'Status'])
    
    for job in jobs:
        # Sort scans for this job
        job_scans = sorted(job.scans, key=lambda x: x.timestamp)
        
        if not job_scans:
            # Write at least one row for the job if it has no scans
            cw.writerow([
                job.job_id,
                job.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                job.expected_barcode,
                'NO SCANS',
                '',
                ''
            ])
            continue
            
        for scan in job_scans:
            cw.writerow([
                job.job_id,
                job.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                job.expected_barcode,
                scan.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                scan.barcode,
                scan.status
            ])
            
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    filename = f"barcode_history_120d_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.get("/api/backup")
async def backup_data(session: Session = Depends(get_session)):
    active_job = session.exec(select(Job).where(Job.is_active == True)).first()
    today = datetime.now().date()
    shift_stats = session.exec(select(ShiftStats).where(ShiftStats.date == today)).first()
    
    state = {
        'shift_stats': {
            'total_shippers': shift_stats.total_shippers if shift_stats else 0,
            'total_pieces': shift_stats.total_pieces if shift_stats else 0,
            'jobs_completed': shift_stats.jobs_completed if shift_stats else 0,
            'total_pass': shift_stats.total_pass if shift_stats else 0,
            'total_fail': shift_stats.total_fail if shift_stats else 0,
            'date': shift_stats.date.isoformat() if shift_stats else today.isoformat()
        },
        'active_job': None
    }
    
    if active_job:
        job_scans = sorted(active_job.scans, key=lambda x: x.timestamp)
        state['active_job'] = {
            'job_id': active_job.job_id,
            'expected_barcode': active_job.expected_barcode,
            'pieces_per_shipper': active_job.pieces_per_shipper,
            'target_quantity': active_job.target_quantity,
            'start_time': active_job.start_time.isoformat(),
            'pass_count': active_job.pass_count,
            'fail_count': active_job.fail_count,
            'total_scans': active_job.total_scans,
            'total_pieces': active_job.total_pieces,
            'is_active': active_job.is_active,
            'end_time': active_job.end_time.isoformat() if active_job.end_time else None,
            'recent_scans': [
                {
                    'barcode': s.barcode,
                    'status': s.status,
                    'timestamp': s.timestamp.isoformat(),
                    'expected': s.expected
                } for s in job_scans
            ]
        }
        
    filename = f"barcode_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return Response(
        json.dumps(state, indent=2),
        media_type='application/json',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )

@app.post("/api/restore")
async def restore_data(file: UploadFile = File(...), session: Session = Depends(get_session)):
    try:
        contents = await file.read()
        data = json.loads(contents)
        
        # Clear existing data using SQLModel/SQLAlchemy 2.0 syntax
        session.exec(delete(Scan))
        session.exec(delete(Job))
        session.exec(delete(ShiftStats))
        session.commit()
        
        # Restore Shift Stats
        if 'shift_stats' in data:
            shift_data = data['shift_stats']
            shift = ShiftStats(
                date=datetime.fromisoformat(shift_data['date']).date(),
                total_shippers=shift_data.get('total_shippers', 0),
                total_pieces=shift_data.get('total_pieces', 0),
                total_pass=shift_data.get('total_pass', 0),
                total_fail=shift_data.get('total_fail', 0),
                jobs_completed=shift_data.get('jobs_completed', 0)
            )
            session.add(shift)
            
        # Restore Active Job
        if data.get('active_job'):
            job_data = data['active_job']
            job = Job(
                job_id=job_data['job_id'],
                expected_barcode=job_data['expected_barcode'],
                pieces_per_shipper=job_data['pieces_per_shipper'],
                target_quantity=job_data['target_quantity'],
                start_time=datetime.fromisoformat(job_data['start_time']),
                is_active=job_data.get('is_active', False),
                end_time=datetime.fromisoformat(job_data['end_time']) if job_data.get('end_time') else None
            )
            session.add(job)
            session.flush() # Get ID
            
            for s in job_data.get('recent_scans', []):
                scan = Scan(
                    job_id=job.id,
                    barcode=s['barcode'],
                    expected=s['expected'],
                    status=s['status'],
                    timestamp=datetime.fromisoformat(s['timestamp'])
                )
                session.add(scan)
        
        session.commit()
        await notify_clients('restore_complete', {'success': True})
        return {'success': True}
        
    except Exception as e:
        session.rollback()
        return JSONResponse(status_code=500, content={'error': str(e)})

@app.get("/api/events")
async def sse_stream(request: Request):
    async def event_generator():
        queue = asyncio.Queue()
        sse_queues.append(queue)
        try:
            while not shutdown_event.is_set():
                if await request.is_disconnected():
                    break
                
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=1.0)  # shorter timeout
                    yield message
                except asyncio.TimeoutError:
                    if shutdown_event.is_set():
                        break
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            # Handle server shutdown or client disconnect cancellation
            pass
        finally:
            if queue in sse_queues:
                sse_queues.remove(queue)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)
