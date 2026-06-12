"""
TurboShare — Cleanup utilities.

Deletes orphaned .turbotemp files left over from crashed transfers.
Called at app launch and on transfer cancellation.
"""

import logging
from pathlib import Path

from src.core.config import TEMP_EXT

log = logging.getLogger(__name__)


def cleanup_turbotemp(*directories: Path) -> int:
    """Delete every ``*.turbotemp`` file in the given directories.

    Returns the number of files removed.
    """
    removed = 0
    for directory in directories:
        if not directory.is_dir():
            continue
        for tmp_file in directory.rglob(f"*{TEMP_EXT}"):
            try:
                tmp_file.unlink()
                log.info("Cleaned up leftover temp file: %s", tmp_file)
                removed += 1
            except OSError as exc:
                log.warning("Failed to delete %s: %s", tmp_file, exc)
    return removed
