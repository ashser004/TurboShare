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

    // ── Initialise ─────────────────────────────────────────────────

    window.App = {
        showSection: showSection,
        showSuccess: showSuccess,
        showError: showError,
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
            setupLanding(data);
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
    }

    // ── Landing setup ──────────────────────────────────────────────

    function setupLanding(data) {
        const indicator = document.getElementById('mode-indicator');

        if (data.mode === 'send') {
            // Phone is receiving files from laptop
            indicator.textContent = 'Files ready for you to download';
            document.getElementById('file-list-card').style.display = 'block';
            document.getElementById('upload-area').style.display = 'none';

            renderFileList(data.files, data.total_size);
        } else {
            // Phone is sending files to laptop
            indicator.textContent = 'Select files to send to the laptop';
            document.getElementById('file-list-card').style.display = 'none';
            document.getElementById('upload-area').style.display = 'block';
        }
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
    }

    // ── PIN confirmation ───────────────────────────────────────────

    async function onConfirm() {
        const pin = window.PinInput.getPin();
        if (pin.length < 6) return;

        const btn = document.getElementById('btn-confirm');
        btn.disabled = true;
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

        const files = data.files || [];
        const totalSize = data.total_bytes || 0;
        const speed = data.speed_mbps || 0;
        const eta = data.eta_seconds || 0;

        document.getElementById('stat-files').textContent = files.length;
        document.getElementById('stat-size').textContent = window.formatSize(totalSize);
        document.getElementById('stat-speed').textContent = speed.toFixed(1) + ' MB/s';

        // Approximate elapsed time
        const elapsed = speed > 0 ? totalSize / (speed * 1024 * 1024) : 0;
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
            'lottie-success': 'success',
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
})();
