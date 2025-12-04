# IT Operations Guide

This guide is for IT staff responsible for maintaining the Barcode Verification System.

---

## 📋 System Overview

| Component | Details |
|-----------|---------|
| **Application** | Python FastAPI web application |
| **Database** | SQLite (single file: `barcode_verification.db`) |
| **Web Server** | Uvicorn on port 8000 |
| **Platform** | Windows PC or Raspberry Pi |

---

## 🔧 Daily Operations

### Morning Checks (5 minutes)

1. **Verify application is running**
   ```bash
   # Windows
   curl http://localhost:8000/health
   
   # Linux/Pi
   curl http://localhost:8000/health
   ```
   
   Expected response: `{"status":"healthy",...}`

2. **Check log file for errors**
   ```bash
   # Windows
   type logs\barcode_verification.log | findstr ERROR
   
   # Linux
   grep ERROR logs/barcode_verification.log
   ```

3. **Verify database size is reasonable**
   ```bash
   # Windows
   dir barcode_verification.db
   
   # Linux  
   ls -lh barcode_verification.db
   ```
   
   Database grows ~10MB per 100,000 scans.

### End of Day Checklist

- [ ] All lines have ended their jobs properly
- [ ] Daily backup completed (if not automated)
- [ ] No critical errors in logs
- [ ] Disk space adequate (>1GB free)

---

## 💾 Backup Procedures

### Automated Daily Backup (Recommended)

Create `backup.bat` (Windows) or `backup.sh` (Linux):

**Windows - backup.bat**
```batch
@echo off
set BACKUP_DIR=C:\backups\barcode_verification
set DATE=%date:~-4%%date:~-10,2%%date:~-7,2%
set TOKEN=YOUR_BACKUP_TOKEN_HERE

mkdir %BACKUP_DIR% 2>nul

:: Database file backup
copy barcode_verification.db %BACKUP_DIR%\db_%DATE%.db

:: API backup (includes all data in JSON format)
curl -H "X-Backup-Token: %TOKEN%" http://localhost:8000/api/backup -o %BACKUP_DIR%\data_%DATE%.json

echo Backup complete: %DATE%
```

**Linux - backup.sh**
```bash
#!/bin/bash
BACKUP_DIR=/home/pi/backups
DATE=$(date +%Y%m%d)
TOKEN="YOUR_BACKUP_TOKEN_HERE"

mkdir -p $BACKUP_DIR

# Database file backup
cp barcode_verification.db $BACKUP_DIR/db_$DATE.db

# API backup
curl -H "X-Backup-Token: $TOKEN" http://localhost:8000/api/backup -o $BACKUP_DIR/data_$DATE.json

echo "Backup complete: $DATE"
```

**Schedule the backup:**
- **Windows**: Task Scheduler → Run daily at 2:00 AM
- **Linux**: Add to crontab: `0 2 * * * /home/pi/barcode_verification/backup.sh`

### Manual Backup

```bash
# Quick database copy
cp barcode_verification.db backup_$(date +%Y%m%d_%H%M%S).db
```

### Backup Retention

Recommended retention policy:
| Backup Type | Retention |
|-------------|-----------|
| Daily backups | 7 days |
| Weekly backups | 4 weeks |
| Monthly backups | 12 months |

---

## 🔄 Restore Procedures

### Restore from Database File (Preferred)

1. **Stop the application**
   ```bash
   # Windows: Close the run.bat window or Ctrl+C
   # Linux: sudo systemctl stop barcode-verifier
   ```

2. **Replace the database**
   ```bash
   mv barcode_verification.db barcode_verification.db.broken
   cp /path/to/backup.db barcode_verification.db
   ```

3. **Start the application**
   ```bash
   # Windows: run.bat
   # Linux: sudo systemctl start barcode-verifier
   ```

### Restore from API Backup (JSON)

> ⚠️ **WARNING**: This is DESTRUCTIVE - it wipes the current database!

```bash
curl -X POST \
  -H "X-Backup-Token: YOUR_TOKEN" \
  -F "file=@backup.json" \
  http://localhost:8000/api/restore
```

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response includes:
- Database status
- Active SSE connections
- Stuck job warnings
- Memory usage

### Key Metrics to Watch

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Memory usage | <200MB | 200-500MB | >500MB |
| Database size | <100MB | 100-500MB | >1GB |
| Response time | <100ms | 100-500ms | >1s |
| Failed scans/hour | <5% | 5-10% | >10% |

### Log Monitoring

**Real-time log viewing:**
```bash
# Windows PowerShell
Get-Content logs\barcode_verification.log -Wait -Tail 50

# Linux
tail -f logs/barcode_verification.log
```

**Log levels:**
| Level | Meaning |
|-------|---------|
| DEBUG | Detailed debugging (usually disabled) |
| INFO | Normal operations |
| WARNING | Something unusual but not broken |
| ERROR | Something failed |
| CRITICAL | System is unusable |

