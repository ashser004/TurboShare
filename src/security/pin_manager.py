"""
TurboShare — PIN generation, verification, rate-limiting, and expiry.

The 6-digit PIN is shown on the sender's screen and must be entered on
the mobile browser.  We enforce:
  • max 3 wrong attempts (then session is killed)
  • 2-second cooldown between attempts per IP
  • 5-minute inactivity timeout (resets on each attempt)
"""

import hmac
import time
import secrets
import logging

from src.core.config import (
    PIN_LENGTH,
    MAX_PIN_ATTEMPTS,
    PIN_RATE_LIMIT_SECONDS,
    PIN_EXPIRY_SECONDS,
)

log = logging.getLogger(__name__)


class PinManager:
    """Manages a single session PIN lifecycle."""

    def __init__(self) -> None:
        self.pin: str = self._generate()
        self._attempts: dict[str, list[float]] = {}  # ip → list of timestamps
        self._total_failures: int = 0
        self._last_activity: float = time.monotonic()

    # ── Generation ──────────────────────────────────────────────────

    @staticmethod
    def _generate() -> str:
        num = secrets.randbelow(10 ** PIN_LENGTH - 10 ** (PIN_LENGTH - 1))
        num += 10 ** (PIN_LENGTH - 1)
        return str(num)

    # ── Verification ────────────────────────────────────────────────

    def verify(self, ip: str, provided_pin: str) -> str:
        """Check the supplied PIN.

        Returns one of:
          ``"ok"``            — correct
          ``"wrong"``         — incorrect, attempts remaining
          ``"rate_limited"``  — too fast, try again later
          ``"max_attempts"``  — 3 failures, session must be killed
          ``"expired"``       — PIN has expired due to inactivity
        """
        now = time.monotonic()

        # Expiry check
        if now - self._last_activity > PIN_EXPIRY_SECONDS:
            log.warning("PIN expired (inactive for >%ds)", PIN_EXPIRY_SECONDS)
            return "expired"

        self._last_activity = now

        # Rate-limit check
        ip_attempts = self._attempts.setdefault(ip, [])
        if ip_attempts:
            elapsed = now - ip_attempts[-1]
            if elapsed < PIN_RATE_LIMIT_SECONDS:
                log.warning("Rate-limited PIN attempt from %s (%.1fs ago)", ip, elapsed)
                return "rate_limited"

        ip_attempts.append(now)

        # PIN comparison (constant-time)
        if hmac.compare_digest(provided_pin.encode(), self.pin.encode()):
            log.info("PIN verified successfully from %s", ip)
            return "ok"

        # Wrong PIN
        self._total_failures += 1
        remaining = MAX_PIN_ATTEMPTS - self._total_failures
        log.warning(
            "Wrong PIN from %s  (total failures=%d, remaining=%d)",
            ip, self._total_failures, remaining,
        )

        if self._total_failures >= MAX_PIN_ATTEMPTS:
            return "max_attempts"

        return "wrong"

    # ── Queries ─────────────────────────────────────────────────────

    @property
    def is_expired(self) -> bool:
        return (time.monotonic() - self._last_activity) > PIN_EXPIRY_SECONDS

    @property
    def failures(self) -> int:
        return self._total_failures
