"""
TurboShare — Transfer engine.

Orchestrates multi-file chunked transfers.  Manages the queue of files,
coordinates chunkers / assemblers, tracks per-file and overall progress,
enforces the 30 GB cumulative cap, and emits PySide6 signals for live
UI updates.
"""

from __future__ import annotations

import time
import logging
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.core.config import CHUNK_SIZE, MAX_TRANSFER_SIZE
from src.core.session import FileEntry
from src.transfer.chunker import FileChunker
from src.transfer.assembler import FileAssembler
from src.transfer.speed_tracker import SpeedTracker

log = logging.getLogger(__name__)


class TransferSignals(QObject):
    """Signals emitted by the transfer engine — connect to UI slots."""
    progress_updated = Signal(dict)     # full progress snapshot
    file_started = Signal(int)          # file id
    file_completed = Signal(int)        # file id
    transfer_completed = Signal(dict)   # summary {files, size, speed, time}
    error_occurred = Signal(str)        # human-readable message
    cap_exceeded = Signal(int)          # file id that caused the 30 GB breach


class TransferEngine:
    """Manages the full lifecycle of a multi-file transfer session."""

    def __init__(self) -> None:
        self.signals = TransferSignals()
        self.speed = SpeedTracker()

        # Sender-side chunkers (file_id → FileChunker)
        self._chunkers: dict[int, FileChunker] = {}

        # Receiver-side assemblers (file_id → FileAssembler)
        self._assemblers: dict[int, FileAssembler] = {}

        self._files: list[FileEntry] = []
        self._current_file_id: int = -1
        self._cancelled: bool = False
        self._cumulative_bytes: int = 0
        self._bytes_sent_per_file: dict[int, int] = {}

    # ── Setup ───────────────────────────────────────────────────────

    def prepare_send(self, files: list[FileEntry]) -> bool:
        """Prepare chunkers for sending.

        Returns False if total size exceeds 30 GB.
        """
        total = sum(f.size for f in files)
        if total > MAX_TRANSFER_SIZE:
            self.signals.error_occurred.emit(
                f"Total size ({total / (1024**3):.1f} GB) exceeds "
                f"the {MAX_TRANSFER_SIZE / (1024**3):.0f} GB limit."
            )
            return False

        self._files = files
        self._cancelled = False
        self._cumulative_bytes = 0
        self._bytes_sent_per_file = {f.id: 0 for f in files}

        for f in files:
            self._chunkers[f.id] = FileChunker(f.path)

        self.speed.start()
        log.info("Prepared %d files for sending (%.1f MB)", len(files), total / (1024**2))
        return True

    def prepare_receive(
        self,
        files: list[FileEntry],
        save_dir: Path,
        chunk_size: int = CHUNK_SIZE,
    ) -> bool:
        """Prepare assemblers for receiving files."""
        self._files = files
        self._cancelled = False
        self._cumulative_bytes = 0
        self._bytes_sent_per_file = {}

        for f in files:
            self._assemblers[f.id] = FileAssembler(
                save_dir=save_dir,
                file_name=f.name,
                file_size=f.size,
                chunk_size=chunk_size,
            )

        self.speed.start()
        log.info("Prepared to receive %d files into %s with chunk size %d", len(files), save_dir, chunk_size)
        return True

    # ── Sender: serve a chunk on demand ─────────────────────────────

    def get_chunk(self, file_id: int, chunk_index: int) -> tuple[bytes, str] | None:
        """Return ``(data, md5_hex)`` for the requested chunk, or None."""
        if self._cancelled:
            return None
        chunker = self._chunkers.get(file_id)
        if chunker is None:
            return None
        try:
            data, md5 = chunker.get_chunk(chunk_index)
            self.speed.record(len(data))
            self._cumulative_bytes += len(data)
            self._bytes_sent_per_file[file_id] = self._bytes_sent_per_file.get(file_id, 0) + len(data)
            self._update_progress(file_id)
            return data, md5
        except IndexError:
            return None

    # ── Receiver: accept a chunk ────────────────────────────────────

    def receive_chunk(
        self,
        file_id: int,
        chunk_index: int,
        data: bytes,
        expected_md5: str,
    ) -> bool:
        """Write an incoming chunk.  Returns True if checksum passed."""
        if self._cancelled:
            return False

        # 30 GB cumulative cap check
        if self._cumulative_bytes + len(data) > MAX_TRANSFER_SIZE:
            log.warning("30 GB cap reached during file %d", file_id)
            self.signals.cap_exceeded.emit(file_id)
            return False

        assembler = self._assemblers.get(file_id)
        if assembler is None:
            return False

        ok = assembler.write_chunk(chunk_index, data, expected_md5)
        if ok:
            self.speed.record(len(data))
            self._cumulative_bytes += len(data)
            self._update_progress(file_id)

            if assembler.is_complete:
                try:
                    assembler.finalize()
                    self._mark_file_done(file_id)
                except Exception as exc:
                    self.signals.error_occurred.emit(str(exc))

        return ok

    # ── Progress ────────────────────────────────────────────────────

    def _update_progress(self, active_file_id: int) -> None:
        """Emit a progress snapshot for the UI."""
        total_size = sum(f.size for f in self._files)
        if total_size == 0:
            total_size = 1

        active_file = next((f for f in self._files if f.id == active_file_id), None)

        # Per-file progress
        if active_file_id in self._assemblers:
            asm = self._assemblers[active_file_id]
            file_progress = asm.progress
        elif active_file_id in self._chunkers:
            # For sender mode, track via bytes sent for this specific file
            bytes_sent = self._bytes_sent_per_file.get(active_file_id, 0)
            file_size = active_file.size if active_file else 1
            file_progress = min(1.0, bytes_sent / max(1, file_size))
        else:
            file_progress = 0.0

        if active_file:
            active_file.progress = file_progress
            if active_file.status == "waiting":
                active_file.status = "transferring"
                self.signals.file_started.emit(active_file_id)

        remaining = total_size - self._cumulative_bytes
        self.signals.progress_updated.emit({
            "current_file": active_file.name if active_file else "",
            "current_file_id": active_file_id,
            "current_file_progress": file_progress,
            "overall_progress": min(1.0, self._cumulative_bytes / total_size),
            "speed_mbps": round(self.speed.speed_mbps, 1),
            "eta_seconds": round(self.speed.eta_seconds(remaining), 1),
            "bytes_transferred": self._cumulative_bytes,
            "total_bytes": total_size,
            "files": [
                {
                    "id": f.id,
                    "name": f.name,
                    "size": f.size,
                    "status": f.status,
                    "progress": f.progress,
                }
                for f in self._files
            ],
        })

    def _mark_file_done(self, file_id: int) -> None:
        for f in self._files:
            if f.id == file_id:
                f.status = "done"
                f.progress = 1.0
                break
        self.signals.file_completed.emit(file_id)
        log.info("File %d completed", file_id)

        # Check if all files are done
        if all(f.status == "done" for f in self._files):
            self._complete()

    def mark_send_file_done(self, file_id: int) -> None:
        """Called by the server when all chunks of a file have been downloaded."""
        self._mark_file_done(file_id)

    def _complete(self) -> None:
        total_size = sum(f.size for f in self._files)
        self.signals.transfer_completed.emit({
            "total_files": len(self._files),
            "total_size": total_size,
            "average_speed_mbps": round(self.speed.average_speed_mbps, 1),
            "elapsed_seconds": round(self.speed.elapsed_seconds, 1),
        })
        log.info("Transfer complete: %d files, %.1f MB", len(self._files), total_size / (1024**2))

    # ── Cancellation ────────────────────────────────────────────────

    def cancel(self) -> None:
        """Cancel the in-progress transfer and clean up temp files."""
        self._cancelled = True

        # Clean up chunkers
        for chunker in self._chunkers.values():
            chunker.close()
        self._chunkers.clear()

        # Clean up assemblers (delete .turbotemp files)
        for assembler in self._assemblers.values():
            assembler.cleanup()
        self._assemblers.clear()

        log.info("Transfer cancelled and cleaned up")

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    # ── Queries ─────────────────────────────────────────────────────

    def get_chunker(self, file_id: int) -> FileChunker | None:
        return self._chunkers.get(file_id)

    def get_assembler(self, file_id: int) -> FileAssembler | None:
        return self._assemblers.get(file_id)

    def get_progress_snapshot(self) -> dict:
        """Return a JSON-serialisable progress snapshot for SSE."""
        total_size = sum(f.size for f in self._files)
        if total_size == 0:
            total_size = 1

        current = next((f for f in self._files if f.status == "transferring"), None)
        remaining = total_size - self._cumulative_bytes

        return {
            "current_file": current.name if current else "",
            "current_file_id": current.id if current else -1,
            "current_file_progress": current.progress if current else 0.0,
            "overall_progress": min(1.0, self._cumulative_bytes / total_size),
            "speed_mbps": round(self.speed.speed_mbps, 1),
            "average_speed_mbps": round(self.speed.average_speed_mbps, 1),
            "eta_seconds": round(self.speed.eta_seconds(remaining), 1),
            "elapsed_seconds": round(self.speed.elapsed_seconds, 1),
            "bytes_transferred": self._cumulative_bytes,
            "total_bytes": total_size,
            "files": [
                {
                    "id": f.id,
                    "name": f.name,
                    "size": f.size,
                    "status": f.status,
                    "progress": round(f.progress, 4),
                }
                for f in self._files
            ],
        }
