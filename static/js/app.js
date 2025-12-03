/* ============================================================
   BARCODE VERIFICATION SYSTEM - CLIENT v4.1
   Now with global scanner detection (no focus required)
   ============================================================ */

class BarcodeVerificationApp {
    constructor() {
        this.activeJob = null;
        this.eventSource = null;
        this.selectedPieces = 1;
        this.flashEnabled = true;
        this.isProcessing = false;

        // Scanner detection config
        this.scanBuffer = '';
        this.lastKeyTime = 0;
        this.scanThreshold = 50;   // Max ms between keystrokes for scanner
        this.minBarcodeLength = 3; // Minimum valid barcode length

        this.initTheme();
        this.init();
        this.bindEvents();
        this.startClock();
    }

    initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
        }

        document.getElementById('theme-toggle')?.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        });
    }

    init() {
        this.checkActiveJob();
        this.connectSSE();

        const flashToggle = document.getElementById('flash-toggle');
        if (flashToggle) {
            flashToggle.checked = this.flashEnabled;
            flashToggle.addEventListener('change', (e) => {
                this.flashEnabled = e.target.checked;
            });
        }
    }

    // ========================================================
    // EVENT BINDINGS
    // ========================================================

    bindEvents() {
        // Setup screen
        document.querySelectorAll('.pieces-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectPieces(e.target));
        });

        document.getElementById('custom-pieces')?.addEventListener('input', (e) => {
            this.selectCustomPieces(e.target.value);
        });

        document.getElementById('start-job-btn')?.addEventListener('click', () => {
            this.startJob();
        });

        document.getElementById('expected-barcode')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.startJob();
        });

        document.getElementById('end-job-btn')?.addEventListener('click', () => {
            this.showEndJobModal();
        });

        // Modal buttons
        document.getElementById('cancel-end-btn')?.addEventListener('click', () => {
            this.hideModal('end-job-modal');
        });

        document.getElementById('confirm-end-btn')?.addEventListener('click', () => {
            this.endJob();
        });

        document.getElementById('supervisor-pin')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.endJob();
        });

        document.getElementById('close-summary-btn')?.addEventListener('click', () => {
            this.hideModal('summary-modal');
            this.showSetupScreen();
        });

        // Line Lock
        document.getElementById('unlock-btn')?.addEventListener('click', () => this.unlockLine());
        document.getElementById('halt-pin')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.unlockLine();
        });

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                e.target.classList.add('active');
                const tabId = e.target.dataset.tab;
                document.getElementById(`tab-${tabId}`)?.classList.add('active');

                if (tabId === 'hourly') {
                    this.fetchHourlyStats();
                }
            });
        });

        // Global barcode scanner listener (timing-based detection)
        this.initBarcodeListener();
    }

    // ========================================================
    // BARCODE SCANNER LISTENER
    // ========================================================

    initBarcodeListener() {
        document.addEventListener('keydown', (e) => this.handleScannerInput(e));

        // Debug: uncomment to see scanner buffer in console
        // setInterval(() => {
        //     if (this.scanBuffer) console.log('Buffer:', this.scanBuffer);
        // }, 100);
    }

    handleScannerInput(e) {
        // Skip if focused on an input field (let user type normally)
        const activeEl = document.activeElement;
        const isInputFocused = activeEl && (
            activeEl.tagName === 'INPUT' ||
            activeEl.tagName === 'TEXTAREA' ||
            activeEl.isContentEditable
        );

        if (isInputFocused) return;

        // Skip if no active job or system locked
        if (!this.activeJob || this.isLocked) return;

        // Skip if modal is open
        if (document.querySelector('.modal:not(.hidden)')) return;

        const now = Date.now();
        const timeDiff = now - this.lastKeyTime;

        // Reset buffer if too much time passed (indicates human typing or pause)
        if (timeDiff > 500) {
            this.scanBuffer = '';
        }

        if (e.key === 'Enter') {
            if (this.scanBuffer.length >= this.minBarcodeLength) {
                e.preventDefault();
                const barcode = this.scanBuffer;
                this.scanBuffer = '';
                console.log('[Scanner] Detected barcode:', barcode);
                this.processScan(barcode);
            }
            this.scanBuffer = '';
        } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
            // Single printable character, not a modifier combo
            // Check timing - scanner is FAST (< 50ms between chars)
            if (timeDiff > this.scanThreshold && this.scanBuffer.length > 0) {
                // Slow typing detected mid-buffer, likely human - reset
                this.scanBuffer = '';
            }
            this.scanBuffer += e.key;
        }

        this.lastKeyTime = now;
    }

    // ========================================================
    // HOURLY STATS
    // ========================================================

    async fetchHourlyStats() {
        try {
            const response = await fetch('/api/hourly_stats');
            const data = await response.json();
            this.renderHourlyTable(data);
        } catch (err) {
            console.error('Failed to fetch hourly stats:', err);
        }
    }

    renderHourlyTable(data) {
        const tbody = document.getElementById('hourly-log-body');
        if (!tbody) return;

        tbody.innerHTML = '';
        const currentHour = new Date().getHours();

        for (let h = 8; h <= 20; h++) {
            const stats = data[h] || { shippers: 0, pieces: 0 };
            const row = document.createElement('tr');

            if (h === currentHour) {
                row.classList.add('current-hour');
            }

            row.innerHTML = `
                <td>${h}:00-${h + 1}:00</td>
                <td>${stats.shippers}</td>
                <td>${stats.pieces}</td>
                <td class="mono">${stats.cumulative || 0}</td>
            `;
            tbody.appendChild(row);
        }
    }

    // ========================================================
    // CLOCK
    // ========================================================

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
            const clockEl = document.getElementById('clock');
            if (clockEl) clockEl.textContent = timeStr;
        };

        updateClock();
        setInterval(updateClock, 1000);
        setInterval(() => this.updateElapsedTime(), 1000);
    }

    updateElapsedTime() {
        if (!this.activeJob || !this.activeJob.start_time_iso) return;

        const startTime = new Date(this.activeJob.start_time_iso);
        const now = new Date();
        const diff = Math.floor((now - startTime) / 1000);

        if (diff < 0) return;

        const hours = Math.floor(diff / 3600);
        const minutes = Math.floor((diff % 3600) / 60);
        const pad = (n) => n.toString().padStart(2, '0');

        const elapsed = document.getElementById('job-elapsed');
        if (elapsed) elapsed.textContent = `${pad(hours)}:${pad(minutes)}`;
    }

    // ========================================================
    // SSE
    // ========================================================

    connectSSE(retryDelay = 1000) {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource('/api/events');
        this.sseRetryDelay = retryDelay;

        this.eventSource.addEventListener('scan', (e) => {
            const data = JSON.parse(e.data);
            this.handleScanUpdate(data);

            if (document.querySelector('.tab-btn[data-tab="hourly"].active')) {
                this.fetchHourlyStats();
            }
        });

        this.eventSource.addEventListener('job_started', (e) => {
            const data = JSON.parse(e.data);
            this.updateActiveJobDisplay(data);
            this.resetScanDisplay();
        });

        this.eventSource.addEventListener('job_ended', (e) => {
            this.activeJob = null;
            this.updateActiveJobDisplay(null);
            this.showJobCompleteModal();
        });

        this.eventSource.addEventListener('shift_update', (e) => {
            const data = JSON.parse(e.data);
            this.updateShiftDisplay(data.shift);
        });

        this.eventSource.onerror = () => {
            console.log('[SSE] Connection error, reconnecting in', this.sseRetryDelay, 'ms...');
            this.eventSource.close();
            const nextDelay = Math.min(this.sseRetryDelay * 2, 30000);
            setTimeout(() => this.connectSSE(nextDelay), this.sseRetryDelay);
        };

        this.eventSource.onopen = () => {
            console.log('[SSE] Connected');
            this.sseRetryDelay = 1000;
        };
    }

    // ========================================================
    // API
    // ========================================================

    async checkActiveJob() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.active_job) {
                this.activeJob = data.active_job;
                this.showScanningScreen();
                this.updateJobDisplay(data.active_job);

                // CHECK LOCK STATE
                if (data.active_job.is_locked) {
                    this.triggerLineLock();
                }
            } else {
                this.showSetupScreen();
            }

            this.updateShiftDisplay(data.shift);
        } catch (err) {
            console.error('Failed to check status:', err);
        }
    }

    async startJob() {
        const expectedBarcode = document.getElementById('expected-barcode')?.value.trim();
        const jobId = document.getElementById('job-id')?.value.trim();
        const targetQty = parseInt(document.getElementById('target-quantity')?.value) || 0;

        // CLIENT-SIDE VALIDATION
        if (!expectedBarcode) {
            alert('Please enter an expected barcode');
            document.getElementById('expected-barcode')?.focus();
            return;
        }

        if (expectedBarcode.length > 200) {
            alert('Barcode is too long (max 200 characters)');
            return;
        }

        const dangerousPattern = /[<>"'&;\\]/;
        if (dangerousPattern.test(expectedBarcode)) {
            alert('Barcode contains invalid characters');
            return;
        }

        if (jobId && jobId.length > 100) {
            alert('Job ID is too long (max 100 characters)');
            return;
        }

        if (jobId && dangerousPattern.test(jobId)) {
            alert('Job ID contains invalid characters');
            return;
        }

        let pieces = this.selectedPieces;
        const customPieces = parseInt(document.getElementById('custom-pieces')?.value);
        if (customPieces > 0) {
            pieces = customPieces;
        }

        if (pieces < 1 || pieces > 10000) {
            alert('Pieces per shipper must be between 1 and 10,000');
            return;
        }

        if (targetQty < 0 || targetQty > 1000000) {
            alert('Target quantity must be between 0 and 1,000,000');
            return;
        }

        try {
            const response = await fetch('/api/job/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: jobId || null,
                    expected_barcode: expectedBarcode,
                    pieces_per_shipper: pieces,
                    target_quantity: targetQty
                })
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                return;
            }

            this.activeJob = data.job;
            this.showScanningScreen();
            this.updateJobDisplay(data.job);
        } catch (err) {
            console.error('Failed to start job:', err);
            alert('Failed to start job');
        }
    }

    async processScan(barcode) {
        if (this.isLocked || this.isProcessing) return;

        barcode = barcode.trim();
        if (!barcode || !this.activeJob) return;

        this.isProcessing = true;

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });

            const data = await response.json();

            // Handle Locked State
            if (response.status === 423) {
                this.triggerLineLock();
                return;
            }

            if (data.error) {
                console.error('Scan error:', data.error);
                return;
            }

            this.handleScanUpdate(data);

        } catch (err) {
            console.error('Failed to process scan:', err);
        } finally {
            this.isProcessing = false;
        }
    }

    async endJob() {
        const pin = document.getElementById('supervisor-pin')?.value;

        try {
            const response = await fetch('/api/job/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });

            const data = await response.json();

            if (response.status === 429) {
                alert(data.error);
                this.hideModal('end-job-modal');
                return;
            }

            if (data.error) {
                document.getElementById('pin-error')?.classList.remove('hidden');
                document.getElementById('supervisor-pin').value = '';
                return;
            }

            this.hideModal('end-job-modal');
            // Job end will be handled by SSE event 'job_ended'

        } catch (err) {
            console.error('Failed to end job:', err);
            alert('Failed to end job');
        }
    }

    // ========================================================
    // UI UPDATES
    // ========================================================

    handleScanUpdate(data) {
        const scan = data.scan;
        const job = data.job;

        this.playSound(scan.status);

        // Flash
        if (this.flashEnabled) {
            const overlay = document.getElementById('flash-overlay');
            if (overlay) {
                overlay.className = '';
                void overlay.offsetWidth;
                overlay.classList.add(scan.status === 'PASS' ? 'flash-pass' : 'flash-fail');
            }
        }

        // Result display
        const resultDisplay = document.getElementById('result-display');
        const resultText = document.getElementById('result-text');
        const resultBarcode = document.getElementById('result-barcode');

        resultDisplay.classList.remove('pass', 'fail');
        resultDisplay.classList.add(scan.status.toLowerCase());

        resultText.textContent = scan.status === 'PASS' ? '✓ PASS' : '✗ FAIL';
        resultBarcode.textContent = scan.status === 'PASS' ? scan.barcode : `Got: ${scan.barcode}`;

        this.updateJobDisplay(job);
        this.updateHistory(data.recent_scans);

        // Trigger Lock on Fail
        if (scan.status === 'FAIL') {
            this.triggerLineLock();
        }
    }

    updateJobDisplay(job) {
        if (!job) return;
        this.activeJob = job;

        const setEl = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        setEl('current-job-id', job.job_id);
        setEl('job-start-time', job.start_time);
        setEl('expected-display', job.expected_barcode);
        setEl('pieces-display', job.pieces_per_shipper);

        // Stats
        setEl('stat-total', job.total_scans);
        setEl('stat-pieces', job.total_pieces);
        setEl('stat-pass', job.pass_count);
        setEl('stat-fail', job.fail_count);
        setEl('stat-rate', `${Math.round(job.pass_rate)}%`);

        // Hourly
        setEl('this-hour-shippers', job.scans_this_hour);
        setEl('this-hour-pieces', job.pieces_this_hour);
        setEl('prev-hour-shippers', job.scans_prev_hour);
        setEl('prev-hour-pieces', job.pieces_prev_hour);
        setEl('job-elapsed', job.elapsed);

        // Progress
        if (job.target_quantity > 0) {
            document.getElementById('progress-section')?.classList.remove('hidden');
            setEl('progress-text', `${job.pass_count} / ${job.target_quantity}`);

            const pct = Math.min((job.pass_count / job.target_quantity) * 100, 100);
            const bar = document.getElementById('progress-bar');
            if (bar) {
                bar.style.width = `${pct}%`;
                bar.classList.toggle('complete', job.pass_count >= job.target_quantity);
            }
        }
    }

    updateHistory(scans) {
        const list = document.getElementById('history-list');
        if (!list || !scans) return;

        list.innerHTML = scans.map(scan => `
            <div class="history-item ${scan.status.toLowerCase()}">
                <span class="history-icon">${scan.status === 'PASS' ? '✓' : '✗'}</span>
                <span class="history-barcode">${scan.barcode}</span>
                <span class="history-time">${scan.timestamp}</span>
            </div>
        `).join('');
    }

    updateShiftDisplay(shift) {
        const setEl = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };
        setEl('shift-shippers', shift.total_shippers);
        setEl('shift-pieces', shift.total_pieces);
        setEl('shift-jobs', shift.jobs_completed);
    }

    showJobSummary(summary) {
        const grid = document.getElementById('summary-stats');
        grid.innerHTML = `
            <div class="summary-item full">
                <span class="label">Job ID</span>
                <span class="value">${summary.job_id}</span>
            </div>
            <div class="summary-item">
                <span class="label">Shippers</span>
                <span class="value">${summary.total_scans}</span>
            </div>
            <div class="summary-item">
                <span class="label">Pieces</span>
                <span class="value">${summary.total_pieces}</span>
            </div>
            <div class="summary-item">
                <span class="label">Passed</span>
                <span class="value" style="color:var(--success)">${summary.pass_count}</span>
            </div>
            <div class="summary-item">
                <span class="label">Failed</span>
                <span class="value" style="color:var(--danger)">${summary.fail_count}</span>
            </div>
            <div class="summary-item">
                <span class="label">Pass Rate</span>
                <span class="value">${summary.pass_rate}%</span>
            </div>
            <div class="summary-item">
                <span class="label">Duration</span>
                <span class="value">${summary.elapsed}</span>
            </div>
        `;
        this.showModal('summary-modal');
    }

    // ========================================================
    // SCREEN MANAGEMENT
    // ========================================================

    showSetupScreen() {
        document.getElementById('setup-screen')?.classList.remove('hidden');
        document.getElementById('scanning-screen')?.classList.add('hidden');
        document.getElementById('expected-barcode')?.focus();
    }

    showScanningScreen() {
        document.getElementById('setup-screen')?.classList.add('hidden');
        document.getElementById('scanning-screen')?.classList.remove('hidden');

        const resultDisplay = document.getElementById('result-display');
        resultDisplay?.classList.remove('pass', 'fail');

        const resultText = document.getElementById('result-text');
        const resultBarcode = document.getElementById('result-barcode');
        if (resultText) resultText.textContent = 'READY';
        if (resultBarcode) resultBarcode.textContent = 'Scan barcode to begin';
    }

    // ========================================================
    // MODALS
    // ========================================================

    showModal(id) {
        document.getElementById(id)?.classList.remove('hidden');
    }

    hideModal(id) {
        document.getElementById(id)?.classList.add('hidden');
        document.getElementById('supervisor-pin').value = '';
        document.getElementById('pin-error')?.classList.add('hidden');
    }

    showEndJobModal() {
        this.showModal('end-job-modal');
        document.getElementById('supervisor-pin')?.focus();
    }

    // ========================================================
    // PIECES SELECTION
    // ========================================================

    selectPieces(btn) {
        if (!btn) return;
        document.querySelectorAll('.pieces-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        this.selectedPieces = parseInt(btn.dataset.pieces);
        document.getElementById('custom-pieces').value = '';
    }

    selectCustomPieces(value) {
        const num = parseInt(value);
        if (num > 0) {
            document.querySelectorAll('.pieces-btn').forEach(b => b.classList.remove('selected'));
            this.selectedPieces = num;
        }
    }

    // ========================================================
    // AUDIO
    // ========================================================

    playSound(status) {
        try {
            if (status === 'PASS') {
                this.beep(800, 100);
            } else {
                this.beep(300, 300);
                setTimeout(() => this.beep(300, 300), 350);
            }
        } catch (err) { }
    }

    beep(frequency, duration) {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.connect(gain);
            gain.connect(ctx.destination);

            osc.frequency.value = frequency;
            osc.type = 'sine';

            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration / 1000);

            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + duration / 1000);
        } catch (err) { }
    }

    // ========================================================
    // LINE LOCK & ALARM
    // ========================================================

    triggerLineLock() {
        this.isLocked = true;
        this.showModal('line-halted-modal');
        document.getElementById('halt-pin').focus();
        this.startAlarm();
    }

    async unlockLine() {
        const pin = document.getElementById('halt-pin').value;
        try {
            const response = await fetch('/api/verify_pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });
            const data = await response.json();

            if (data.success) {
                this.isLocked = false;
                this.stopAlarm();
                this.hideModal('line-halted-modal');
                document.getElementById('halt-pin').value = '';
                document.getElementById('halt-error').classList.add('hidden');
            } else {
                document.getElementById('halt-error').classList.remove('hidden');
                document.getElementById('halt-pin').value = '';
            }
        } catch (err) {
            console.error('Unlock failed:', err);
        }
    }

    startAlarm() {
        if (this.alarmInterval) return;
        const play = () => {
            this.beep(800, 300);
            setTimeout(() => this.beep(600, 300), 300);
        };
        play();
        this.alarmInterval = setInterval(play, 700);
    }

    stopAlarm() {
        if (this.alarmInterval) {
            clearInterval(this.alarmInterval);
            this.alarmInterval = null;
        }
    }
}

// Restore function
function uploadRestore(input) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/restore', {
        method: 'POST',
        body: formData
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Restore failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => alert('Restore failed: ' + err));

    input.value = '';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BarcodeVerificationApp();
});