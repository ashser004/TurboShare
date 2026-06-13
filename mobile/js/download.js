/**
 * TurboShare — File download trigger (Send mode: laptop → phone).
 *
 * When files complete transfer, triggers browser-native downloads
 * via dynamically created <a> links with Content-Disposition.
 *
 * In Upload mode (phone → laptop), handles chunked uploading.
 */

(function () {
    'use strict';

    const downloadedFiles = new Set();
    let sessionToken = '';
    let downloadQueue = [];
    let activeDownloadId = null;

    window.Download = {
        setToken: function (token) { sessionToken = token; },
        startQueue: startQueue,
        onProgressUpdate: onProgressUpdate,
        uploadFiles: uploadFiles,
        triggerDownload: triggerDownload,
    };

    /**
     * Start the sequential download queue.
     */
    function startQueue(files) {
        downloadQueue = [...files];
        activeDownloadId = null;
        downloadNext();
    }

    /**
     * Download the next file in the queue.
     */
    function downloadNext() {
        if (downloadQueue.length === 0) return;
        const nextFile = downloadQueue.shift();
        activeDownloadId = nextFile.id;
        triggerDownload(nextFile.id, nextFile.name);
    }

    /**
     * Listen to server progress updates and trigger next file when current completes.
     */
    function onProgressUpdate(files) {
        if (activeDownloadId === null) return;
        const activeFile = files.find(f => f.id === activeDownloadId);
        if (activeFile && activeFile.status === 'done') {
            activeDownloadId = null;
            downloadNext();
        }
    }

    /**
     * Trigger a native browser download for a file.
     */
    function triggerDownload(fileId, filename) {
        if (downloadedFiles.has(fileId)) return;
        downloadedFiles.add(fileId);

        const a = document.createElement('a');
        a.href = `/ts/${sessionToken}/api/download/${fileId}`;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        setTimeout(() => a.remove(), 1000);
    }

    /**
     * Upload files from the phone browser to the laptop (Receive mode).
     *
     * Sends an init request with file metadata, then uploads chunks
     * with 4 parallel connections per file.
     */
    async function uploadFiles(token, fileList) {
        sessionToken = token;
        const CHUNK_SIZE = 524288; // 512 KB
        const PARALLEL = 4;

        // Build file metadata
        const filesData = [];
        for (let i = 0; i < fileList.length; i++) {
            filesData.push({
                name: fileList[i].name,
                size: fileList[i].size,
            });
        }

        // Init upload on server
        let initResp;
        try {
            const res = await fetch(`/ts/${token}/api/upload-init`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ files: filesData }),
            });
            initResp = await res.json();
        } catch (e) {
            if (window.App) window.App.showError('Failed to initialise upload.');
            return;
        }

        if (initResp.status !== 'ok') {
            if (window.App) window.App.showError('Upload init failed.');
            return;
        }

        // Upload each file
        for (const fileMeta of initResp.files) {
            const file = fileList[fileMeta.id];
            const totalChunks = fileMeta.total_chunks;
            const chunkSize = fileMeta.chunk_size;

            // Create chunk upload queue
            const chunkQueue = [];
            for (let i = 0; i < totalChunks; i++) {
                chunkQueue.push(i);
            }

            // Process queue with PARALLEL workers
            const workers = [];
            for (let w = 0; w < PARALLEL; w++) {
                workers.push(uploadWorker(token, fileMeta.id, file, chunkQueue, chunkSize));
            }

            await Promise.all(workers);
        }
    }

    async function uploadWorker(token, fileId, file, queue, chunkSize) {
        while (queue.length > 0) {
            const chunkIndex = queue.shift();
            if (chunkIndex === undefined) break;

            const offset = chunkIndex * chunkSize;
            const end = Math.min(offset + chunkSize, file.size);
            const blob = file.slice(offset, end);
            
            // Read to memory (essential for mobile OS file access / content URI stability)
            const buffer = await blob.arrayBuffer();
            const data = new Uint8Array(buffer);

            // Upload with retry
            let success = false;
            for (let attempt = 0; attempt < 3; attempt++) {
                try {
                    const res = await fetch(
                        `/ts/${token}/api/chunk/${fileId}/${chunkIndex}`,
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/octet-stream'
                            },
                            body: data,
                        }
                    );

                    if (res.ok) {
                        success = true;
                        break;
                    } else if (res.status === 413) {
                        // 30 GB cap exceeded
                        return;
                    }
                } catch (e) {
                    console.warn(`Chunk ${chunkIndex} upload failed, retry ${attempt + 1}`);
                }
            }

            if (!success) {
                console.error(`Failed to upload chunk ${chunkIndex} after 3 retries`);
                if (window.App) {
                    window.App.showError(`Connection lost. Failed to upload chunk ${chunkIndex}.`);
                }
                return;
            }
        }
    }
})();
