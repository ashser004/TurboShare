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

    Only searches the root of the given directories (non-recursive).
    Returns the number of files removed.
    """
    removed = 0
    for directory in directories:
        if not directory.is_dir():
            continue
        try:
            # Flat scan: only iterate over immediate files in the directory
            for path in directory.iterdir():
                if path.is_file() and path.name.endswith(TEMP_EXT):
                    try:
                        path.unlink()
                        log.info("Cleaned up leftover temp file: %s", path)
                        removed += 1
                    except OSError as exc:
                        log.warning("Failed to delete %s: %s", path, exc)
        except OSError as exc:
            log.warning("Failed to list directory %s: %s", directory, exc)
    return removed
