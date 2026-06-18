/**
 * TurboShare — Mobile application main logic.
 *
 * Handles the SPA flow: fetch session info → PIN entry → confirm →
 * wait for handshake → transfer → success/error.
 */

(function () {
    'use strict';

    // Extract token from current URL path: /ts/{token}/
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    const TOKEN = pathParts.length >= 2 ? pathParts[1] : '';
    const API_BASE = `/ts/${TOKEN}/api`;

    let sessionMode = 'send';  // 'send' = laptop sends, phone receives
    let selectedFiles = null;
    let sessionFiles = [];
    let safeTransferEnabled = true;

    // ── Initialise ─────────────────────────────────────────────────

    window.App = {
        showSection: showSection,
        showSuccess: showSuccess,
        showError: showError,
        updateConfirmButtonState: updateConfirmButtonState,
    };

    document.addEventListener('DOMContentLoaded', init);

    async function init() {
        if (!TOKEN) {
            showError('Invalid session URL.');
            return;
        }

        // Set download token
        if (window.Download) window.Download.setToken(TOKEN);

        // Fetch session info
        try {
            const res = await fetch(`${API_BASE}/session-info`);
            const data = await res.json();
            sessionMode = data.mode;
            safeTransferEnabled = data.safe_transfer !== false;
            setupLanding(data);
            if (sessionMode === 'send') {
                startSessionInfoPolling();
            }
        } catch (e) {
            showError('Could not connect to TurboShare. Make sure you are on the same network.');
        }

        // Confirm button
        document.getElementById('btn-confirm').addEventListener('click', onConfirm);

        // Upload area
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', onFilesSelected);
        }

        // Load Lottie animations
        loadLottieAnimations();
    }

    // ── Section management ─────────────────────────────────────────

    function showSection(id) {
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        const section = document.getElementById(id);
        if (section) section.classList.add('active');

        // Stop polling if we transition away from landing or waiting sections
        if (id !== 'sec-landing' && id !== 'sec-waiting') {
            stopSessionInfoPolling();
        }
    }

    // ── Landing setup ──────────────────────────────────────────────

    function setupLanding(data) {
        const indicator = document.getElementById('mode-indicator');
        const confirmBtn = document.getElementById('btn-confirm');

        // Add class to connection-nodes to dynamically swap left/right nodes
        const connectionNodes = document.querySelector('.connection-nodes');
        if (connectionNodes) {
            connectionNodes.classList.remove('mode-send', 'mode-receive');
            connectionNodes.classList.add('mode-' + data.mode);
        }

        if (data.mode === 'send') {
            // Phone is receiving files from laptop
            indicator.textContent = 'Files ready for you to download';
            document.getElementById('file-list-card').style.display = 'block';
            document.getElementById('upload-area').style.display = 'none';
            sessionFiles = data.files || [];

            renderFileList(data.files, data.total_size);

            if (!safeTransferEnabled) {
                confirmBtn.textContent = 'Accept & Download';
            }
        } else {
            // Phone is sending files to laptop
            indicator.textContent = 'Select files to send to the laptop';
            document.getElementById('file-list-card').style.display = 'none';
            document.getElementById('upload-area').style.display = 'block';

            if (!safeTransferEnabled) {
                confirmBtn.textContent = 'Send Files';
            }
        }

        if (!safeTransferEnabled) {
            // Hide PIN labels and inputs
            const pinLabel = document.querySelector('.pin-label');
            if (pinLabel) pinLabel.style.display = 'none';
            const pinContainer = document.getElementById('pin-container');
            if (pinContainer) pinContainer.style.display = 'none';
        }

        updateConfirmButtonState();
    }

    function renderFileList(files, totalSize) {
        const container = document.getElementById('file-list');
        container.innerHTML = '';
        files.forEach(f => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `
                <span class="file-icon">${window.getFileIcon(f.name)}</span>
                <span class="file-name">${window.escapeHtml(f.name)}</span>
                <span class="file-size">${window.formatSize(f.size)}</span>
            `;
            container.appendChild(item);
        });

        document.getElementById('file-count').textContent =
            files.length + ' file' + (files.length !== 1 ? 's' : '');
        document.getElementById('total-size').textContent =
            window.formatSize(totalSize);
    }

    // ── File selection (upload mode) ───────────────────────────────

    function onFilesSelected(e) {
        selectedFiles = e.target.files;
        if (!selectedFiles || selectedFiles.length === 0) return;

        const listContainer = document.getElementById('selected-files-list');
        listContainer.innerHTML = '';
        let total = 0;

        for (let i = 0; i < selectedFiles.length; i++) {
            const f = selectedFiles[i];
            total += f.size;
            const item = document.createElement('div');
            item.className = 'file-item';
            item.innerHTML = `
                <span class="file-icon">${window.getFileIcon(f.name)}</span>
                <span class="file-name">${window.escapeHtml(f.name)}</span>
                <span class="file-size">${window.formatSize(f.size)}</span>
            `;
            listContainer.appendChild(item);
        }

        document.getElementById('selected-files-card').style.display = 'block';
        document.getElementById('selected-count').textContent =
            selectedFiles.length + ' file' + (selectedFiles.length !== 1 ? 's' : '');
        document.getElementById('selected-size').textContent = window.formatSize(total);

        document.getElementById('upload-area').style.display = 'none';

        updateConfirmButtonState();
    }

    // ── PIN confirmation ───────────────────────────────────────────

    async function onConfirm() {
        const btn = document.getElementById('btn-confirm');
        btn.disabled = true;

        if (sessionMode === 'receive' && (!selectedFiles || selectedFiles.length === 0)) {
            const fileWarning = document.getElementById('file-warning');
            if (fileWarning) fileWarning.style.display = 'block';
            btn.disabled = false;
            return;
        }

        if (!safeTransferEnabled) {
            btn.textContent = 'Connecting…';
            try {
                const res = await fetch(`${API_BASE}/verify-pin`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pin: '000000' }), // Send dummy PIN
                });
                const data = await res.json();
                if (data.status === 'ok') {
                    await fetch(`${API_BASE}/confirm`, { method: 'POST' });
                    showSection('sec-waiting');
                    listenForHandshake();
                } else {
                    showError('Failed to initialize connection.');
                    btn.disabled = false;
                }
            } catch (e) {
                showError('Connection error. Try again.');
                btn.disabled = false;
            }
            return;
        }

        const pin = window.PinInput.getPin();
        if (pin.length < 6) return;

        btn.textContent = 'Verifying…';

        try {
            // Verify PIN
            const res = await fetch(`${API_BASE}/verify-pin`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin: pin }),
            });
            const data = await res.json();

            if (data.status === 'ok') {
                // PIN correct — confirm intent (Stage 1)
                await fetch(`${API_BASE}/confirm`, { method: 'POST' });

                // Transition to waiting
                showSection('sec-waiting');

                // Listen for handshake (Stage 3)
                listenForHandshake();

            } else if (data.status === 'wrong') {
                window.PinInput.showError(data.message || 'Wrong PIN');
                btn.disabled = false;
                btn.textContent = 'Confirm';
            } else if (data.status === 'rate_limited') {
                window.PinInput.showError('Too fast! Wait 2 seconds.');
                setTimeout(() => {
                    btn.disabled = false;
                    btn.textContent = 'Confirm';
                }, 2000);
            } else if (data.status === 'max_attempts' || data.status === 'expired') {
                showError(data.message || 'Session expired. Scan the new QR code.');
            } else {
                window.PinInput.showError(data.message || 'Verification failed.');
                btn.disabled = false;
                btn.textContent = 'Confirm';
            }
        } catch (e) {
            window.PinInput.showError('Connection error. Try again.');
            btn.disabled = false;
            btn.textContent = 'Confirm';
        }
    }

    // ── Handshake SSE ──────────────────────────────────────────────

    function listenForHandshake() {
        const source = new EventSource(`${API_BASE}/handshake`);

        source.onmessage = async function (event) {
            try {
                const data = JSON.parse(event.data);

                if (data.event === 'ready') {
                    source.close();

                    // Acknowledge ready (Stage 3)
                    await fetch(`${API_BASE}/ready`, { method: 'POST' });

                    // Start transfer
                    showSection('sec-transfer');

                    if (sessionMode === 'receive' && selectedFiles) {
                        // Phone is sender — upload files
                        window.Download.uploadFiles(TOKEN, selectedFiles);
                    } else if (sessionMode === 'send') {
                        // Phone is receiver — perform final session-info fetch to guarantee up-to-date file list
                        try {
                            const res = await fetch(`${API_BASE}/session-info`);
                            const finalData = await res.json();
                            sessionFiles = finalData.files || [];
                        } catch (e) {
                            console.warn('Failed to perform final session info check:', e);
                        }

                        // Start download queue with the guaranteed latest files
                        if (window.Download && sessionFiles.length > 0) {
                            window.Download.startQueue(sessionFiles);
                        }
                    }

                    // Start progress listener
                    window.Progress.start(TOKEN);

                } else if (data.event === 'session_cancelled') {
                    source.close();
                    showError('Session was cancelled by the sender.');
                }
            } catch (e) {
                console.warn('Handshake parse error:', e);
            }
        };

        source.onerror = function () {
            // SSE auto-reconnects, but log for debugging
            console.warn('Handshake SSE error');
        };
    }

    // ── Success ────────────────────────────────────────────────────

    function showSuccess(data) {
        window.Progress.stop();
        showSection('sec-success');

        // Inject custom animated SVG checkmark
        const successContainer = document.getElementById('lottie-success');
        if (successContainer) {
            successContainer.innerHTML = `
                <svg class="checkmark-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
                    <circle class="checkmark-circle" cx="26" cy="26" r="25" fill="none"/>
                    <path class="checkmark-check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
                </svg>
            `;
        }

        // Dynamically update success title based on mode (send = phone received, receive = phone sent)
        const titleEl = document.querySelector('.success-title');
        if (titleEl) {
            if (sessionMode === 'send') {
                titleEl.textContent = 'All files received! 🎉';
            } else {
                titleEl.textContent = 'All files sent! 🎉';
            }
        }

        const files = data.files || [];
        const totalSize = data.total_bytes || 0;
        const avgSpeed = data.average_speed_mbps || data.speed_mbps || 0;
        const elapsed = data.elapsed_seconds || 0;

        document.getElementById('stat-files').textContent = files.length;
        document.getElementById('stat-size').textContent = window.formatSize(totalSize);
        document.getElementById('stat-speed').textContent = avgSpeed.toFixed(1) + ' MB/s';

        // Display exact elapsed time from server
        if (elapsed < 60) {
            document.getElementById('stat-time').textContent = Math.round(elapsed) + 's';
        } else {
            document.getElementById('stat-time').textContent =
                Math.floor(elapsed / 60) + 'm ' + Math.round(elapsed % 60) + 's';
        }

        // Download location hint
        const hint = document.getElementById('download-hint');
        const ua = navigator.userAgent.toLowerCase();
        if (sessionMode === 'send') {
            if (ua.includes('iphone') || ua.includes('ipad')) {
                hint.textContent = '📂 Files saved to Files app → Downloads';
            } else {
                hint.textContent = '📂 Files saved to your Downloads folder';
            }
        } else {
            hint.textContent = '✅ Files sent to the laptop successfully!';
        }
    }

    // ── Error ──────────────────────────────────────────────────────

    function showError(message) {
        window.Progress.stop();
        showSection('sec-error');
        document.getElementById('error-detail').textContent = message;
    }

    // ── Lottie ─────────────────────────────────────────────────────

    function loadLottieAnimations() {
        if (typeof lottie === 'undefined') return;

        const animations = {
            'lottie-transfer': 'transferring',
            'lottie-error': 'error',
        };

        Object.entries(animations).forEach(([containerId, name]) => {
            const container = document.getElementById(containerId);
            if (!container) return;

            fetch(`/ts/${TOKEN}/static/animations/${name}.json`)
                .then(r => r.json())
                .then(animData => {
                    lottie.loadAnimation({
                        container: container,
                        renderer: 'svg',
                        loop: name !== 'success',
                        autoplay: true,
                        animationData: animData,
                    });
                })
                .catch(() => {
                    // Fallback: show a CSS pulse
                    container.innerHTML = '<div style="width:60px;height:60px;border-radius:50%;background:rgba(0,212,170,0.2);margin:auto;animation:pulse 2s ease infinite;"></div>';
                });
        });
    }

    // ── Session Info Polling (Real-Time Sync) ──────────────────────

    let sessionInfoPollInterval = null;

    function startSessionInfoPolling() {
        if (sessionInfoPollInterval) return;
        sessionInfoPollInterval = setInterval(async () => {
            const activeSection = document.querySelector('.section.active');
            if (!activeSection || (activeSection.id !== 'sec-landing' && activeSection.id !== 'sec-waiting')) {
                stopSessionInfoPolling();
                return;
            }
            if (sessionMode !== 'send') {
                stopSessionInfoPolling();
                return;
            }

            try {
                const res = await fetch(`${API_BASE}/session-info`);
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();

                // If transfer already started/ended, stop polling
                if (data.state === 'transferring' || data.state === 'completed' || data.state === 'cancelled') {
                    stopSessionInfoPolling();
                    return;
                }

                sessionFiles = data.files || [];
                renderFileList(data.files, data.total_size);
            } catch (e) {
                console.warn('Session info poll failed:', e);
            }
        }, 1000); // Poll every 1 second
    }

    function stopSessionInfoPolling() {
        if (sessionInfoPollInterval) {
            clearInterval(sessionInfoPollInterval);
            sessionInfoPollInterval = null;
        }
    }

    function updateConfirmButtonState() {
        const confirmBtn = document.getElementById('btn-confirm');
        const fileWarning = document.getElementById('file-warning');
        if (!confirmBtn) return;

        let filesSelected = selectedFiles && selectedFiles.length > 0;
        let pinComplete = true;

        if (safeTransferEnabled) {
            const pin = window.PinInput ? window.PinInput.getPin() : '';
            pinComplete = pin.length === 6;
        }

        // Show/hide warning for files
        if (fileWarning) {
            if (sessionMode === 'receive' && !filesSelected) {
                if (pinComplete) {
                    fileWarning.style.display = 'block';
                } else {
                    fileWarning.style.display = 'none';
                }
            } else {
                fileWarning.style.display = 'none';
            }
        }

        // Validate button disable state
        if (sessionMode === 'receive' && !filesSelected) {
            confirmBtn.disabled = true;
            return;
        }

        if (safeTransferEnabled && !pinComplete) {
            confirmBtn.disabled = true;
            return;
        }

        confirmBtn.disabled = false;
    }
})();
