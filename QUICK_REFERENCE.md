# QUICK REFERENCE - Production Deployment Patches

## 🚨 Pre-Deployment Checklist

```
□ All 10 patches applied and tested
□ SUPERVISOR_PIN changed from "1234"
□ BACKUP_TOKEN set to random 32-char string
□ Migration script run (Patch #4)
□ Logs directory created
□ All tests passing
□ Health check returns 200
□ 8-hour burn-in test completed
```

## ⚡ Quick Apply - All Patches (6 hours total)

### Phase 1: Critical Security (1.5 hrs)
```bash
# BACKUP FIRST
copy barcode_verification.db backup_%date%.db

# Patch 1 - Logging (20 min)
# Patch 2 - Race Condition (30 min)  
# Patch 3 - PIN Rate Limit (40 min)

# Change PIN in run.bat!
set SUPERVISOR_PIN=NewSecurePin123
```

### Phase 2: Performance & Validation (2.5 hrs)
```bash
# Patch 4 - Cached Counts (45 min)
# STOP APP, run migration, START APP

# Patch 5 - Input Validation (30 min)
# Patch 6 - SSE Memory Leak (45 min)
# Patch 7 - JS Error Boundary (30 min)
```

### Phase 3: Polish (1 hr)
```bash
# Patches 8, 9, 10 from combined file (60 min)

# Set backup token in run.bat
set BACKUP_TOKEN=Random32CharTokenHere123456
```

## 🔧 Essential Commands

```bash
# Start application
run.bat

# Check health
curl http://localhost:8000/health

# View logs
type logs\barcode_verification.log | more

# Backup database
curl -H "X-Backup-Token: YOUR_TOKEN" http://localhost:8000/api/backup -o backup.json

# Run migration (Patch #4 only)
uv run python migrate_add_cached_counts.py

# Run tests
uv run pytest tests/
```

## 🐛 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "Database is locked" | Stop app, delete .db-wal/.db-shm, restart |
| "Module has no attribute" | Check for typos, restart app completely |
| Memory growing | Verify Patch #6 applied (bounded queues) |
| Wrong counts | Run Patch #4 migration script |
| Can't access /api/backup | Set BACKUP_TOKEN in environment |
| SSE not working | Check browser console, verify Patch #6 |
| Health check 503 | Check database connectivity |

## 📊 Monitoring Basics

```bash
# Check if running
tasklist | findstr python

# Monitor memory (watch for growth)
# Open Task Manager → Details → python.exe

# Watch logs in real-time
powershell Get-Content logs\barcode_verification.log -Wait -Tail 20

# Disk space
dir barcode_verification.db
```

## 🔄 Emergency Rollback

```bash
# Stop application (Ctrl+C or close window)

# Restore database
del barcode_verification.db
copy backup_%date%.db barcode_verification.db

# Restore code
xcopy /E /I /Y barcode_verification_backup\* barcode_verification\

# Restart
run.bat
```

## 🎯 Files Changed by Each Patch

| Patch | Files | Restart Required |
|-------|-------|------------------|
| 1 | main.py | Yes |
| 2 | main.py | Yes |
| 3 | main.py, run.bat | Yes |
| 4 | models.py, main.py, +migration | Yes + migration |
| 5 | models.py | Yes |
| 6 | main.py | Yes |
| 7 | static/js/app.js | No (refresh browser) |
| 8 | database.py | Yes |
| 9 | main.py | Yes |
| 10 | main.py, run.bat | Yes |

## 🔒 Security Configuration

**In run.bat, set these:**
```batch
set SUPERVISOR_PIN=YourSecurePin2024!
set BACKUP_TOKEN=YourRandom32CharToken12345678901
set ADMIN_KEY=YourAdminKeyHere12345678901234
set LOG_LEVEL=INFO
```

**Generate random tokens (PowerShell):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

## 📈 Success Metrics

After deployment, verify:
- ✅ Uptime > 8 hours continuous
- ✅ Memory usage stable (<500MB)
- ✅ No "database locked" errors
- ✅ Logs show no ERROR level messages
- ✅ Health check always returns 200
- ✅ Can scan 1000+ barcodes without issues
- ✅ Multiple users can work simultaneously

## 📞 If Something Breaks

1. Check `logs\barcode_verification.log` for errors
2. Try restarting: Ctrl+C, then `run.bat`
3. Check health: `curl http://localhost:8000/health`
4. If database issues: restore from backup
5. If code issues: restore from backup_folder

## 💾 Backup Strategy

```batch
:: Daily backup script (save as backup.bat)
@echo off
set BACKUP_DIR=backups
set DATE=%date:~-4%%date:~-10,2%%date:~-7,2%
mkdir %BACKUP_DIR% 2>nul
copy barcode_verification.db %BACKUP_DIR%\db_%DATE%.db
curl -H "X-Backup-Token: YOUR_TOKEN" http://localhost:8000/api/backup -o %BACKUP_DIR%\data_%DATE%.json
echo Backup complete: %DATE%

:: Schedule with Task Scheduler to run daily at 2 AM
```

## 🚀 Performance Expectations

**After all patches:**
- Start time: <5 seconds
- Scan processing: <100ms
- Health check: <50ms
- Memory usage: 100-200MB stable
- Concurrent users: 10+ supported
- Database size: ~10MB per 100,000 scans

## ✨ You're Ready When...

- [ ] All patches applied
- [ ] Tests passing
- [ ] Logs show "Application startup complete"
- [ ] Health endpoint returns `{"status":"healthy"}`
- [ ] Can scan barcodes successfully
- [ ] Can start and end jobs
- [ ] Wrong PIN gets rate limited
- [ ] Backup requires authentication
- [ ] Ran 8+ hours without errors
- [ ] Supervisor trained on system

---

**Now proceed to production with confidence! 🎉**

For detailed instructions, see README.md in the patches directory.
