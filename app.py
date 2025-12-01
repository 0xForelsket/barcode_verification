#!/usr/bin/env python3
"""
Barcode Verification System v3.0
================================
Web-based Master Shipper Label Verification System

Features:
- Flask web UI (accessible from any device on network)
- SQLite database for reliable data storage
- Real-time updates via Server-Sent Events
- Supervisor PIN for ending jobs
- Audio feedback on all scans
- GPIO relay control
- Remote monitoring
- Hourly counts for production boards
- Watchdog auto-restart

Hardware Setup:
- Raspberry Pi 4 (or any Linux/Windows PC)
- USB Barcode Scanner (keyboard wedge mode)
- Optional: GPIO relay module for alarm
- Optional: Touchscreen display

Usage:
    python3 app.py

Then open http://localhost:5000 (or http://<pi-ip>:5000 from any device)
"""

import os
import json
import threading
import time
from datetime import datetime, timedelta
from functools import wraps
from dataclasses import dataclass
from typing import Optional, Generator

from flask import (
    Flask, render_template, request, jsonify, 
    Response, session, redirect, url_for
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract

# ============================================================
# CONFIGURATION
# ============================================================

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production-abc123')
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///barcode_verification.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Supervisor PIN (change this!)
    SUPERVISOR_PIN = os.environ.get('SUPERVISOR_PIN', '1234')
    
    # GPIO Settings
    USE_GPIO = os.environ.get('USE_GPIO', 'false').lower() == 'true'
    PIN_ALARM_RELAY = 17
    PIN_PASS_LIGHT = 27
    PIN_FAIL_LIGHT = 22
    PIN_LINE_STOP = 23
    ALARM_DURATION = 3.0
    
    # Server
    HOST = '0.0.0.0'  # Listen on all interfaces for network access
    PORT = 5000
    DEBUG = False


# ============================================================
# APP INITIALIZATION
# ============================================================

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Global state for SSE
sse_subscribers = []


# ============================================================
# DATABASE MODELS
# ============================================================

class Job(db.Model):
    """A verification job/batch"""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), nullable=False)
    expected_barcode = db.Column(db.String(200), nullable=False)
    pieces_per_shipper = db.Column(db.Integer, default=1)
    target_quantity = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    scans = db.relationship('Scan', backref='job', lazy='dynamic')
    
    @property
    def pass_count(self) -> int:
        return self.scans.filter_by(status='PASS').count()
    
    @property
    def fail_count(self) -> int:
        return self.scans.filter_by(status='FAIL').count()
    
    @property
    def total_scans(self) -> int:
        return self.scans.count()
    
    @property
    def total_pieces(self) -> int:
        return self.pass_count * self.pieces_per_shipper
    
    @property
    def pass_rate(self) -> float:
        if self.total_scans == 0:
            return 100.0
        return (self.pass_count / self.total_scans) * 100
    
    @property
    def elapsed_seconds(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return int((datetime.now() - self.start_time).total_seconds())
    
    @property
    def progress_percent(self) -> float:
        if not self.target_quantity or self.target_quantity <= 0:
            return 0.0
        return min((self.pass_count / self.target_quantity) * 100, 100.0)

    @property
    def elapsed_formatted(self) -> str:
        seconds = self.elapsed_seconds
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def scans_in_hour(self, target_hour: int) -> int:
        """Get pass count for a specific clock hour (0-23) of today"""
        today = datetime.now().date()
        # Create range for that hour
        start_dt = datetime.combine(today, datetime.min.time().replace(hour=target_hour))
        end_dt = start_dt + timedelta(hours=1)
        
        return self.scans.filter(
            Scan.timestamp >= start_dt,
            Scan.timestamp < end_dt,
            Scan.status == 'PASS'
        ).count()
    
    @property
    def scans_this_hour(self) -> int:
        return self.scans_in_hour(datetime.now().hour)
        
    @property
    def scans_prev_hour(self) -> int:
        prev_hour = datetime.now().hour - 1
        if prev_hour < 0: return 0 # Don't go back to yesterday for simplicity
        return self.scans_in_hour(prev_hour)

    def recent_scans(self, limit=10):
        return self.scans.order_by(Scan.timestamp.desc()).limit(limit).all()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'job_id': self.job_id,
            'expected_barcode': self.expected_barcode,
            'pieces_per_shipper': self.pieces_per_shipper,
            'target_quantity': self.target_quantity,
            'start_time': self.start_time.strftime('%H:%M'),
            'is_active': self.is_active,
            'pass_count': self.pass_count,
            'fail_count': self.fail_count,
            'total_scans': self.total_scans,
            'total_pieces': self.total_pieces,
            'pass_rate': round(self.pass_rate, 1),
            'elapsed': self.elapsed_formatted,
            'scans_this_hour': self.scans_this_hour,
            'pieces_this_hour': self.scans_this_hour * self.pieces_per_shipper,
            'scans_prev_hour': self.scans_prev_hour,
            'pieces_prev_hour': self.scans_prev_hour * self.pieces_per_shipper,
        }


