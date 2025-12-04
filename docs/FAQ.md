# Frequently Asked Questions (FAQ)

Quick answers to common questions from operators, supervisors, and IT staff.

---

## 🧑‍🔧 Operator Questions

### How do I start a job?
1. Enter the Job ID (work order number)
2. Enter or scan the expected barcode
3. Select pieces per shipper (usually 1)
4. Click **START JOB**

### What do I do when I get a FAIL?
1. **Stop scanning immediately**
2. Check if the label on the carton is correct
3. If wrong label: Remove carton, set aside for relabeling
4. If label looks correct: Try scanning again (sometimes scanners misread)
5. If it keeps failing: Call your supervisor

### Can I fix a wrong scan?
No, scans cannot be edited or deleted. This is by design to maintain data integrity. If you scanned something incorrectly, tell your supervisor - they can note it in the job history.

### Why is there no sound when I scan?
1. Click anywhere on the webpage first (browsers sometimes block sound until you interact)
2. Check your computer/tablet volume
3. Make sure speakers aren't muted
4. Try refreshing the page (F5)

### I entered the wrong barcode when starting the job. What do I do?
You'll need to **END** the current job (requires supervisor PIN) and start a new one with the correct barcode.

### How do I know if the scanner is working?
The scanner should beep and flash when it reads a barcode. Try scanning any barcode (even on a package or document) - if the scanner beeps, it's working.

---

## 👔 Supervisor Questions

### How do I see completed jobs?
Click **History** in the top menu. You can search by Job ID or date.

### What is the supervisor PIN?
The PIN protects job ending and prevents operators from accidentally closing jobs. Ask your IT department if you don't know the PIN.

> ⚠️ The default PIN is `1234` - this should be changed for production!

### Can supervisors monitor from their desk?
Yes! Go to `http://<device-ip>:8000/monitor` from any browser on your network. This shows a read-only dashboard.

### How do I see today's production totals?
The **Monitor** page (`/monitor`) shows:
- Current job progress
- Hourly counts
- Today's shift totals
- Recent job history

### What happens if power goes out during a job?
The database automatically saves after every scan. When power returns and the app restarts, the job will still be there (marked as "stuck" if it wasn't properly ended). You can end it normally.

### How do I change the supervisor PIN?
Contact IT. The PIN is set in the system configuration files (`run.bat` on Windows or `barcode-verifier.service` on Linux).

---

## 💻 IT Questions

### What ports does this application use?
- **Port 8000** - Web server (main application)
- No other ports required

### Where is data stored?
All data is in `barcode_verification.db` (SQLite database file) in the application folder.

### How do I backup the database?
**Quick backup:**
```bash
cp barcode_verification.db backup_$(date +%Y%m%d).db
```

**API backup (with full data export):**
```bash
curl -H "X-Backup-Token: YOUR_TOKEN" http://localhost:8000/api/backup -o backup.json
```

### How do I restore from a backup?
1. Stop the application
2. Replace `barcode_verification.db` with your backup file
3. Start the application

### How do I check if the application is healthy?
```bash
curl http://localhost:8000/health
```
Should return `{"status":"healthy", ...}`

### The application won't start. What do I check?
1. **Port in use?** Check if another app is using port 8000
2. **Database locked?** Delete `.db-wal` and `.db-shm` files if they exist
3. **Check logs**: `logs/barcode_verification.log`
4. **Try restarting**: Close the window and run `run.bat` again

### How much disk space does this need?
- Application: ~50MB
- Database: ~10MB per 100,000 scans
- Logs: Depends on activity (recommend log rotation)

### Can multiple people use it at once?
Yes! Multiple browsers can connect simultaneously:
- One operator screen (actively scanning)
- Multiple monitor screens (read-only viewing)

---

## 🔧 Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Scanner won't scan | Check USB connection, try unplugging/replugging |
| No sound | Click the page, check volume, refresh browser |
| Screen frozen | Wait 10 seconds, then restart application |
| Wrong barcode entered | End job and start new one with correct barcode |
| "Database locked" error | Stop all instances, delete lock files, restart |
| Can't access from network | Check IP address, ensure port 8000 is open |
| Forgot supervisor PIN | Contact IT to reset it |
| High fail rate | Check label quality, scanner cleanliness, and expected barcode |

---

## 📞 Contact

| Issue Type | Who to Contact |
|------------|----------------|
| Wrong labels on products | Line Supervisor |
| Scanner hardware issues | IT Department |
| Application down | IT Department |
| Password/PIN issues | IT Department |
| Process questions | Line Supervisor |

---

*For detailed guides, see:*
- [Operator Guide](OPERATOR_GUIDE.md)
- [IT Operations Guide](IT_OPERATIONS.md)
- [Windows Setup](WINDOWS_SETUP.md)
