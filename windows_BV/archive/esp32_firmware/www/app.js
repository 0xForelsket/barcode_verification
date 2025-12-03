/* ============================================================
   BARCODE VERIFICATION SYSTEM - CLIENT APPLICATION
   ============================================================ */

class BarcodeVerificationApp {
    constructor() {
        // State
        this.activeJob = null;
        this.eventSource = null;
        this.selectedPieces = 3; // Default
        this.flashEnabled = true; // Default flash on

        this.init();

        // Audio
        this.soundPass = document.getElementById('sound-pass');
        this.soundFail = document.getElementById('sound-fail');
        // Initialize
        this.bindEvents();
        this.startClock();
        // this.connectSSE(); // Moved to init()
        // this.checkActiveJob(); // Moved to init()

        // Focus scan input if on scanning screen
        this.focusScanInput();
    }

    init() {
        // Initialize UI
        this.checkActiveJob();
        this.connectSSE();

        // Initialize Flash Toggle
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

        // Scanning screen
        document.getElementById('result-display')?.addEventListener('click', () => {
            this.focusScanInput();
        });

        document.getElementById('scan-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.processScan(e.target.value);
                e.target.value = '';
            }
        });

        document.getElementById('end-job-btn')?.addEventListener('click', () => {
            this.showEndJobModal();
        });

        // End job modal
        document.getElementById('cancel-end-btn')?.addEventListener('click', () => {
            this.hideModal('end-job-modal');
        });

        document.getElementById('confirm-end-btn')?.addEventListener('click', () => {
            this.endJob();
        });

        document.getElementById('supervisor-pin')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.endJob();
        });

        // Summary modal
        document.getElementById('close-summary-btn')?.addEventListener('click', () => {
            this.hideModal('summary-modal');
            this.showSetupScreen();
        });

        // Global click to focus scan input
        document.addEventListener('click', (e) => {
            if (this.activeJob && !e.target.closest('.modal') && !e.target.closest('button') && !e.target.closest('input')) {
                this.focusScanInput();
            }
        });

        // Tab Switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                // Remove active class from all
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                // Add active to clicked
                e.target.classList.add('active');
                const tabId = e.target.dataset.tab;
                document.getElementById(`tab-${tabId}`).classList.add('active');

                // Fetch data if hourly tab
                if (tabId === 'hourly') {
                    this.fetchHourlyStats();
                }
            });
        });
    }

    // ========================================================
    // CLOCK
    // ========================================================

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
            const clockEl = document.getElementById('clock');
            if (clockEl) clockEl.textContent = timeStr;
        };

        updateClock();
        setInterval(updateClock, 1000);

        // Also update elapsed time every second
        setInterval(() => this.updateElapsedTime(), 1000);
    }

    updateElapsedTime() {
        if (!this.activeJob) return;

        // Recalculate elapsed from start time
        const elapsed = document.getElementById('job-elapsed');
        if (!elapsed) return;

        // We'll rely on server updates for accurate elapsed time
        // This is just to keep the display ticking between updates
    }

    // ========================================================
    // SERVER-SENT EVENTS (Real-time updates)
    // ========================================================

    connectSSE() {
        this.eventSource = new EventSource('/api/events');

        this.eventSource.addEventListener('scan', (e) => {
            const data = JSON.parse(e.data);
            this.handleScanUpdate(data);

            // Refresh hourly stats if tab is active
            if (document.querySelector('.tab-btn[data-tab="hourly"].active')) {
                this.fetchHourlyStats();
            }
        });

        this.eventSource.addEventListener('job_started', (e) => {
            const data = JSON.parse(e.data);
            this.activeJob = data;
            this.showScanningScreen();
            this.updateJobDisplay(data);
        });

        this.eventSource.addEventListener('job_ended', (e) => {
            const data = JSON.parse(e.data);
            this.updateShiftDisplay(data.shift);
            // Only show summary if we're the one who ended it
            // Other viewers will just see the setup screen
        });

        this.eventSource.onerror = () => {
            console.log('[SSE] Connection lost, reconnecting...');
            setTimeout(() => this.connectSSE(), 3000);
        };
    }

    // ========================================================
    // API CALLS
    // ========================================================

    async checkActiveJob() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.active_job) {
                this.activeJob = data.active_job;
                this.showScanningScreen();
                this.updateJobDisplay(data.active_job);
            }

            this.updateShiftDisplay(data.shift);
        } catch (err) {
            console.error('Failed to check status:', err);
        }
    }

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

        // Loop 8 to 20
        for (let h = 8; h <= 20; h++) {
            const stats = data[h] || { shippers: 0, pieces: 0 };
            const hourDisplay = `${h}:00 - ${h + 1}:00`;
            const row = document.createElement('tr');

            // Highlight current hour
            const currentHour = new Date().getHours();
            if (h === currentHour) {
                row.style.color = 'var(--primary)';
                row.style.fontWeight = 'bold';
            }

            row.innerHTML = `
                <td>${hourDisplay}</td>
                <td>${stats.shippers}</td>
                <td>${stats.pieces}</td>
            `;
            tbody.appendChild(row);
        }
    }

    async startJob() {
        const expectedBarcode = document.getElementById('expected-barcode')?.value.trim();
        if (!expectedBarcode) {
            alert('Please enter the expected barcode');
            return;
        }

        const jobId = document.getElementById('job-id')?.value.trim();
        const targetQty = parseInt(document.getElementById('target-quantity')?.value) || 0;

        // Get pieces
        let pieces = this.selectedPieces;
        const customPieces = parseInt(document.getElementById('custom-pieces')?.value);
        if (customPieces > 0) pieces = customPieces;

        try {
            const response = await fetch('/api/job/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: jobId,
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

            // Clear form
            document.getElementById('job-id').value = '';
            document.getElementById('expected-barcode').value = '';
            document.getElementById('target-quantity').value = '';
            document.getElementById('custom-pieces').value = '';
            this.selectPieces(document.querySelector('.pieces-btn[data-pieces="3"]'));

        } catch (err) {
            console.error('Failed to start job:', err);
            alert('Failed to start job. Please try again.');
        }
    }

    async processScan(barcode) {
        barcode = barcode.trim();
        if (!barcode || !this.activeJob) return;

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });

            const data = await response.json();

            if (data.error) {
                console.error('Scan error:', data.error);
                return;
            }

            // Update is handled by SSE, but we also handle locally for responsiveness
            this.handleScanUpdate(data);

        } catch (err) {
            console.error('Failed to process scan:', err);
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

            if (data.error) {
                document.getElementById('pin-error')?.classList.remove('hidden');
                document.getElementById('supervisor-pin').value = '';
                return;
            }

            this.hideModal('end-job-modal');
            this.activeJob = null;

            // Show summary
            this.showJobSummary(data.summary);

        } catch (err) {
            console.error('Failed to end job:', err);
            alert('Failed to end job. Please try again.');
        }
    }

    // ========================================================
    // UI UPDATES
    // ========================================================

    handleScanUpdate(data) {
        const scan = data.scan;
        const job = data.job;

        // Play sound
        this.playSound(scan.status);

        // Trigger Flash
        if (this.flashEnabled) {
            const overlay = document.getElementById('flash-overlay');
            if (overlay) {
                overlay.className = ''; // Reset
                void overlay.offsetWidth; // Trigger reflow
                overlay.classList.add(scan.status === 'PASS' ? 'flash-pass' : 'flash-fail');
            }
        }

        // Update result display
        const resultDisplay = document.getElementById('result-display');
        const resultText = document.getElementById('result-text');
        const resultBarcode = document.getElementById('result-barcode');

        resultDisplay.classList.remove('pass', 'fail');
        resultDisplay.classList.add(scan.status.toLowerCase());

        resultText.textContent = scan.status === 'PASS' ? '✓ PASS' : '✗ FAIL';
        resultBarcode.textContent = scan.status === 'PASS' ? scan.barcode : `Got: ${scan.barcode}`;

        // Update job stats
        this.updateJobDisplay(job);

        // Update history
        this.updateHistory(data.recent_scans);

        // Refocus input
        this.focusScanInput();
    }

    updateJobDisplay(job) {
        if (!job) return;

        this.activeJob = job;

        // Header info
        document.getElementById('current-job-id').textContent = job.job_id;
        document.getElementById('job-start-time').textContent = job.start_time;
        document.getElementById('expected-display').textContent = job.expected_barcode;
        document.getElementById('pieces-display').textContent = job.pieces_per_shipper;

        // Stats
        document.getElementById('stat-total').textContent = job.total_scans;
        document.getElementById('stat-pieces').textContent = job.total_pieces;
        document.getElementById('stat-pass').textContent = job.pass_count;
        document.getElementById('stat-fail').textContent = job.fail_count;
        document.getElementById('stat-rate').textContent = `${job.pass_rate}%`;

        // Color code pass rate
        const rateEl = document.getElementById('stat-rate');
        rateEl.classList.remove('highlight-success', 'highlight-warning', 'highlight-danger');
        if (job.pass_rate >= 99) {
            rateEl.classList.add('highlight-success');
        } else if (job.pass_rate >= 95) {
            rateEl.classList.add('highlight-warning');
        } else {
            rateEl.classList.add('highlight-danger');
        }

        // Hourly board
        document.getElementById('this-hour-shippers').textContent = job.scans_this_hour;
        document.getElementById('this-hour-pieces').textContent = job.pieces_this_hour;
        document.getElementById('prev-hour-shippers').textContent = job.scans_prev_hour;
        document.getElementById('prev-hour-pieces').textContent = job.pieces_prev_hour;

        document.getElementById('job-elapsed').textContent = job.elapsed;

        // Progress bar
        if (job.target_quantity > 0) {
            document.getElementById('progress-section')?.classList.remove('hidden');
            document.getElementById('progress-text').textContent = `${job.pass_count} / ${job.target_quantity} shippers`;

            const pct = Math.min((job.pass_count / job.target_quantity) * 100, 100);
            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = `${pct}%`;

            if (job.pass_count >= job.target_quantity) {
                progressBar.classList.add('complete');
            } else {
                progressBar.classList.remove('complete');
            }
        }
    }

    updateHistory(scans) {
        const historyList = document.getElementById('history-list');
        if (!historyList || !scans) return;

        historyList.innerHTML = scans.map(scan => `
            <div class="history-item ${scan.status.toLowerCase()}">
                <span class="history-icon">${scan.status === 'PASS' ? '✓' : '✗'}</span>
                <span class="history-barcode">${scan.barcode}</span>
                <span class="history-time">${scan.timestamp}</span>
            </div>
        `).join('');
    }

    updateShiftDisplay(shift) {
        document.getElementById('shift-shippers').textContent = shift.total_shippers;
        document.getElementById('shift-pieces').textContent = shift.total_pieces;
        document.getElementById('shift-jobs').textContent = shift.jobs_completed;
    }

    showJobSummary(summary) {
        const statsEl = document.getElementById('summary-stats');
        statsEl.innerHTML = `
            <p><span class="label">Job ID:</span> <span>${summary.job_id}</span></p>
            <p><span class="label">Master Shippers:</span> <span>${summary.total_scans}</span></p>
            <p><span class="label">Total Pieces:</span> <span>${summary.total_pieces}</span></p>
            <p><span class="label">Passed:</span> <span style="color: var(--success)">${summary.pass_count}</span></p>
            <p><span class="label">Failed:</span> <span style="color: var(--danger)">${summary.fail_count}</span></p>
            <p><span class="label">Pass Rate:</span> <span>${summary.pass_rate}%</span></p>
            <p><span class="label">Duration:</span> <span>${summary.elapsed}</span></p>
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

        // Reset result display
        const resultDisplay = document.getElementById('result-display');
        resultDisplay.classList.remove('pass', 'fail');
        document.getElementById('result-text').textContent = 'READY TO SCAN';
        document.getElementById('result-barcode').textContent = 'Click here or scan barcode';

        this.focusScanInput();
    }

    focusScanInput() {
        const scanInput = document.getElementById('scan-input');
        if (scanInput && this.activeJob) {
            scanInput.focus();
        }
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
    // AUDIO FEEDBACK
    // ========================================================

    playSound(status) {
        try {
            if (status === 'PASS') {
                this.playBeep(800, 100);  // High beep for pass
            } else {
                this.playBeep(300, 300);  // Low beep for fail
                setTimeout(() => this.playBeep(300, 300), 350);  // Double beep for fail
            }
        } catch (err) {
            console.log('Audio not available');
        }
    }

    playBeep(frequency, duration) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = frequency;
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration / 1000);
        } catch (err) {
            // Audio not supported
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BarcodeVerificationApp();
});