class Scan(db.Model):
    """A single barcode scan"""
    __tablename__ = 'scans'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    barcode = db.Column(db.String(200), nullable=False)
    expected = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # PASS or FAIL
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'barcode': self.barcode,
            'expected': self.expected,
            'status': self.status,
            'timestamp': self.timestamp.strftime('%H:%M:%S'),
        }


class ShiftStats(db.Model):
    """Daily shift statistics"""
    __tablename__ = 'shift_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.now().date, unique=True)
    total_shippers = db.Column(db.Integer, default=0)
    total_pieces = db.Column(db.Integer, default=0)
    total_pass = db.Column(db.Integer, default=0)
    total_fail = db.Column(db.Integer, default=0)
    jobs_completed = db.Column(db.Integer, default=0)
    
    @classmethod
    def get_today(cls):
        today = datetime.now().date()
        stats = cls.query.filter_by(date=today).first()
        if not stats:
            stats = cls(date=today)
            db.session.add(stats)
            db.session.commit()
        return stats
    
    def to_dict(self) -> dict:
        return {
            'total_shippers': self.total_shippers,
            'total_pieces': self.total_pieces,
            'total_pass': self.total_pass,
            'total_fail': self.total_fail,
            'jobs_completed': self.jobs_completed,
        }


# ============================================================
# GPIO CONTROLLER
# ============================================================

class GPIOController:
    """Handles GPIO operations for relays and indicators"""
    
    def __init__(self):
        self.initialized = False
        self.gpio = None
        
        if Config.USE_GPIO:
            try:
                import RPi.GPIO as GPIO
                self.gpio = GPIO
                self._setup()
            except ImportError:
                print("[GPIO] RPi.GPIO not available - running in simulation mode")
    
    def _setup(self):
        try:
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setwarnings(False)
            pins = [Config.PIN_ALARM_RELAY, Config.PIN_PASS_LIGHT, 
                    Config.PIN_FAIL_LIGHT, Config.PIN_LINE_STOP]
            for pin in pins:
                self.gpio.setup(pin, self.gpio.OUT)
                self.gpio.output(pin, self.gpio.LOW)
            self.initialized = True
            print("[GPIO] Initialized successfully")
        except Exception as e:
            print(f"[GPIO] Setup failed: {e}")
    
    def trigger_pass(self):
        if not self.initialized:
            print("[GPIO SIM] PASS")
            return
        self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.HIGH)
        self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.LOW)
        threading.Timer(1.0, lambda: self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.LOW)).start()
    
    def trigger_fail(self):
        if not self.initialized:
            print("[GPIO SIM] FAIL - ALARM!")
            return
        self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.HIGH)
        self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.LOW)
        self._trigger_alarm()
    
    def _trigger_alarm(self):
        def alarm_sequence():
            if self.initialized:
                self.gpio.output(Config.PIN_ALARM_RELAY, self.gpio.HIGH)
                time.sleep(Config.ALARM_DURATION)
                self.gpio.output(Config.PIN_ALARM_RELAY, self.gpio.LOW)
                self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.LOW)
        threading.Thread(target=alarm_sequence, daemon=True).start()
    
    def all_off(self):
        if self.initialized:
            pins = [Config.PIN_ALARM_RELAY, Config.PIN_PASS_LIGHT, 
                    Config.PIN_FAIL_LIGHT, Config.PIN_LINE_STOP]
            for pin in pins:
                self.gpio.output(pin, self.gpio.LOW)
    
    def cleanup(self):
        if self.initialized:
            self.all_off()
            self.gpio.cleanup()


