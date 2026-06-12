"""
TurboShare — Platform-specific utility helpers.

Currently Windows 11+ only.  Provides OS-level helpers for file
pre-allocation, default directories, and system info.
"""

import os
import subprocess
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def get_downloads_folder() -> Path:
    """Return the current user's Downloads folder."""
    return Path.home() / "Downloads"


def open_folder_in_explorer(path: Path) -> None:
    """Open a folder in Windows Explorer."""
    try:
        os.startfile(str(path))
    except Exception as exc:
        log.warning("Could not open folder %s: %s", path, exc)


def get_system_info() -> dict:
    """Return basic system information for diagnostics."""
    import platform
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
