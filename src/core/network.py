"""
TurboShare — Network utilities.

Detects the local IP of the active network interface (works for WiFi,
hotspot, and Ethernet) and finds an available TCP port in the ephemeral
range.
"""

import socket
import random
from src.core.config import PORT_RANGE_START, PORT_RANGE_END


def get_local_ip() -> str:
    """Return the local IP used to reach the LAN.

    Uses a non-connecting UDP socket trick — no actual packets leave the
    machine, so this works even without internet (hotspot / router).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 10.255.255.255 is unreachable but forces the OS to select
        # the outgoing interface.  No packet is actually sent for UDP.
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def find_available_port(
    start: int | None = None,
    end: int = PORT_RANGE_END,
    host: str = "0.0.0.0",
) -> int:
    """Find a free TCP port in the given range.

    Picks a random starting point in the ephemeral range and scans
    upward until a free port is found.  Raises ``RuntimeError`` if
    the entire range is exhausted.
    """
    if start is None:
        start = random.randint(PORT_RANGE_START, PORT_RANGE_END)

    attempts = end - PORT_RANGE_START + 1
    port = start
    for _ in range(attempts):
        if port > PORT_RANGE_END:
            port = PORT_RANGE_START
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            return port
        except OSError:
            port += 1
            continue
    raise RuntimeError(
        f"No available port found in range {PORT_RANGE_START}–{PORT_RANGE_END}"
    )


def configure_socket(sock: socket.socket) -> None:
    """Apply performance-critical socket options.

    • 4 MB send / receive buffers
    • TCP_NODELAY (disable Nagle — reduce latency for small packets)
    """
    from src.core.config import SOCKET_BUFFER_SIZE

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFER_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFER_SIZE)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError:
        pass  # Some options may not be available on all platforms
