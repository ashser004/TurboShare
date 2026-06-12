"""
TurboShare — Low-level file I/O helpers.

Platform-specific pre-allocation and socket tuning helpers
used by the transfer engine and the server.
"""

import os
import socket
import logging
from pathlib import Path

from src.core.config import SOCKET_BUFFER_SIZE

log = logging.getLogger(__name__)


def pre_allocate_file(path: Path, size: int) -> None:
    """Pre-allocate *size* bytes for *path* on Windows.

    Opens the file, seeks to ``size - 1``, writes a null byte so the
    filesystem allocates contiguous blocks upfront.  This prevents
    fragmentation and dynamic growth during transfer.
    """
    with open(path, "wb") as f:
        if size > 0:
            f.seek(size - 1)
            f.write(b"\x00")
    log.debug("Pre-allocated %d bytes at %s", size, path)


def configure_tcp_socket(sock: socket.socket) -> None:
    """Apply performance options to a TCP socket.

    • SO_RCVBUF / SO_SNDBUF → 4 MB
    • TCP_NODELAY → disable Nagle's algorithm
    """
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFER_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFER_SIZE)
    except OSError:
        log.debug("Could not set socket buffer size to %d", SOCKET_BUFFER_SIZE)

    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError:
        log.debug("Could not set TCP_NODELAY")


def safe_delete(path: Path) -> bool:
    """Delete a file if it exists, returning True on success."""
    try:
        if path.exists():
            path.unlink()
            return True
    except OSError as exc:
        log.warning("Could not delete %s: %s", path, exc)
    return False
