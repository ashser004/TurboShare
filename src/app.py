"""
TurboShare — Main window and page orchestrator.

The MainWindow manages a QStackedWidget containing all pages and
coordinates between the UI, session, server, and transfer engine.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import Qt, Slot, QPropertyAnimation, QTimer, QRect, QByteArray
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QFileDialog, QWidget,
    QGraphicsOpacityEffect, QLabel, QHBoxLayout, QVBoxLayout, QFrame,
    QPushButton,
)

from src.core.config import APP_NAME, APP_VERSION, MAX_TRANSFER_SIZE, LOGO_PATH
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
from src.ui.pages.about_page import AboutPage
from src.ui.pages.security_page import SecurityPage
from src.ui.pages.logs_page import LogsPage
from src.ui.pages.log_view_page import LogViewPage
from src.utils.session_logger import SessionLoggingManager
from src.utils.formatters import format_size
from src.utils.platform_utils import open_folder_in_explorer

log = logging.getLogger(__name__)

# Page indices in the QStackedWidget
PAGE_HOME = 0
PAGE_SEND_PREVIEW = 1
PAGE_RECEIVE_WAITING = 2
PAGE_TRANSFER = 3
PAGE_DONE = 4
PAGE_ABOUT = 5
PAGE_SECURITY = 6
PAGE_LOGS = 7
PAGE_LOG_VIEW = 8


class MainWindow(QMainWindow):
    """Application main window with stacked pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        if LOGO_PATH.is_file():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        self.setAcceptDrops(True)

        # ── Core objects ────────────────────────────────────────────
        self.session = Session()
        self.engine = TransferEngine()
        self.server = TurboShareServer(self.session, self.engine)
        self.log_manager = SessionLoggingManager()

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
        self._about = AboutPage()
        self._security = SecurityPage(self.session)
        self._logs = LogsPage()
        self._log_view = LogViewPage()

        self._stack.addWidget(self._home)            # 0
        self._stack.addWidget(self._send_preview)     # 1
        self._stack.addWidget(self._receive_waiting)  # 2
        self._stack.addWidget(self._transfer)         # 3
        self._stack.addWidget(self._done)             # 4
        self._stack.addWidget(self._about)            # 5
        self._stack.addWidget(self._security)         # 6
        self._stack.addWidget(self._logs)             # 7
        self._stack.addWidget(self._log_view)         # 8

        # ── Navigation Drawer ───────────────────────────────────────
        self._drawer = NavDrawer(self, on_navigate=self._navigate_to)

        # ── Connect signals ─────────────────────────────────────────
        self._connect_home_signals()
        self._connect_send_preview_signals()
        self._connect_receive_waiting_signals()
        self._connect_transfer_signals()
        self._connect_done_signals()
        self._connect_about_signals()
        self._connect_security_signals()
        self._connect_logs_signals()
        self._connect_log_view_signals()
        self._connect_session_signals()
        self._connect_engine_signals()

        # ── Startup cleanup ─────────────────────────────────────────
        from src.core.config import DEFAULT_SAVE_DIR
        cleanup_turbotemp(DEFAULT_SAVE_DIR)

    # ── Signal wiring ───────────────────────────────────────────────

    def _connect_home_signals(self) -> None:
        self._home.send_clicked.connect(self._on_send_clicked)
        self._home.receive_clicked.connect(self._on_receive_clicked)
        self._home.hamburger_clicked.connect(self._drawer.open_drawer)

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

    def _connect_about_signals(self) -> None:
        self._about.back_clicked.connect(self._go_home)

    def _connect_security_signals(self) -> None:
        self._security.back_clicked.connect(self._go_home)

    def _connect_logs_signals(self) -> None:
        self._logs.back_clicked.connect(self._go_home)
        self._logs.log_selected.connect(self._on_log_selected)

    def _connect_log_view_signals(self) -> None:
        self._log_view.back_clicked.connect(lambda: self._navigate_to(PAGE_LOGS))

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
        
        if page_index == PAGE_LOGS:
            self._logs.refresh_logs_list()

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
        self._start_send_session(paths)

    def _start_send_session(self, paths: list[str]) -> None:
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
        self.log_manager.start_session_logging()

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
            self.session.safe_transfer,
        )
        self._navigate_to(PAGE_SEND_PREVIEW)

        # Start server
        asyncio.ensure_future(self.server.start())

    # ── Receive flow ────────────────────────────────────────────────

    @Slot()
    def _on_receive_clicked(self) -> None:
        self.session.create(SessionMode.RECEIVE)
        self.log_manager.start_session_logging()
        self._receive_waiting.setup(
            self.session.session_url,
            self.session.pin,
            self.session.safe_transfer,
        )
        self._navigate_to(PAGE_RECEIVE_WAITING)
        asyncio.ensure_future(self.server.start())

    # ── Handshake ───────────────────────────────────────────────────

    @Slot(object)
    def _on_receiver_connected(self, device_info: DeviceInfo) -> None:
        """Stage 1 complete — show device info on the appropriate page."""
        if not self.session.safe_transfer:
            return

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
                self.session.session_url, self.session.pin, self.session.safe_transfer,
            )
        else:
            self._receive_waiting.refresh_session(
                self.session.session_url, self.session.pin, self.session.safe_transfer,
            )

    # ── Transfer progress ───────────────────────────────────────────

    @Slot(dict)
    def _on_progress_updated(self, data: dict) -> None:
        self._transfer.update_progress(data)

    @Slot(dict)
    def _on_transfer_completed(self, stats: dict) -> None:
        from src.core.session import SessionState
        self.session.set_state(SessionState.COMPLETED)
        is_receive = self.session.mode == SessionMode.RECEIVE
        self._done.show_stats(stats, is_receive=is_receive)
        self._navigate_to(PAGE_DONE)
        self.log_manager.stop_session_logging()
        asyncio.ensure_future(self._stop_server_delayed())

    @Slot(str)
    def _on_error(self, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Error", message)

    # ── Cancellation ────────────────────────────────────────────────

    @Slot()
    def _on_cancel_session(self) -> None:
        self.session.invalidate()
        self.engine.cancel()
        self.log_manager.stop_session_logging()
        asyncio.ensure_future(self._stop_server())
        self._navigate_to(PAGE_HOME)

    @Slot()
    def _on_cancel_transfer(self) -> None:
        self.engine.cancel()
        self.session.invalidate()
        self.log_manager.stop_session_logging()
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
        self.engine.prepare_send(self.session.files)

    @Slot(str)
    def _on_save_dir_changed(self, folder: str) -> None:
        self.session.save_dir = Path(folder)

    # ── Helpers ─────────────────────────────────────────────────────

    @Slot()
    def _on_open_folder(self) -> None:
        open_folder_in_explorer(self.session.save_dir)

    @Slot(str)
    def _on_log_selected(self, file_path: str) -> None:
        self._log_view.load_log_file(file_path, self)
        self._navigate_to(PAGE_LOG_VIEW)

    async def _stop_server(self) -> None:
        if self.server.is_running:
            await self.server.stop()

    async def _stop_server_delayed(self) -> None:
        await asyncio.sleep(1.0)
        await self._stop_server()

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
        self.log_manager.stop_session_logging()
        try:
            await self._stop_server()
        except Exception as e:
            log.error("Error stopping server during shutdown: %s", e)
        log.info("Graceful shutdown complete. Quitting application.")
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    # ── Drag and Drop Overrides ─────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if self._stack.currentIndex() == PAGE_HOME and event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._home.show_drag_overlay(True)

    def dragMoveEvent(self, event) -> None:
        if self._stack.currentIndex() == PAGE_HOME and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._home.show_drag_overlay(False)

    def dropEvent(self, event) -> None:
        self._home.show_drag_overlay(False)
        if self._stack.currentIndex() == PAGE_HOME and event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            paths = [url.toLocalFile() for url in urls if url.isLocalFile()]

            files_paths = []
            has_folders = False
            for p in paths:
                p_path = Path(p)
                if p_path.is_file():
                    files_paths.append(p)
                elif p_path.is_dir():
                    has_folders = True

            if has_folders:
                self.show_toast("Folder sharing is not supported.")

            if files_paths:
                self._start_send_session(files_paths)
                event.acceptProposedAction()

    def show_toast(self, message: str) -> None:
        """Show a temporary floating toast notification in the center."""
        ToastNotification(message, self)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_drawer"):
            self._drawer.setGeometry(self.rect())
            self._drawer.update_geometry()


class ToastNotification(QLabel):
    """Self-dismissing floating toast notification in the center of the parent."""

    def __init__(self, message: str, parent: QWidget) -> None:
        super().__init__(message, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"""
            background-color: rgba(25, 25, 30, 0.92);
            color: {Colors.ACCENT_DANGER};
            border: 1.5px solid {Colors.BORDER_LIGHT};
            border-radius: 10px;
            font-size: 13px; font-weight: bold;
            padding: 12px 24px;
        """)

        # Set graphics effect for opacity fading
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        # Animation
        self.anim = QPropertyAnimation(self.opacity_effect, QByteArray(b"opacity"))
        self.anim.setDuration(800)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close_and_delete)

        # Timer to start fade out after 2.2 seconds (total duration ~3s)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.anim.start)
        self.timer.start(2200)

        self.adjustSize()
        self.center_position()
        self.show()

    def center_position(self) -> None:
        parent = self.parentWidget()
        if parent:
            p_rect = parent.rect()
            x = (p_rect.width() - self.width()) // 2
            y = (p_rect.height() - self.height()) // 2
            self.move(x, y)

    def close_and_delete(self) -> None:
        self.hide()
        self.deleteLater()


