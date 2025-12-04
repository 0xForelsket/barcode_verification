# Operator Guide

This guide is for line operators who will use the Barcode Verification System daily.

---

## 📱 Quick Reference Card

| Action | How To |
|--------|--------|
| Start a job | Enter Job ID + Barcode → Click **START JOB** |
| Scan a barcode | Point scanner at label, pull trigger |
| Pass scan | ✅ Green screen + high beep |
| Fail scan | ❌ Red screen + double low beep |
| End a job | Click **END JOB** → Enter supervisor PIN |
| View history | Click **History** in top menu |

---

## 🚀 Starting Your Shift

### Step 1: Check the System
1. The screen should show the **Barcode Verification System** home page
2. If the screen is off or frozen, see [Troubleshooting](#troubleshooting)
3. Make sure the barcode scanner is connected (try scanning any barcode)

### Step 2: Start a New Job

1. **Enter Job ID**: Type the work order or job number (e.g., `WO-12345`)
2. **Enter Expected Barcode**: Type or scan the barcode that SHOULD be on every label
3. **Select Pieces Per Shipper**: Choose 1, 2, 3, or Custom
4. **Set Target (Optional)**: Enter total shippers if you have a target
5. **Click START JOB**

![Job Setup Screen](job_setup_placeholder.png)

> 💡 **Tip**: You can scan the expected barcode directly into the barcode field instead of typing it!

---

## ✅ During Production

### What a PASS Looks Like
- Screen flashes **GREEN**
- You hear a **single high beep**
- Counter increases by 1
- Keep scanning!

### What a FAIL Looks Like
- Screen flashes **RED**
- You hear **two low beeps**
- An alarm may sound (if configured)
- **STOP** - check the label

### What To Do When You Get a FAIL

1. **Stop scanning** - Don't scan more until you investigate
2. **Check the label** - Is it the wrong barcode? Damaged? Misread?
3. **If wrong label**: Remove the carton, set aside for relabeling
4. **If scanner error**: Try scanning again (sometimes scanners misread)
5. **If correct label but still failing**: Call your supervisor

> ⚠️ **Never ignore a FAIL!** Every fail needs to be investigated.

---

## 🏁 Ending Your Job

### When the Job is Complete
1. Click the **END JOB** button
2. Enter the **Supervisor PIN** (get this from your supervisor)
3. The system will save your job to history

### If You Made a Mistake
- You **cannot** change past scans
- Tell your supervisor - they can add notes or adjust counts in the system

---

## 📊 Understanding the Screen

### Main Display
| Element | What It Shows |
|---------|---------------|
| **Job ID** | Current work order |
| **Expected Barcode** | What every scan should match |
| **Total Scans** | How many barcodes scanned |
| **Pass** | Number of good scans |
| **Fail** | Number of bad scans |
| **Pass Rate** | Percentage of good scans |
| **Progress Bar** | How close to target (if set) |

### Last Scan Display
Shows the most recent barcode scanned and whether it passed or failed.

---

## 🔊 Sound Guide

| Sound | Meaning | Action |
|-------|---------|--------|
| 🔔 Single high beep | PASS - Good scan | Continue |
| 🔔🔔 Two low beeps | FAIL - Wrong barcode | Stop and check |
| 🔕 No sound | System may be muted | Check volume, tell supervisor |

---

## ❓ Troubleshooting

### Screen is Frozen or Black

1. **Wait 10 seconds** - it might be loading
2. **Touch the screen** or move the mouse
3. **If still frozen**: Hold the power button for 5 seconds, then release and press again
4. **If it doesn't come back**: Call IT or your supervisor

### Scanner Won't Scan

1. **Check the USB cable** - is it plugged in firmly?
2. **Try unplugging and replugging** the scanner
3. **Test on any barcode** - does it beep when scanning?
4. **Check the scanner's light** - is it turning on when you press the trigger?
5. **If nothing works**: Use a backup scanner or call IT

### Wrong Barcode Entered

1. **If you haven't started scanning yet**: Click back and re-enter
2. **If you've already started**: You must END the current job and start a new one
3. **Failed scans from wrong setup**: Tell your supervisor

### I Keep Getting FAIL on Good Labels

1. **Check the expected barcode** - did you enter it correctly?
2. **Check the label quality** - is it printed clearly?
3. **Clean the scanner window** - smudges can cause misreads
4. **Try scanning slower** - move the scanner across the barcode
5. **If labels look good but keep failing**: Call your supervisor

### No Sound / Can't Hear Beeps

1. **Check if speakers are muted** - look for speaker icon on screen
2. **Check volume** - it might be turned down
3. **Click anywhere on the page** - browsers sometimes block sound until you click

---

## 📞 Who To Call

| Issue | Contact |
|-------|---------|
| Wrong labels on cartons | Line Supervisor |
| Scanner broken | IT Department |
| System down/frozen | IT Department |
| Forgot supervisor PIN | Line Supervisor |
| Reporting a problem | Shift Lead |

---

## ✋ Important Rules

1. **Never skip a FAIL** - always investigate
2. **Don't force-pass** bad labels - this creates shipping errors
3. **Report scanner issues immediately** - don't work with faulty equipment
4. **End your job properly** - don't just walk away
5. **If unsure, ask** - supervisors are here to help

---

## 📝 Daily Checklist

Before starting your shift:
- [ ] Screen is on and showing home page
- [ ] Scanner is connected and working
- [ ] You know today's job IDs and barcodes
- [ ] You have supervisor PIN available

At end of shift:
- [ ] Current job is ended properly
- [ ] Any issues reported to supervisor
- [ ] Scanner is in its holder

---

*If this guide doesn't answer your question, ask your supervisor or IT department.*
