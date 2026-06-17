"""
TurboShare — Central session state manager.

A Session encapsulates every piece of state for a single transfer
interaction: port, token, PIN, SSL context, file list, connected
device info, transfer progress, etc.

It emits PySide6 Signals so the UI can react to state changes without
polling or touching the session from the wrong thread.
"""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.core.config import (
    DEFAULT_SAVE_DIR,
    build_session_url,
)
from src.core.preferences import load_safe_transfer_setting
from src.core.network import get_local_ip, find_available_port
from src.security.token_manager import generate_token
from src.security.pin_manager import PinManager

log = logging.getLogger(__name__)


# ── Session mode & state enums ──────────────────────────────────────

class SessionMode(enum.Enum):
    SEND = "send"
    RECEIVE = "receive"


class SessionState(enum.Enum):
    IDLE = "idle"
    WAITING_FOR_RECEIVER = "waiting_for_receiver"
    RECEIVER_CONFIRMED = "receiver_confirmed"      # Stage 1 done
    SENDER_CONFIRMED = "sender_confirmed"            # Stage 2 done
    HANDSHAKE_COMPLETE = "handshake_complete"         # Stage 3 done
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


# ── File entry ──────────────────────────────────────────────────────

@dataclass
class FileEntry:
    """Metadata for a single file in the transfer session."""
    id: int
    name: str
    path: Path
    size: int
    status: str = "waiting"      # waiting | transferring | done | error
    progress: float = 0.0        # 0.0 – 1.0


# ── Receiver device info ────────────────────────────────────────────

@dataclass
class DeviceInfo:
    """Browser / OS info parsed from the receiver's User-Agent."""
    browser: str = "Unknown"
    os: str = "Unknown"
    ip: str = "Unknown"


# ── Session signals ─────────────────────────────────────────────────

class SessionSignals(QObject):
    """Thread-safe signals emitted by the session."""
    state_changed = Signal(str)             # SessionState.value
    receiver_connected = Signal(object)     # DeviceInfo
    progress_updated = Signal(dict)         # {current_file, progress, speed, ...}
    file_completed = Signal(int)            # file id
    transfer_completed = Signal(dict)       # summary stats
    error_occurred = Signal(str)            # human-readable message
    session_regenerated = Signal()          # QR / PIN / URL refreshed


# ── Session ─────────────────────────────────────────────────────────

class Session:
    """Full state container for one transfer session."""

    def __init__(self) -> None:
        self.signals = SessionSignals()

        # Will be populated by create()
        self.mode: SessionMode = SessionMode.SEND
        self.state: SessionState = SessionState.IDLE

        self.local_ip: str = ""
        self.port: int = 0
        self.token: str = ""
        self.session_url: str = ""

        self.pin_manager: PinManager | None = None

        self.files: list[FileEntry] = []
        self.save_dir: Path = DEFAULT_SAVE_DIR
        self.safe_transfer: bool = load_safe_transfer_setting()

        self.locked_ip: str | None = None
        self.device_info: DeviceInfo | None = None

        # Transfer stats (filled after completion)
        self.total_bytes_transferred: int = 0
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    # ── Lifecycle ───────────────────────────────────────────────────

    def create(
        self,
        mode: SessionMode,
        files: list[dict] | None = None,
        save_dir: Path | None = None,
    ) -> None:
        """Initialise (or re-initialise) the session for a new transfer.

        ``files`` is a list of ``{"path": Path, "name": str, "size": int}``
        dicts — required for SEND mode, optional for RECEIVE (the phone
        will supply files via upload).
        """
        self.mode = mode
        self.state = SessionState.WAITING_FOR_RECEIVER

        self.local_ip = get_local_ip()
        self.port = find_available_port()
        self.token = generate_token()
        self.session_url = build_session_url(self.local_ip, self.port, self.token)

        self.pin_manager = PinManager()

        self.locked_ip = None
        self.device_info = None
        self.total_bytes_transferred = 0
        self.start_time = 0.0
        self.end_time = 0.0

        if save_dir is not None:
            self.save_dir = save_dir

        # Build file entries
        self.files = []
        if files:
            for idx, f in enumerate(files):
                self.files.append(FileEntry(
                    id=idx,
                    name=f["name"],
                    path=Path(f["path"]),
                    size=f["size"],
                ))

        self.signals.state_changed.emit(self.state.value)
        log.info(
            "Session created  mode=%s  ip=%s  port=%d  url=%s",
            mode.value, self.local_ip, self.port, self.session_url,
        )

    def regenerate(self) -> None:
        """Kill the current session and create fresh credentials.

        Called after 3 wrong PIN attempts or manual rejection.
        """
        old_mode = self.mode
        old_files_data = [
            {"path": str(f.path), "name": f.name, "size": f.size}
            for f in self.files
        ]
        self.create(old_mode, files=old_files_data, save_dir=self.save_dir)
        self.signals.session_regenerated.emit()
        log.info("Session regenerated (port=%d, token=%s…)", self.port, self.token[:4])

    def set_state(self, new_state: SessionState) -> None:
        self.state = new_state
        self.signals.state_changed.emit(new_state.value)

    def lock_to_ip(self, ip: str) -> None:
        self.locked_ip = ip
        log.info("Session locked to IP %s", ip)

    def is_ip_allowed(self, ip: str) -> bool:
        if self.locked_ip is None:
            return True
        return ip == self.locked_ip

    def invalidate(self) -> None:
        """Mark session as done / cancelled — clears sensitive state."""
        self.state = SessionState.CANCELLED
        self.token = ""
        if self.pin_manager:
            self.pin_manager = None
        self.locked_ip = None
        self.signals.state_changed.emit(self.state.value)

    # ── Convenience ─────────────────────────────────────────────────

    @property
    def pin(self) -> str:
        return self.pin_manager.pin if self.pin_manager else ""

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def files_as_dicts(self) -> list[dict]:
        return [
            {
                "id": f.id,
                "name": f.name,
                "size": f.size,
                "status": f.status,
                "progress": f.progress,
            }
            for f in self.files
        ]