# Initialize GPIO controller
gpio_controller = GPIOController()


# ============================================================
# SERVER-SENT EVENTS (Real-time updates)
# ============================================================

def notify_clients(event_type: str, data: dict):
    """Send update to all connected clients"""
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    dead_subscribers = []
    for subscriber in sse_subscribers:
        try:
            subscriber.put(message)
        except:
            dead_subscribers.append(subscriber)
    for sub in dead_subscribers:
        sse_subscribers.remove(sub)


class MessageQueue:
    """Simple message queue for SSE"""
    def __init__(self):
        self.messages = []
        self.event = threading.Event()
    
    def put(self, message):
        self.messages.append(message)
        self.event.set()
    
    def get(self, timeout=30):
        self.event.wait(timeout)
        self.event.clear()
        if self.messages:
            return self.messages.pop(0)
        return None


# ============================================================
# ROUTES - PAGES
# ============================================================

@app.route('/')
def index():
    """Main operator page"""
    active_job = Job.query.filter_by(is_active=True).first()
    shift = ShiftStats.get_today()
    return render_template('index.html', 
                          active_job=active_job,
                          shift=shift,
                          gpio_enabled=Config.USE_GPIO)


@app.route('/monitor')
def monitor():
    """Read-only monitoring page for supervisors"""
    active_job = Job.query.filter_by(is_active=True).first()
    shift = ShiftStats.get_today()
    recent_jobs = Job.query.order_by(Job.start_time.desc()).limit(10).all()
    return render_template('monitor.html',
                          active_job=active_job,
                          shift=shift,
                          recent_jobs=recent_jobs)


@app.route('/history')
def history():
    """Job history page"""
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.start_time.desc()).paginate(page=page, per_page=20)
    return render_template('history.html', jobs=jobs)


# ============================================================
# ROUTES - API
# ============================================================

@app.route('/api/job/start', methods=['POST'])
def start_job():
    """Start a new verification job"""
    data = request.json
    
    # Check for active job
    active = Job.query.filter_by(is_active=True).first()
    if active:
        return jsonify({'error': 'A job is already active. End it first.'}), 400
    
    # Validate
    expected = data.get('expected_barcode', '').strip()
    if not expected:
        return jsonify({'error': 'Expected barcode is required'}), 400
    
    job_id = data.get('job_id', '').strip()
    if not job_id:
        job_id = datetime.now().strftime('JOB_%Y%m%d_%H%M%S')
    
    pieces = data.get('pieces_per_shipper', 1)
    try:
        pieces = int(pieces)
        if pieces < 1:
            pieces = 1
    except:
        pieces = 1
    
    target = data.get('target_quantity', 0)
    try:
        target = int(target)
        if target < 0:
            target = 0
    except:
        target = 0
    
    # Create job
    job = Job(
        job_id=job_id,
        expected_barcode=expected,
        pieces_per_shipper=pieces,
        target_quantity=target,
        start_time=datetime.now(),
        is_active=True
    )
    db.session.add(job)
    db.session.commit()
    
    # Notify clients
    notify_clients('job_started', job.to_dict())
    
    return jsonify({'success': True, 'job': job.to_dict()})


@app.route('/api/job/end', methods=['POST'])
def end_job():
    """End the current job (requires supervisor PIN)"""
    data = request.json
    pin = data.get('pin', '')
    
    if pin != Config.SUPERVISOR_PIN:
        return jsonify({'error': 'Invalid supervisor PIN'}), 403
    
    job = Job.query.filter_by(is_active=True).first()
    if not job:
        return jsonify({'error': 'No active job'}), 400
    
    job.is_active = False
    job.end_time = datetime.now()
    
    # Update shift stats
    shift = ShiftStats.get_today()
    shift.total_shippers += job.total_scans
    shift.total_pieces += job.total_pieces
    shift.total_pass += job.pass_count
    shift.total_fail += job.fail_count
    shift.jobs_completed += 1
    
    db.session.commit()
    
    # Notify clients
    notify_clients('job_ended', {
        'job': job.to_dict(),
        'shift': shift.to_dict()
    })
    
    gpio_controller.all_off()
    
    return jsonify({
        'success': True, 
        'summary': {
            'job_id': job.job_id,
            'total_scans': job.total_scans,
            'total_pieces': job.total_pieces,
            'pass_count': job.pass_count,
            'fail_count': job.fail_count,
            'pass_rate': round(job.pass_rate, 1),
            'elapsed': job.elapsed_formatted
        }
    })


