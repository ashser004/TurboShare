/**
 * TurboShare — Real-time progress tracking via SSE.
 *
 * Connects to the server's SSE progress endpoint and updates
 * the transfer UI in real time.
 */

(function () {
    'use strict';

    let eventSource = null;

    window.Progress = {
        start: startListening,
        stop: stopListening,
    };

    function startListening(token) {
        if (eventSource) eventSource.close();

        const url = `/ts/${token}/api/progress`;
        eventSource = new EventSource(url);

        eventSource.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                handleEvent(data);
            } catch (e) {
                console.warn('Progress parse error:', e);
            }
        };

        eventSource.onerror = function () {
            console.warn('SSE connection error — will auto-reconnect');
        };
    }

    function stopListening() {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    }

    function handleEvent(data) {
        const event = data.event;

        if (event === 'progress') {
            updateProgress(data);
        } else if (event === 'completed') {
            updateProgress(data);
            // Small delay then transition
            setTimeout(() => {
                if (window.App) window.App.showSuccess(data);
            }, 500);
        } else if (event === 'cancelled') {
            if (window.App) window.App.showError('Transfer was cancelled.');
        } else if (event === 'error') {
            if (window.App) window.App.showError(data.message || 'Transfer failed.');
        }
    }

    function updateProgress(data) {
        // Current file
        const nameEl = document.getElementById('transfer-current-file');
        if (nameEl && data.current_file) {
            nameEl.textContent = '📄 ' + data.current_file;
        }

        // Per-file progress bar
        const fileBar = document.getElementById('transfer-file-bar');
        const filePct = document.getElementById('transfer-file-pct');
        if (fileBar) {
            const pct = Math.round((data.current_file_progress || 0) * 100);
            fileBar.style.width = pct + '%';
            if (filePct) filePct.textContent = pct + '%';
        }

        // Speed
        const speedEl = document.getElementById('transfer-speed');
        if (speedEl) {
            const mbps = data.speed_mbps || 0;
            if (mbps < 1) {
                speedEl.textContent = Math.round(mbps * 1024) + ' KB/s';
            } else {
                speedEl.textContent = mbps.toFixed(1) + ' MB/s';
            }
        }

        // ETA
        const etaEl = document.getElementById('transfer-eta');
        if (etaEl) {
            const eta = data.eta_seconds;
            if (eta < 0) {
                etaEl.textContent = 'estimating…';
            } else if (eta < 60) {
                etaEl.textContent = '~' + Math.round(eta) + 's remaining';
            } else {
                const m = Math.floor(eta / 60);
                const s = Math.round(eta % 60);
                etaEl.textContent = '~' + m + 'm ' + s + 's remaining';
            }
        }

        // Bytes transferred
        const bytesEl = document.getElementById('transfer-bytes');
        if (bytesEl) {
            bytesEl.textContent = formatSize(data.bytes_transferred || 0) +
                ' / ' + formatSize(data.total_bytes || 0);
        }

        // Overall bar
        const overallBar = document.getElementById('transfer-overall-bar');
        if (overallBar) {
            overallBar.style.width = Math.round((data.overall_progress || 0) * 100) + '%';
        }

        // Files count
        const countEl = document.getElementById('transfer-files-count');
        if (countEl && data.files) {
            const done = data.files.filter(f => f.status === 'done').length;
            countEl.textContent = done + ' of ' + data.files.length;
        }

        // File status list
        updateFileStatusList(data.files || []);

        // Trigger file downloads for completed files (send mode)
        if (window.Download && data.files) {
            window.Download.checkCompleted(data.files);
        }
    }

    function updateFileStatusList(files) {
        const container = document.getElementById('transfer-file-list');
        if (!container) return;

        // Only rebuild if file count changed
        if (container.childElementCount !== files.length) {
            container.innerHTML = '';
            files.forEach(f => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.id = 'tf-' + f.id;
                item.innerHTML = `
                    <span class="file-icon">${getFileIcon(f.name)}</span>
                    <span class="file-name">${escapeHtml(f.name)}</span>
                    <span class="file-size">${formatSize(f.size)}</span>
                    <span class="file-status" id="tfs-${f.id}"></span>
                `;
                container.appendChild(item);
            });
        }

        // Update statuses
        files.forEach(f => {
            const statusEl = document.getElementById('tfs-' + f.id);
            if (statusEl) {
                if (f.status === 'done') statusEl.textContent = '✅';
                else if (f.status === 'transferring') statusEl.textContent = '🔄';
                else if (f.status === 'error') statusEl.textContent = '❌';
                else statusEl.textContent = '⏳';
            }
        });
    }

    // ── Helpers ──────────────────────────────────────────────────

    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    }

    function getFileIcon(name) {
        const ext = name.lastIndexOf('.') >= 0 ? name.slice(name.lastIndexOf('.')).toLowerCase() : '';
        const icons = {
            '.jpg':'🖼️','.jpeg':'🖼️','.png':'🖼️','.gif':'🖼️','.webp':'🖼️','.heic':'🖼️',
            '.mp4':'🎬','.mkv':'🎬','.avi':'🎬','.mov':'🎬','.webm':'🎬',
            '.mp3':'🎵','.wav':'🎵','.flac':'🎵','.aac':'🎵','.m4a':'🎵',
            '.pdf':'📄','.doc':'📝','.docx':'📝','.txt':'📃',
            '.zip':'📦','.rar':'📦','.7z':'📦',
            '.py':'🐍','.js':'⚡','.html':'🌐','.css':'🎨',
            '.exe':'⚙️','.apk':'📱',
        };
        return icons[ext] || '📁';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Expose formatSize globally for other modules
    window.formatSize = formatSize;
    window.getFileIcon = getFileIcon;
    window.escapeHtml = escapeHtml;
})();
