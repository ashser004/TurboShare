"""
TurboShare — File assembler with chunk verification.

Pre-allocates the target file on disk, writes incoming chunks to their
correct offsets, verifies MD5 checksums, and finalises the file once
every chunk is confirmed.
"""

import hashlib
import math
import logging
from pathlib import Path
from threading import Lock

from src.core.config import CHUNK_SIZE, TEMP_EXT

log = logging.getLogger(__name__)


class FileAssembler:
    """Write-side counterpart to FileChunker.  Assembles a file from
    individually-received chunks.
    """

    def __init__(
        self,
        save_dir: Path,
        file_name: str,
        file_size: int,
        chunk_size: int = CHUNK_SIZE,
    ) -> None:
        self.file_name = file_name
        self.file_size = file_size
        self.chunk_size = chunk_size
        self.total_chunks = max(1, math.ceil(file_size / chunk_size))

        # Temp file — only renamed on successful completion
        self.temp_path = save_dir / (file_name + TEMP_EXT)
        self.final_path = save_dir / file_name

        self._received: set[int] = set()
        self._lock = Lock()

        # Pre-allocate the full file size on disk
        self._pre_allocate()

    # ── Pre-allocation ──────────────────────────────────────────────

    def _pre_allocate(self) -> None:
        """Create the .turbotemp file at the full target size.

        On Windows we seek to (size - 1) and write a zero byte so the
        filesystem reserves contiguous blocks up front.
        """
        with open(self.temp_path, "wb") as f:
            if self.file_size > 0:
                f.seek(self.file_size - 1)
                f.write(b"\x00")
        log.debug(
            "Pre-allocated %s (%d bytes, %d chunks)",
            self.temp_path.name, self.file_size, self.total_chunks,
        )

    # ── Chunk reception ─────────────────────────────────────────────

    def write_chunk(
        self,
        index: int,
        data: bytes,
        expected_md5: str,
    ) -> bool:
        """Write a chunk at *index* after verifying its MD5.

        Returns ``True`` if the checksum matched and the chunk was
        written.  Returns ``False`` if verification failed (caller
        should re-request the chunk).
        """
        if index < 0 or index >= self.total_chunks:
            log.error("Chunk index %d out of range", index)
            return False

        if expected_md5:
            actual_md5 = hashlib.md5(data).hexdigest()
            if actual_md5 != expected_md5:
                log.warning(
                    "Checksum mismatch on chunk %d of %s (expected %s, got %s)",
                    index, self.file_name, expected_md5, actual_md5,
                )
                return False

        offset = index * self.chunk_size
        with self._lock:
            with open(self.temp_path, "r+b") as f:
                f.seek(offset)
                f.write(data)
            self._received.add(index)

        return True

    # ── Status ──────────────────────────────────────────────────────

    @property
    def is_complete(self) -> bool:
        return len(self._received) == self.total_chunks

    @property
    def progress(self) -> float:
        if self.total_chunks == 0:
            return 1.0
        return len(self._received) / self.total_chunks

    @property
    def bytes_received(self) -> int:
        # Last chunk may be smaller
        full_chunks = min(len(self._received), self.total_chunks - 1)
        has_last = (self.total_chunks - 1) in self._received
        last_chunk_size = self.file_size - (self.total_chunks - 1) * self.chunk_size
        return full_chunks * self.chunk_size + (last_chunk_size if has_last else 0)

    def missing_chunks(self) -> list[int]:
        return sorted(set(range(self.total_chunks)) - self._received)

    # ── Finalisation ────────────────────────────────────────────────

    def finalize(self) -> Path:
        """Rename .turbotemp → real filename.

        Raises ``RuntimeError`` if not all chunks have been received.
        Returns the final file path.
        """
        if not self.is_complete:
            raise RuntimeError(
                f"Cannot finalise {self.file_name}: "
                f"{len(self._received)}/{self.total_chunks} chunks received"
            )

        # Handle name collisions
        final = self.final_path
        counter = 1
        while final.exists():
            stem = self.final_path.stem
            suffix = self.final_path.suffix
            final = self.final_path.parent / f"{stem} ({counter}){suffix}"
            counter += 1

        self.temp_path.rename(final)
        self.final_path = final
        log.info("Finalised file: %s", final)
        return final

    # ── Cleanup ─────────────────────────────────────────────────────

    def cleanup(self) -> None:
        """Delete the temp file (called on cancel / error)."""
        try:
            if self.temp_path.exists():
                self.temp_path.unlink()
                log.info("Deleted temp file: %s", self.temp_path)
        except OSError as exc:
            log.warning("Failed to delete %s: %s", self.temp_path, exc)