---

## 🔄 Maintenance Tasks

### Weekly Tasks

1. **Review error logs**
   ```bash
   grep -c ERROR logs/barcode_verification.log
   ```

2. **Check disk space**
   ```bash
   # Windows
   wmic logicaldisk get size,freespace,caption
   
   # Linux
   df -h
   ```

3. **Verify backups are working**
   - Check backup folder has recent files
   - Test restore on a test system periodically

### Monthly Tasks

1. **Archive old logs**
   ```bash
   # Compress logs older than 30 days
   gzip logs/barcode_verification.log.old
   mv logs/*.gz /archive/logs/
   ```

2. **Database optimization** (optional)
   ```bash
   sqlite3 barcode_verification.db "VACUUM;"
   ```

3. **Update documentation** - Note any changes or issues

### Quarterly Tasks

1. **Test full disaster recovery**
   - Restore backup to test machine
   - Verify data integrity
   - Document any issues

2. **Review access controls**
   - Are PINs still secure?
   - Are backup tokens rotated?

---

## 🔒 Security Tasks

### Change Supervisor PIN

**Windows (run.bat):**
```batch
set SUPERVISOR_PIN=NewSecurePIN2024!
```

**Linux (barcode-verifier.service):**
```ini
Environment="SUPERVISOR_PIN=NewSecurePIN2024!"
```

Then restart the application.

### Rotate Backup Token

1. Generate new token:
   ```powershell
   # PowerShell
   -join ((48..57)+(65..90)+(97..122)|Get-Random -Count 32|%{[char]$_})
   ```

2. Update in configuration
3. Update any backup scripts that use the token

### Security Audit Checklist

- [ ] Default PIN (1234) is NOT in use
- [ ] Backup token is set and not default
- [ ] Firewall restricts port 8000 to local network
- [ ] Log files don't contain sensitive data in public areas
- [ ] Old backups are secured/encrypted

---

## 🚨 Emergency Procedures

### Application Won't Start

1. **Check port conflict**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux
   lsof -i :8000
   ```

2. **Check for database lock**
   ```bash
   # Delete lock files if any exist
   del barcode_verification.db-wal
   del barcode_verification.db-shm
   ```

3. **Check logs for errors**
   ```bash
   tail -100 logs/barcode_verification.log
   ```

### Database Corruption

1. **Stop the application immediately**
2. **Try database repair**
   ```bash
   sqlite3 barcode_verification.db ".dump" | sqlite3 repaired.db
   mv barcode_verification.db corrupted.db
   mv repaired.db barcode_verification.db
   ```
3. **If repair fails**: Restore from backup

### Production Line Down

**Priority 1: Get scanning working again**

1. Quick restart:
   ```bash
   # Windows: Close window, double-click run.bat
   # Linux: sudo systemctl restart barcode-verifier
   ```

2. If restart doesn't work, check health endpoint
3. If database issue, restore from last backup
4. Document incident for post-mortem

---

## 📞 Escalation Matrix

| Issue Severity | Response Time | Escalation |
|----------------|---------------|------------|
| Line down | Immediate | On-call IT → IT Manager |
| Data loss suspected | 15 minutes | IT Manager → Vendor |
| Slow performance | 1 hour | Regular IT ticket |
| Feature request | Next business day | IT ticket → Development |

---

## 📁 Important File Locations

### Windows
```
C:\barcode_verification\
├── main.py                    # Main application
├── barcode_verification.db    # Database
├── run.bat                    # Startup script
├── logs\                      # Log files
│   └── barcode_verification.log
└── backups\                   # Backup files (create this)
```

### Linux/Raspberry Pi
```
/home/pi/barcode_verification/
├── main.py                    # Main application
├── barcode_verification.db    # Database
├── barcode-verifier.service   # systemd service config
├── logs/                      # Log files
│   └── barcode_verification.log
└── backups/                   # Backup files
```

---

## 🔧 Common IT Tasks

### Restart the Application

**Windows:**
1. Close the run.bat window (or Ctrl+C)
2. Double-click run.bat

**Linux:**
```bash
sudo systemctl restart barcode-verifier
```

### Check if Application is Running

**Windows:**
```batch
tasklist | findstr python
```

**Linux:**
```bash
sudo systemctl status barcode-verifier
```

### View Live Connections

```bash
curl http://localhost:8000/health | jq .sse_connections
```

### Clear Old Jobs (if needed)

Use SQLite directly (with app stopped):
```sql
sqlite3 barcode_verification.db
DELETE FROM jobs WHERE date(start_time) < date('now', '-90 days');
DELETE FROM scans WHERE job_id NOT IN (SELECT job_id FROM jobs);
VACUUM;
.exit
```

---

*For technical development details, see [ENGINEERING_HANDOVER.md](ENGINEERING_HANDOVER.md)*
