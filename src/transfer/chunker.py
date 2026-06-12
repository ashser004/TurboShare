"""
TurboShare — File chunker with MD5 checksums.

Splits a file into 512 KB chunks and provides random-access reading
of individual chunks.  Uses mmap for files ≤ 2 GB for zero-copy reads,
falls back to seek+read for larger files.
"""

import hashlib
import math
import mmap
import logging
from pathlib import Path
from threading import Lock

from src.core.config import CHUNK_SIZE, MMAP_THRESHOLD

log = logging.getLogger(__name__)


class FileChunker:
    """Read-only random-access chunk provider for a single file."""

    def __init__(self, file_path: Path, chunk_size: int = CHUNK_SIZE) -> None:
        self.path = file_path
        self.chunk_size = chunk_size
        self.file_size = file_path.stat().st_size
        self.total_chunks = max(1, math.ceil(self.file_size / chunk_size))
        self._use_mmap = self.file_size <= MMAP_THRESHOLD and self.file_size > 0
        self._lock = Lock()

        # Open file handle (kept open for the session)
        self._fh = open(file_path, "rb")
        self._mm: mmap.mmap | None = None

        if self._use_mmap and self.file_size > 0:
            try:
                self._mm = mmap.mmap(
                    self._fh.fileno(), 0, access=mmap.ACCESS_READ,
                )
                log.debug("mmap reader for %s (%d chunks)", file_path.name, self.total_chunks)
            except Exception as exc:
                log.warning("mmap failed for %s, falling back to seek: %s", file_path.name, exc)
                self._use_mmap = False
                self._mm = None

    def get_chunk(self, index: int) -> tuple[bytes, str]:
        """Return ``(chunk_data, md5_hex)`` for chunk *index*.

        Raises ``IndexError`` if index is out of range.
        """
        if index < 0 or index >= self.total_chunks:
            raise IndexError(f"Chunk index {index} out of range (0–{self.total_chunks - 1})")

        offset = index * self.chunk_size
        length = min(self.chunk_size, self.file_size - offset)

        with self._lock:
            if self._mm is not None:
                data = self._mm[offset:offset + length]
            else:
                self._fh.seek(offset)
                data = self._fh.read(length)

        md5 = hashlib.md5(data).hexdigest()
        return data, md5

    def close(self) -> None:
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if self._fh and not self._fh.closed:
            self._fh.close()

    def __del__(self) -> None:
        self.close()
