"""
TurboShare — Transfer Progress page.

Shows current file name, per-file progress bar, speed, ETA, overall
progress, and a scrollable file status list.  Used for both send and
receive modes.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox,
)

from src.ui.theme import Colors
from src.ui.widgets.progress_bar import AnimatedProgressBar
from src.ui.widgets.file_list import FileListWidget
from src.ui.widgets.speed_display import SpeedDisplay
from src.ui.animations import LottieWidget
from src.utils.formatters import format_size, format_eta


class TransferPage(QWidget):
    """Transfer progress page with real-time stats."""

    cancel_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Header: current file ────────────────────────────────────
        self._current_file_label = QLabel("Preparing transfer…")
        self._current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_file_label.setStyleSheet(f"""
            font-size: 18px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY}; background: transparent;
        """)
        layout.addWidget(self._current_file_label)

        # ── Per-file progress ───────────────────────────────────────
        self._file_progress = AnimatedProgressBar(height=18)
        layout.addWidget(self._file_progress)

        # ── Speed + ETA row ─────────────────────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(24)

        self._speed_display = SpeedDisplay()
        stats_layout.addWidget(self._speed_display, alignment=Qt.AlignmentFlag.AlignCenter)

        self._eta_label = QLabel("estimating…")
        self._eta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._eta_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.TEXT_SECONDARY};
            background: transparent;
        """)
        stats_layout.addWidget(self._eta_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(stats_layout)

        # ── Lottie transfer animation ───────────────────────────────
        self._lottie = LottieWidget("transferring", width=140, height=80)
        layout.addWidget(self._lottie, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Overall progress ────────────────────────────────────────
        overall_card = QFrame()
        overall_card.setObjectName("overall_card_frame")
        overall_card.setStyleSheet(f"""
            QFrame#overall_card_frame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        overall_layout = QVBoxLayout(overall_card)
        overall_layout.setContentsMargins(16, 12, 16, 12)
        overall_layout.setSpacing(8)

        overall_header = QHBoxLayout()
        overall_title = QLabel("Overall Progress")
        overall_title.setStyleSheet(f"""
            font-size: 13px; color: {Colors.TEXT_SECONDARY};
            font-weight: bold; background: transparent;
        """)
        overall_header.addWidget(overall_title)

        self._files_count_label = QLabel("0 of 0 files")
        self._files_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._files_count_label.setStyleSheet(f"""
            font-size: 13px; color: {Colors.ACCENT_PRIMARY};
            font-weight: bold; background: transparent;
        """)
        overall_header.addWidget(self._files_count_label)
        overall_layout.addLayout(overall_header)

        self._overall_progress = AnimatedProgressBar(height=12)
        overall_layout.addWidget(self._overall_progress)

        self._transferred_label = QLabel("")
        self._transferred_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._transferred_label.setStyleSheet(f"""
            font-size: 11px; color: {Colors.TEXT_MUTED};
            background: transparent;
        """)
        overall_layout.addWidget(self._transferred_label)

        layout.addWidget(overall_card)

        # ── File status list ────────────────────────────────────────
        self._file_list = FileListWidget(removable=False)
        self._file_list.setMaximumHeight(200)
        layout.addWidget(self._file_list)

        # ── Cancel button ───────────────────────────────────────────
        self._cancel_btn = QPushButton("✕ Cancel Transfer")
        self._cancel_btn.setProperty("class", "danger")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Public API ──────────────────────────────────────────────────

    def setup(self, files: list[dict]) -> None:
        """Initialise the page with the file list."""
        self._file_list.clear_files()
        for f in files:
            self._file_list.add_file(f["id"], f["name"], f["size"])
            self._file_list.update_status(f["id"], "waiting")

        self._file_progress.set_value_instant(0)
        self._overall_progress.set_value_instant(0)
        self._current_file_label.setText("Starting transfer…")
        self._speed_display.set_speed(0)
        self._eta_label.setText("estimating…")
        total_files = len(files)
        self._files_count_label.setText(f"0 of {total_files} files")
        self._lottie.load_animation("transferring")

    def update_progress(self, data: dict) -> None:
        """Update all progress elements from a progress snapshot."""
        # Current file
        current = data.get("current_file", "")
        if current:
            self._current_file_label.setText(f"📄 {current}")

        # Per-file progress
        self._file_progress.set_value(data.get("current_file_progress", 0))

        # Speed
        self._speed_display.set_speed(data.get("speed_mbps", 0))

        # ETA
        eta = data.get("eta_seconds", -1)
        self._eta_label.setText(format_eta(eta))

        # Overall
        self._overall_progress.set_value(data.get("overall_progress", 0))

        # Transferred bytes
        transferred = data.get("bytes_transferred", 0)
        total = data.get("total_bytes", 1)
        self._transferred_label.setText(
            f"{format_size(transferred)} / {format_size(total)}"
        )

        # File statuses
        files = data.get("files", [])
        done_count = 0
        for f in files:
            self._file_list.update_status(f["id"], f["status"])
            if f["status"] == "done":
                done_count += 1

        self._files_count_label.setText(f"{done_count} of {len(files)} files")

    def _on_cancel(self) -> None:
        reply = QMessageBox.question(
            self,
            "Cancel Transfer",
            "Are you sure you want to cancel the transfer?\n"
            "All incomplete files will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cancel_requested.emit()
