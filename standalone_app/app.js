/**
 * Barcode Verification System - Standalone Version
 * Runs entirely in the browser using localStorage.
 */

class BarcodeApp {
    constructor() {
        // State
        this.state = {
            activeJob: null,
            shiftStats: {
                date: new Date().toDateString(),
                total_shippers: 0,
                total_pieces: 0,
                jobs_completed: 0
            },
            flashEnabled: true,
            selectedPieces: 3
        };

        // Audio Context
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();

        this.init();
    }

    init() {
        this.loadState();
        this.bindEvents();
        this.startClock();
        this.render();

        // Check for shift reset
        const today = new Date().toDateString();
        if (this.state.shiftStats.date !== today) {
            this.state.shiftStats = {
                date: today,
                total_shippers: 0,
                total_pieces: 0,
                jobs_completed: 0
            };
            this.saveState();
        }
    }

    loadState() {
        const saved = localStorage.getItem('barcode_app_state');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                // Merge saved state with default structure to handle updates
                this.state = { ...this.state, ...parsed };

                // Restore Date objects if needed (JSON stores strings)
                if (this.state.activeJob) {
                    this.state.activeJob.start_time = new Date(this.state.activeJob.start_time);
                }
            } catch (e) {
                console.error("Failed to load state", e);
            }
        }
    }

    saveState() {
        localStorage.setItem('barcode_app_state', JSON.stringify(this.state));
        this.render();
    }

    bindEvents() {
        // Buttons
        document.getElementById('start-job-btn')?.addEventListener('click', () => this.startJob());
        document.getElementById('end-job-btn')?.addEventListener('click', () => this.showEndModal());
        document.getElementById('confirm-end-job')?.addEventListener('click', () => this.endJob());
        document.getElementById('cancel-end-job')?.addEventListener('click', () => this.hideEndModal());
        document.getElementById('export-btn')?.addEventListener('click', () => this.exportCSV());
        document.getElementById('backup-btn')?.addEventListener('click', () => this.backupData());

        const restoreInput = document.getElementById('restore-input');
        document.getElementById('restore-btn')?.addEventListener('click', () => restoreInput?.click());
        restoreInput?.addEventListener('change', (e) => this.restoreData(e.target.files[0]));

        // Pieces Selection
        document.querySelectorAll('.pieces-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.pieces-btn').forEach(b => b.classList.remove('selected'));
                e.target.classList.add('selected');
                this.state.selectedPieces = parseInt(e.target.dataset.pieces);
                document.getElementById('custom-pieces').value = '';
            });
        });

        document.getElementById('custom-pieces')?.addEventListener('input', (e) => {
            if (e.target.value) {
                document.querySelectorAll('.pieces-btn').forEach(b => b.classList.remove('selected'));
                this.state.selectedPieces = parseInt(e.target.value);
            }
        });

        // Flash Toggle
        const flashToggle = document.getElementById('flash-toggle');
        if (flashToggle) {
            flashToggle.checked = this.state.flashEnabled;
            flashToggle.addEventListener('change', (e) => {
                this.state.flashEnabled = e.target.checked;
                this.saveState();
            });
        }

        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                e.target.classList.add('active');
                const tabId = e.target.dataset.tab;
                document.getElementById(`tab-${tabId}`).classList.add('active');
            });
        });

        // Keyboard Input (Scanner)
        document.addEventListener('keydown', (e) => {
            const input = document.getElementById('scan-input');
            if (!input) return;

            // Always keep focus on input if job is active
            if (this.state.activeJob && document.activeElement !== input &&
                document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'BUTTON') {
                input.focus();
            }

            if (e.key === 'Enter' && this.state.activeJob) {
                if (document.activeElement === input) {
                    this.handleScan(input.value);
                    input.value = '';
                }
            }
        });

        // Focus input on click anywhere in scanning screen
        document.getElementById('scanning-screen')?.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                document.getElementById('scan-input')?.focus();
            }
        });
    }

    startJob() {
        const jobId = document.getElementById('job-id').value.trim() || `JOB-${Math.floor(Date.now() / 1000)}`;
        const expected = document.getElementById('expected-barcode').value.trim();
        const target = parseInt(document.getElementById('target-quantity').value) || 0;

        if (!expected) {
            alert("Please enter an Expected Barcode");
            return;
        }

        this.state.activeJob = {
            job_id: jobId,
            expected_barcode: expected,
            pieces_per_shipper: this.state.selectedPieces,
            target_quantity: target,
            start_time: new Date(),
            pass_count: 0,
            fail_count: 0,
            total_scans: 0,
            total_pieces: 0,
            recent_scans: [], // Array of {barcode, status, timestamp}
            hourly_log: {} // { "14": {shippers: 10, pieces: 30} }
        };

        this.saveState();

        // Reset UI inputs
        document.getElementById('job-id').value = '';
        document.getElementById('expected-barcode').value = '';
        document.getElementById('target-quantity').value = '';
    }

    endJob() {
        if (!this.state.activeJob) return;

        // Update shift stats
        this.state.shiftStats.total_shippers += this.state.activeJob.total_scans;
        this.state.shiftStats.total_pieces += this.state.activeJob.total_pieces;
        this.state.shiftStats.jobs_completed += 1;

        this.state.activeJob = null;
        this.saveState();
        this.hideEndModal();

        // Reset pieces selection to 3 (default)
        this.state.selectedPieces = 3;
        document.querySelectorAll('.pieces-btn').forEach(b => b.classList.remove('selected'));
        document.querySelector('.pieces-btn[data-pieces="3"]')?.classList.add('selected');
        const customInput = document.getElementById('custom-pieces');
        if (customInput) customInput.value = '';
    }

    handleScan(barcode) {
        if (!barcode) return;

        // Resume Audio Context if needed (browser policy)
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        const job = this.state.activeJob;
        const status = barcode === job.expected_barcode ? 'PASS' : 'FAIL';
        const now = new Date();
        const hour = now.getHours();

        // Update Job Stats
        job.total_scans++;
        if (status === 'PASS') {
            job.pass_count++;
            job.total_pieces += job.pieces_per_shipper;

            // Hourly Stats
            if (!job.hourly_log[hour]) job.hourly_log[hour] = { shippers: 0, pieces: 0 };
            job.hourly_log[hour].shippers++;
            job.hourly_log[hour].pieces += job.pieces_per_shipper;

            this.beep(600, 100, 'triangle'); // High pitch for pass
            this.flash('pass');
        } else {
            job.fail_count++;
            this.beep(150, 500, 'sawtooth'); // Low pitch for fail
            this.flash('fail');
        }

        // Add to history
        job.recent_scans.unshift({
            barcode: barcode,
            status: status,
            timestamp: now.toISOString()
        });
        if (job.recent_scans.length > 50) job.recent_scans.pop();

        this.saveState();
    }

    // --- UI Rendering ---

    render() {
        const job = this.state.activeJob;
        const shift = this.state.shiftStats;

        // Screens
        const setupScreen = document.getElementById('setup-screen');
        const scanningScreen = document.getElementById('scanning-screen');

        if (job) {
            setupScreen.classList.add('hidden');
            scanningScreen.classList.remove('hidden');
            this.updateScanningUI(job);
        } else {
            setupScreen.classList.remove('hidden');
            scanningScreen.classList.add('hidden');
        }

        // Shift Stats
        document.getElementById('shift-shippers').textContent = shift.total_shippers;
        document.getElementById('shift-pieces').textContent = shift.total_pieces;
        document.getElementById('shift-jobs').textContent = shift.jobs_completed;
    }

    updateScanningUI(job) {
        // Header Info
        document.getElementById('current-job-id').textContent = job.job_id;
        const startTime = new Date(job.start_time);
        document.getElementById('job-start-time').textContent =
            `${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}`;
        document.getElementById('expected-display').textContent = job.expected_barcode;
        document.getElementById('pieces-display').textContent = job.pieces_per_shipper;

        // Main Stats
        document.getElementById('stat-total').textContent = job.total_scans;
        document.getElementById('stat-pieces').textContent = job.total_pieces;
        document.getElementById('stat-pass').textContent = job.pass_count;
        document.getElementById('stat-fail').textContent = job.fail_count;

        const rate = job.total_scans > 0 ? ((job.pass_count / job.total_scans) * 100).toFixed(1) : 100;
        const rateEl = document.getElementById('stat-rate');
        rateEl.textContent = `${rate}%`;
        rateEl.className = 'stat-value'; // Reset
        if (rate >= 99) rateEl.classList.add('highlight-success');
        else if (rate >= 95) rateEl.classList.add('highlight-warning');
        else rateEl.classList.add('highlight-danger');

        // Progress Bar
        const progressSection = document.getElementById('progress-section');
        if (job.target_quantity > 0) {
            progressSection.classList.remove('hidden');
            document.getElementById('progress-text').textContent = `${job.pass_count} / ${job.target_quantity} shippers`;
            const pct = Math.min((job.pass_count / job.target_quantity) * 100, 100);
            document.getElementById('progress-bar').style.width = `${pct}%`;
        } else {
            progressSection.classList.add('hidden');
        }

        // Hourly Board
        const currentHour = new Date().getHours();
        const prevHour = currentHour - 1;

        const thisHourStats = job.hourly_log[currentHour] || { shippers: 0, pieces: 0 };
        const prevHourStats = job.hourly_log[prevHour] || { shippers: 0, pieces: 0 };

        document.getElementById('this-hour-shippers').textContent = thisHourStats.shippers;
        document.getElementById('this-hour-pieces').textContent = thisHourStats.pieces;
        document.getElementById('prev-hour-shippers').textContent = prevHourStats.shippers;
        document.getElementById('prev-hour-pieces').textContent = prevHourStats.pieces;

        // Elapsed Time
        const elapsedSec = Math.floor((new Date() - new Date(job.start_time)) / 1000);
        const hours = Math.floor(elapsedSec / 3600);
        const mins = Math.floor((elapsedSec % 3600) / 60);
        document.getElementById('job-elapsed').textContent = `${hours}:${mins.toString().padStart(2, '0')}`;

        // Recent Scans List
        const list = document.getElementById('history-list');
        list.innerHTML = job.recent_scans.slice(0, 8).map(scan => `
            <div class="history-item ${scan.status === 'PASS' ? 'pass' : 'fail'}">
                <span class="history-icon">${scan.status === 'PASS' ? '✓' : '✗'}</span>
                <span class="history-barcode">${scan.barcode}</span>
                <span class="history-time">${new Date(scan.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            </div>
        `).join('');

        // Hourly Log Table
        const tbody = document.getElementById('hourly-log-body');
        let tableHtml = '';
        for (let h = 8; h <= 20; h++) {
            const stats = job.hourly_log[h] || { shippers: 0, pieces: 0 };
            const isCurrent = h === currentHour ? 'style="background-color: var(--bg-card-light); font-weight: bold;"' : '';
            tableHtml += `
                <tr ${isCurrent}>
                    <td>${h}:00</td>
                    <td>${stats.shippers}</td>
                    <td>${stats.pieces}</td>
                </tr>
            `;
        }
        tbody.innerHTML = tableHtml;

        // Result Display
        if (job.recent_scans.length > 0) {
            const last = job.recent_scans[0];
            const resultText = document.getElementById('result-text');
            const resultBarcode = document.getElementById('result-barcode');
            const resultDisplay = document.getElementById('result-display');

            resultText.textContent = last.status;
            resultBarcode.textContent = last.barcode;

            resultDisplay.className = 'result-display ' + (last.status === 'PASS' ? 'result-pass' : 'result-fail');
        }
    }

    // --- Utilities ---

    exportCSV() {
        const job = this.state.activeJob;
        if (!job && this.state.shiftStats.total_shippers === 0) {
            alert("No data to export.");
            return;
        }

        const now = new Date();
        const dateStr = now.toISOString().split('T')[0];
        const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
        const filename = `barcode_report_${dateStr}_${timeStr}.csv`;

        let csvContent = "data:text/csv;charset=utf-8,";

        // Header
        csvContent += "Report Date," + now.toLocaleString() + "\n";
        csvContent += "Shift Shippers," + this.state.shiftStats.total_shippers + "\n";
        csvContent += "Shift Pieces," + this.state.shiftStats.total_pieces + "\n\n";

        // Active Job Details
        if (job) {
            csvContent += "ACTIVE JOB DETAILS\n";
            csvContent += "Job ID," + job.job_id + "\n";
            csvContent += "Expected Barcode," + job.expected_barcode + "\n";
            csvContent += "Start Time," + new Date(job.start_time).toLocaleString() + "\n";
            csvContent += "Total Scans," + job.total_scans + "\n";
            csvContent += "Pass Count," + job.pass_count + "\n";
            csvContent += "Fail Count," + job.pass_count + "\n\n";

            csvContent += "SCAN LOG\n";
            csvContent += "Timestamp,Barcode,Status\n";

            // Note: recent_scans only keeps last 50. 
            // For a full log, we'd need to store all scans in memory or IndexedDB.
            // For now, we export what we have.
            job.recent_scans.forEach(scan => {
                csvContent += `${scan.timestamp},${scan.barcode},${scan.status}\n`;
            });
        }

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    beep(freq, duration, type) {
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();

        osc.type = type;
        osc.frequency.value = freq;

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.start();

        // Fade out to avoid clicking
        gain.gain.setValueAtTime(1, this.audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + (duration / 1000));

        osc.stop(this.audioCtx.currentTime + (duration / 1000));
    }

    flash(type) {
        if (!this.state.flashEnabled) return;
        const overlay = document.getElementById('flash-overlay');
        overlay.className = '';
        void overlay.offsetWidth; // Trigger reflow
        overlay.classList.add(type === 'pass' ? 'flash-pass' : 'flash-fail');
    }

    startClock() {
        setInterval(() => {
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleTimeString();
            if (this.state.activeJob) this.render(); // Update elapsed time
        }, 1000);
    }

    showEndModal() {
        document.getElementById('end-job-modal').classList.remove('hidden');
    }

    hideEndModal() {
        document.getElementById('end-job-modal').classList.add('hidden');
    }
}

// Start App
window.addEventListener('DOMContentLoaded', () => {
    window.app = new BarcodeApp();
});