@app.route('/api/scan', methods=['POST'])
def process_scan():
    """Process a barcode scan"""
    data = request.json
    barcode = data.get('barcode', '').strip()
    
    if not barcode:
        return jsonify({'error': 'No barcode provided'}), 400
    
    job = Job.query.filter_by(is_active=True).first()
    if not job:
        return jsonify({'error': 'No active job'}), 400
    
    # Determine pass/fail
    status = 'PASS' if barcode == job.expected_barcode else 'FAIL'
    
    # Record scan
    scan = Scan(
        job_id=job.id,
        barcode=barcode,
        expected=job.expected_barcode,
        status=status,
        timestamp=datetime.now()
    )
    db.session.add(scan)
    db.session.commit()
    
    # Trigger GPIO
    if status == 'PASS':
        gpio_controller.trigger_pass()
    else:
        gpio_controller.trigger_fail()
    
    # Build response
    response_data = {
        'scan': scan.to_dict(),
        'job': job.to_dict(),
        'recent_scans': [s.to_dict() for s in job.recent_scans(8)]
    }
    
    # Notify all clients
    notify_clients('scan', response_data)
    
    return jsonify(response_data)


@app.route('/api/status')
def get_status():
    """Get current system status"""
    job = Job.query.filter_by(is_active=True).first()
    shift = ShiftStats.get_today()
    
    return jsonify({
        'active_job': job.to_dict() if job else None,
        'shift': shift.to_dict(),
        'gpio_enabled': Config.USE_GPIO,
        'server_time': datetime.now().strftime('%H:%M:%S')
    })


@app.route('/api/job/<int:job_db_id>')
def get_job(job_db_id):
    """Get job details"""
    job = Job.query.get_or_404(job_db_id)
    return jsonify({
        'job': job.to_dict(),
        'scans': [s.to_dict() for s in job.recent_scans(100)]
    })


@app.route('/api/hourly_stats')
def get_hourly_stats():
    """Get production stats grouped by hour (8AM - 8PM)"""
    today = datetime.now().date()
    
    # Query scans for today
    results = db.session.query(
        extract('hour', Scan.timestamp).label('hour'),
        func.count(Scan.id).label('count'),
        func.sum(Job.pieces_per_shipper).label('pieces')
    ).join(Job).filter(
        func.date(Scan.timestamp) == today,
        Scan.status == 'PASS'
    ).group_by('hour').all()
    
    # Initialize 8AM to 8PM (20:00)
    hourly_data = {h: {'shippers': 0, 'pieces': 0} for h in range(8, 21)}
    
    for r in results:
        hour = int(r.hour)
        if 8 <= hour <= 20:
            hourly_data[hour]['shippers'] = r.count
            hourly_data[hour]['pieces'] = int(r.pieces) if r.pieces else 0
            
    return jsonify(hourly_data)


@app.route('/api/events')
def sse_stream():
    """Server-Sent Events stream for real-time updates"""
    def generate():
        queue = MessageQueue()
        sse_subscribers.append(queue)
        try:
            while True:
                message = queue.get(timeout=30)
                if message:
                    yield message
                else:
                    # Heartbeat
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            sse_subscribers.remove(queue)
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("[DB] Database initialized")


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    init_db()
    print(f"""
╔════════════════════════════════════════════════════════════╗
║         BARCODE VERIFICATION SYSTEM v3.0                   ║
╠════════════════════════════════════════════════════════════╣
║  Local:   http://localhost:{Config.PORT}                          ║
║  Network: http://<your-ip>:{Config.PORT}                          ║
║                                                            ║
║  Supervisor PIN: {Config.SUPERVISOR_PIN}                                     ║
║  GPIO: {'ENABLED' if Config.USE_GPIO else 'SIMULATION MODE'}                                   ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True
        )
    finally:
        gpio_controller.cleanup()
