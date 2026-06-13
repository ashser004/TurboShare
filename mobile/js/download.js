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

    let activeWorkersCount = 0;
    let desiredConcurrency = 4;
    let maxConcurrencyCap = 4;

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
     * with dynamically adjusted parallel connections per file.
     */
    async function uploadFiles(token, fileList) {
        sessionToken = token;

        // Detect device hardware specs for memory and CPU concurrency hints
        const deviceMemory = navigator.deviceMemory || 8; // Default to 8 GB if unsupported
        maxConcurrencyCap = deviceMemory < 3 ? 1 : (deviceMemory < 6 ? 2 : 4);
        desiredConcurrency = Math.min(4, maxConcurrencyCap);

        // Calculate dynamic chunk size
        let preferredChunkSize = 2097152; // Default 2 MB
        if (deviceMemory < 3) {
            preferredChunkSize = 524288; // 512 KB
        } else if (deviceMemory < 6) {
            preferredChunkSize = 1048576; // 1 MB
        }

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
                body: JSON.stringify({
                    files: filesData,
                    preferred_chunk_size: preferredChunkSize
                }),
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

            activeWorkersCount = 0;
            const workers = [];
            const initialWorkers = Math.min(desiredConcurrency, chunkQueue.length);
            for (let w = 0; w < initialWorkers; w++) {
                activeWorkersCount++;
                workers.push(uploadWorker(token, fileMeta.id, file, chunkQueue, chunkSize));
            }

            await Promise.all(workers);
        }
    }

    async function uploadWorker(token, fileId, file, queue, chunkSize) {
        while (queue.length > 0) {
            // Downshift active workers if desired concurrency was lowered
            if (activeWorkersCount > desiredConcurrency) {
                activeWorkersCount--;
                return;
            }

            const chunkIndex = queue.shift();
            if (chunkIndex === undefined) break;

            const offset = chunkIndex * chunkSize;
            const end = Math.min(offset + chunkSize, file.size);
            const blob = file.slice(offset, end);
            
            // Read to memory (essential for mobile OS file access / content URI stability)
            let buffer;
            try {
                buffer = await blob.arrayBuffer();
            } catch (e) {
                console.error(`Failed to read chunk ${chunkIndex} to buffer:`, e);
                if (window.App) {
                    window.App.showError(`Error reading file. Please try again.`);
                }
                activeWorkersCount--;
                return;
            }
            const data = new Uint8Array(buffer);

            // Upload with retry
            let success = false;
            let lastDuration = 0;

            for (let attempt = 0; attempt < 3; attempt++) {
                // Check concurrency limit before initiating fetch
                if (activeWorkersCount > desiredConcurrency) {
                    queue.unshift(chunkIndex); // put it back
                    activeWorkersCount--;
                    return;
                }

                const startTime = performance.now();
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

                    lastDuration = performance.now() - startTime;

                    if (res.ok) {
                        success = true;
                        break;
                    } else if (res.status === 413) {
                        // 30 GB cap or server size limit hit
                        if (window.App) window.App.showError("Transfer size limit exceeded.");
                        activeWorkersCount--;
                        return;
                    }
                } catch (e) {
                    console.warn(`Chunk ${chunkIndex} upload failed, retry ${attempt + 1}:`, e);
                    // Drop concurrency immediately on network error
                    desiredConcurrency = 1;
                    await new Promise(r => setTimeout(r, 1000));
                }
            }

            if (!success) {
                console.error(`Failed to upload chunk ${chunkIndex} after 3 retries`);
                if (window.App) {
                    window.App.showError(`Connection lost. Failed to upload chunk ${chunkIndex}.`);
                }
                activeWorkersCount--;
                return;
            }

            // --- Adaptive Tuning ---
            if (lastDuration > 0) {
                if (lastDuration < 800) {
                    // Fast: Increase concurrency limit if below max capacity
                    if (desiredConcurrency < maxConcurrencyCap) {
                        desiredConcurrency++;
                        // If queue has work and we have worker capacity, spin up a new worker
                        if (activeWorkersCount < desiredConcurrency && queue.length > 0) {
                            activeWorkersCount++;
                            uploadWorker(token, fileId, file, queue, chunkSize);
                        }
                    }
                } else if (lastDuration > 3000) {
                    // Slow: Decrease concurrency limit (minimum 1)
                    if (desiredConcurrency > 1) {
                        desiredConcurrency--;
                    }
                }
            }
        }

        activeWorkersCount--;
    }
})();
