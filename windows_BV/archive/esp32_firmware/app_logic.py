import json
import time
import os
from machine import Pin

# GPIO Setup
PIN_PASS = Pin(27, Pin.OUT)
PIN_FAIL = Pin(22, Pin.OUT)
PIN_ALARM = Pin(17, Pin.OUT)

# State
current_job = None
shift_stats = {
    "total_shippers": 0,
    "total_pieces": 0,
    "jobs_completed": 0
}

def load_state():
    global current_job, shift_stats
    try:
        with open('job.json', 'r') as f:
            current_job = json.load(f)
    except:
        current_job = None
        
    try:
        with open('shift.json', 'r') as f:
            shift_stats = json.load(f)
    except:
        pass

def save_state():
    if current_job:
        with open('job.json', 'w') as f:
            json.dump(current_job, f)
    else:
        try:
            os.remove('job.json')
        except:
            pass
            
    with open('shift.json', 'w') as f:
        json.dump(shift_stats, f)

def trigger_pass():
    PIN_PASS.on()
    time.sleep(0.5)
    PIN_PASS.off()

def trigger_fail():
    PIN_FAIL.on()
    PIN_ALARM.on()
    time.sleep(1.0)
    PIN_FAIL.off()
    PIN_ALARM.off()

# API Handlers
def get_status(body):
    return {
        "active_job": current_job,
        "shift": shift_stats
    }

def start_job(body):
    global current_job
    if current_job:
        return {"error": "Job already active"}
        
    current_job = {
        "job_id": body.get("job_id", f"JOB_{int(time.time())}"),
        "expected_barcode": body.get("expected_barcode"),
        "pieces_per_shipper": int(body.get("pieces_per_shipper", 1)),
        "target_quantity": int(body.get("target_quantity", 0)),
        "start_time": "00:00", # No RTC usually, simplified
        "pass_count": 0,
        "fail_count": 0,
        "total_scans": 0,
        "total_pieces": 0,
        "pass_rate": 100.0,
        "scans_this_hour": 0,
        "pieces_this_hour": 0,
        "scans_prev_hour": 0,
        "pieces_prev_hour": 0,
        "recent_scans": []
    }
    save_state()
    return {"success": True, "job": current_job}

def end_job(body):
    global current_job
    if not current_job:
        return {"error": "No active job"}
        
    # Update shift
    shift_stats["total_shippers"] += current_job["total_scans"]
    shift_stats["total_pieces"] += current_job["total_pieces"]
    shift_stats["jobs_completed"] += 1
    
    summary = current_job.copy()
    current_job = None
    save_state()
    
    return {"success": True, "summary": summary}

def scan_barcode(body):
    global current_job
    if not current_job:
        return {"error": "No active job"}
        
    barcode = body.get("barcode", "").strip()
    status = "FAIL"
    
    if barcode == current_job["expected_barcode"]:
        status = "PASS"
        current_job["pass_count"] += 1
        current_job["total_pieces"] += current_job["pieces_per_shipper"]
        current_job["scans_this_hour"] += 1
        current_job["pieces_this_hour"] += current_job["pieces_per_shipper"]
        trigger_pass()
    else:
        current_job["fail_count"] += 1
        trigger_fail()
        
    current_job["total_scans"] += 1
    if current_job["total_scans"] > 0:
        current_job["pass_rate"] = round((current_job["pass_count"] / current_job["total_scans"]) * 100, 1)
        
    # Add to history
    scan_record = {
        "status": status,
        "barcode": barcode,
        "timestamp": "00:00" # Placeholder
    }
    current_job["recent_scans"].insert(0, scan_record)
    current_job["recent_scans"] = current_job["recent_scans"][:10]
    
    save_state()
    
    return {
        "scan": scan_record,
        "job": current_job,
        "recent_scans": current_job["recent_scans"]
    }

def get_hourly_stats(body):
    # Simplified for ESP32 - just return current job stats
    # A full hourly log would require RTC and more complex storage
    return {} 
