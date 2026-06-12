"""
TurboShare — Single-IP session locking.

After a device authenticates, the session is locked to that device's
IP address.  Any request from another IP receives a 503 Session Busy.
"""

import logging

log = logging.getLogger(__name__)


class IPLock:
    """Thread-safe IP lock for one session."""

    def __init__(self) -> None:
        self._locked_ip: str | None = None

    def lock(self, ip: str) -> None:
        self._locked_ip = ip
        log.info("Session locked to IP: %s", ip)

    def is_allowed(self, ip: str) -> bool:
        if self._locked_ip is None:
            return True
        return ip == self._locked_ip

    def release(self) -> None:
        old = self._locked_ip
        self._locked_ip = None
        log.info("IP lock released (was %s)", old)

    @property
    def locked_ip(self) -> str | None:
        return self._locked_ip