class NavDrawer(QWidget):
    """Sliding navigation drawer overlay for the main window."""

    def __init__(self, parent: MainWindow, on_navigate) -> None:
        super().__init__(parent)
        self.on_navigate = on_navigate
        self.hide()

        # Dim background
        self.dim_bg = QFrame(self)
        self.dim_bg.setStyleSheet("background-color: rgba(10, 10, 15, 0.65);")
        self.dim_bg.mousePressEvent = lambda event: self.close_drawer()

        # Menu Panel
        self.panel = QFrame(self)
        self.panel.setObjectName("nav_panel")
        self.panel.setStyleSheet(f"""
            QFrame#nav_panel {{
                background-color: {Colors.BG_SECONDARY};
                border-right: 1px solid {Colors.BORDER};
            }}
        """)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(16, 24, 16, 24)
        panel_layout.setSpacing(12)

        # Header / Close Button
        brand_layout = QHBoxLayout()
        self.brand_label = QLabel("⚡ TurboShare")
        self.brand_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {Colors.ACCENT_PRIMARY};
            background: transparent;
        """)
        brand_layout.addWidget(self.brand_label)
        brand_layout.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_SECONDARY};
                font-size: 16px;
                font-weight: bold;
                padding: 4px;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_DANGER};
            }}
        """)
        self.close_btn.clicked.connect(self.close_drawer)
        brand_layout.addWidget(self.close_btn)
        panel_layout.addLayout(brand_layout)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {Colors.BORDER};")
        panel_layout.addWidget(sep)
        panel_layout.addSpacing(10)

        # Helper for modern buttons
        def create_menu_btn(text: str, target_page: int) -> QPushButton:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Colors.TEXT_PRIMARY};
                    border: 1px solid transparent;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {Colors.BG_HOVER};
                    border-color: {Colors.BORDER};
                    color: {Colors.ACCENT_PRIMARY};
                }}
            """)
            btn.clicked.connect(lambda: self._handle_navigation(target_page))
            return btn

        # Menu options
        self.security_btn = create_menu_btn("🔒   Security", PAGE_SECURITY)
        self.logs_btn = create_menu_btn("📋   Session Logs", PAGE_LOGS)
        self.about_btn = create_menu_btn("ℹ️   About", PAGE_ABOUT)

        panel_layout.addWidget(self.security_btn)
        panel_layout.addWidget(self.logs_btn)
        panel_layout.addWidget(self.about_btn)

        panel_layout.addStretch()

        # Bottom version info
        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 11px; background-color: transparent;")
        panel_layout.addWidget(self.version_label)

        # Setup slide animation
        self.anim = QPropertyAnimation(self.panel, QByteArray(b"pos"))
        self.anim.setDuration(250)

    def _handle_navigation(self, page_index: int) -> None:
        self.close_drawer()
        self.on_navigate(page_index)

    def open_drawer(self) -> None:
        self.show()
        self.raise_()
        self.dim_bg.setGeometry(self.rect())

        w = int(self.width() * 0.22)
        w = max(200, min(w, 280))
        self.panel.setGeometry(-w, 0, w, self.height())

        self.anim.stop()
        self.anim.setStartValue(self.panel.pos())
        self.anim.setEndValue(QRect(0, 0, w, self.height()).topLeft())
        self.anim.start()

    def close_drawer(self) -> None:
        w = self.panel.width()
        self.anim.stop()
        self.anim.setStartValue(self.panel.pos())
        self.anim.setEndValue(QRect(-w, 0, w, self.height()).topLeft())

        def on_finished():
            try:
                self.anim.finished.disconnect(on_finished)
            except RuntimeError:
                pass
            self.hide()

        self.anim.finished.connect(on_finished)
        self.anim.start()

    def update_geometry(self) -> None:
        self.dim_bg.setGeometry(self.rect())
        if self.isVisible():
            w = int(self.width() * 0.22)
            w = max(200, min(w, 280))
            self.panel.setGeometry(0, 0, w, self.height())

