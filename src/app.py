"""
TurboShare — Main window and page orchestrator.

The MainWindow manages a QStackedWidget containing all pages and
coordinates between the UI, session, server, and transfer engine.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QFileDialog, QWidget,
)

from src.core.config import APP_NAME, MAX_TRANSFER_SIZE
from src.core.session import Session, SessionMode, SessionState, DeviceInfo
from src.core.cleanup import cleanup_turbotemp
from src.transfer.engine import TransferEngine
from src.server.server import TurboShareServer
from src.ui.theme import Colors
from src.ui.transitions import fade_transition
from src.ui.pages.home_page import HomePage
from src.ui.pages.send_preview_page import SendPreviewPage
from src.ui.pages.receive_waiting_page import ReceiveWaitingPage
from src.ui.pages.transfer_page import TransferPage
from src.ui.pages.done_page import DonePage
from src.utils.formatters import format_size
from src.utils.platform_utils import open_folder_in_explorer

log = logging.getLogger(__name__)

# Page indices in the QStackedWidget
PAGE_HOME = 0
PAGE_SEND_PREVIEW = 1
PAGE_RECEIVE_WAITING = 2
PAGE_TRANSFER = 3
PAGE_DONE = 4


class MainWindow(QMainWindow):
    """Application main window with stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        # ── Core objects ────────────────────────────────────────────
        self.session = Session()
        self.engine = TransferEngine()
        self.server = TurboShareServer(self.session, self.engine)

        # Keep animation refs alive
        self._current_anim = None

        # ── Pages ───────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home = HomePage()
        self._send_preview = SendPreviewPage()
        self._receive_waiting = ReceiveWaitingPage()
        self._transfer = TransferPage()
        self._done = DonePage()

        self._stack.addWidget(self._home)           # 0
        self._stack.addWidget(self._send_preview)    # 1
        self._stack.addWidget(self._receive_waiting) # 2
        self._stack.addWidget(self._transfer)        # 3
        self._stack.addWidget(self._done)            # 4

        # ── Connect signals ─────────────────────────────────────────
        self._connect_home_signals()
        self._connect_send_preview_signals()
        self._connect_receive_waiting_signals()
        self._connect_transfer_signals()
        self._connect_done_signals()
        self._connect_session_signals()
        self._connect_engine_signals()

        # ── Startup cleanup ─────────────────────────────────────────
        from src.core.config import DEFAULT_SAVE_DIR
        cleanup_turbotemp(DEFAULT_SAVE_DIR)

    # ── Signal wiring ───────────────────────────────────────────────

    def _connect_home_signals(self) -> None:
        self._home.send_clicked.connect(self._on_send_clicked)
        self._home.receive_clicked.connect(self._on_receive_clicked)

    def _connect_send_preview_signals(self) -> None:
        self._send_preview.confirm_clicked.connect(self._on_sender_confirm)
        self._send_preview.reject_clicked.connect(self._on_sender_reject)
        self._send_preview.cancel_clicked.connect(self._on_cancel_session)
        self._send_preview.files_changed.connect(self._on_files_changed)

    def _connect_receive_waiting_signals(self) -> None:
        self._receive_waiting.confirm_clicked.connect(self._on_sender_confirm)
        self._receive_waiting.reject_clicked.connect(self._on_sender_reject)
        self._receive_waiting.cancel_clicked.connect(self._on_cancel_session)
        self._receive_waiting.save_dir_changed.connect(self._on_save_dir_changed)

    def _connect_transfer_signals(self) -> None:
        self._transfer.cancel_requested.connect(self._on_cancel_transfer)

    def _connect_done_signals(self) -> None:
        self._done.send_more_clicked.connect(self._on_send_clicked)
        self._done.go_home_clicked.connect(self._go_home)
        self._done.open_folder_clicked.connect(self._on_open_folder)

    def _connect_session_signals(self) -> None:
        self.session.signals.state_changed.connect(self._on_state_changed)
        self.session.signals.receiver_connected.connect(self._on_receiver_connected)
        self.session.signals.session_regenerated.connect(self._on_session_regenerated)

    def _connect_engine_signals(self) -> None:
        self.engine.signals.progress_updated.connect(self._on_progress_updated)
        self.engine.signals.transfer_completed.connect(self._on_transfer_completed)
        self.engine.signals.error_occurred.connect(self._on_error)

    # ── Page navigation ─────────────────────────────────────────────

    def _navigate_to(self, page_index: int) -> None:
        old_index = self._stack.currentIndex()
        if old_index == page_index:
            return
        old_widget = self._stack.widget(old_index)
        new_widget = self._stack.widget(page_index)
        self._stack.setCurrentIndex(page_index)
        self._current_anim = fade_transition(old_widget, new_widget, duration=300)

    def _go_home(self) -> None:
        asyncio.ensure_future(self._stop_server())
        self._navigate_to(PAGE_HOME)

    # ── Send flow ───────────────────────────────────────────────────

    @Slot()
    def _on_send_clicked(self) -> None:
        from PySide6.QtCore import QStandardPaths
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Send", default_dir, "All Files (*)"
        )
        if not paths:
            return

        # Build file entries
        files_data = []
        for idx, p in enumerate(paths):
            p = Path(p)
            files_data.append({
                "id": idx,
                "name": p.name,
                "path": str(p),
                "size": p.stat().st_size,
            })

        # Check 30 GB cap
        total = sum(f["size"] for f in files_data)
        if total > MAX_TRANSFER_SIZE:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Size Limit",
                f"Total size ({format_size(total)}) exceeds the "
                f"30 GB limit. Please select fewer files.",
            )
            return

        # Create session
        self.session.create(SessionMode.SEND, files=files_data)

        # Prepare transfer engine
        self.engine.prepare_send(self.session.files)

        # Setup send preview page
        files_dicts = [
            {"id": f.id, "name": f.name, "path": str(f.path), "size": f.size}
            for f in self.session.files
        ]
        self._send_preview.setup(
            files_dicts,
            self.session.session_url,
            self.session.pin,
        )
        self._navigate_to(PAGE_SEND_PREVIEW)

        # Start server
        asyncio.ensure_future(self.server.start())

    # ── Receive flow ────────────────────────────────────────────────

    @Slot()
    def _on_receive_clicked(self) -> None:
        self.session.create(SessionMode.RECEIVE)
        self._receive_waiting.setup(
            self.session.session_url,
            self.session.pin,
        )
        self._navigate_to(PAGE_RECEIVE_WAITING)
        asyncio.ensure_future(self.server.start())

    # ── Handshake ───────────────────────────────────────────────────

    @Slot(object)
    def _on_receiver_connected(self, device_info: DeviceInfo) -> None:
        """Stage 1 complete — show device info on the appropriate page."""
        if self.session.mode == SessionMode.SEND:
            self._send_preview.show_receiver_info(
                device_info.browser, device_info.os, device_info.ip
            )
        else:
            self._receive_waiting.show_sender_info(
                device_info.browser, device_info.os, device_info.ip
            )

    @Slot()
    def _on_sender_confirm(self) -> None:
        """Stage 2: User clicks Confirm."""
        from src.core.session import SessionState
        if self.session.state == SessionState.RECEIVER_CONFIRMED:
            self.session.set_state(SessionState.SENDER_CONFIRMED)
            log.info("Sender confirmed receiver directly in memory")

    @Slot()
    def _on_sender_reject(self) -> None:
        """User clicks Reject — regenerate session."""
        log.info("Sender rejected receiver directly in memory — regenerating session")
        self.session.regenerate()

    # ── State changes ───────────────────────────────────────────────

    @Slot(str)
    def _on_state_changed(self, state_value: str) -> None:
        state = SessionState(state_value)

        if state == SessionState.TRANSFERRING:
            # Transition to transfer page
            files_dicts = self.session.files_as_dicts
            self._transfer.setup(files_dicts)
            self._navigate_to(PAGE_TRANSFER)

    @Slot()
    def _on_session_regenerated(self) -> None:
        """QR/PIN/URL refreshed after failed PIN or rejection."""
        asyncio.ensure_future(self.server.restart())

        if self.session.mode == SessionMode.SEND:
            self._send_preview.refresh_session(
                self.session.session_url, self.session.pin,
            )
        else:
            self._receive_waiting.refresh_session(
                self.session.session_url, self.session.pin,
            )

    # ── Transfer progress ───────────────────────────────────────────

    @Slot(dict)
    def _on_progress_updated(self, data: dict) -> None:
        self._transfer.update_progress(data)

    @Slot(dict)
    def _on_transfer_completed(self, stats: dict) -> None:
        is_receive = self.session.mode == SessionMode.RECEIVE
        self._done.show_stats(stats, is_receive=is_receive)
        self._navigate_to(PAGE_DONE)
        asyncio.ensure_future(self._stop_server())

    @Slot(str)
    def _on_error(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)

    # ── Cancellation ────────────────────────────────────────────────

    @Slot()
    def _on_cancel_session(self) -> None:
        self.session.invalidate()
        self.engine.cancel()
        asyncio.ensure_future(self._stop_server())
        self._navigate_to(PAGE_HOME)

    @Slot()
    def _on_cancel_transfer(self) -> None:
        self.engine.cancel()
        self.session.invalidate()
        asyncio.ensure_future(self._stop_server())
        self._navigate_to(PAGE_HOME)

    # ── File changes ────────────────────────────────────────────────

    @Slot(list)
    def _on_files_changed(self, files: list[dict]) -> None:
        # Update session files
        from src.core.session import FileEntry
        self.session.files = [
            FileEntry(id=f["id"], name=f["name"], path=Path(f["path"]), size=f["size"])
            for f in files
        ]

    @Slot(str)
    def _on_save_dir_changed(self, folder: str) -> None:
        self.session.save_dir = Path(folder)

    # ── Helpers ─────────────────────────────────────────────────────

    @Slot()
    def _on_open_folder(self) -> None:
        open_folder_in_explorer(self.session.save_dir)

    async def _stop_server(self) -> None:
        if self.server.is_running:
            await self.server.stop()

    def closeEvent(self, event) -> None:
        """Clean shutdown on window close."""
        # Prevent default close, hide window, and run async cleanup first
        event.ignore()
        self.hide()
        asyncio.create_task(self._shutdown_and_quit())

    async def _shutdown_and_quit(self) -> None:
        log.info("Graceful shutdown started...")
        self.engine.cancel()
        self.session.invalidate()
        try:
            await self._stop_server()
        except Exception as e:
            log.error("Error stopping server during shutdown: %s", e)
        log.info("Graceful shutdown complete. Quitting application.")
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
