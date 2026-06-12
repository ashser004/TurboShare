"""
TurboShare — Application entry point.

Initialises PySide6 with the qasync event loop bridge so that
both the Qt GUI and the aiohttp server share a single event loop.
"""

import sys
import asyncio
import logging

# Configure logging before any other imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)-28s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("turboshare")

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from src.ui.theme import load_fonts, get_stylesheet
from src.app import MainWindow


def main() -> None:
    """Launch the TurboShare desktop application."""
    # ── Qt Application ──────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("TurboShare")
    app.setOrganizationName("TurboShare")

    # Load custom fonts and apply global stylesheet
    load_fonts()
    app.setStyleSheet(get_stylesheet())

    # ── qasync event loop ───────────────────────────────────────────
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # ── Main window ─────────────────────────────────────────────────
    window = MainWindow()
    window.show()

    # ── Run ─────────────────────────────────────────────────────────
    with loop:
        log.info("TurboShare started")
        loop.run_forever()


if __name__ == "__main__":
    main()
