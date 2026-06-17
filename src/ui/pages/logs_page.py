"""
TurboShare — Logs Page.

Lists all past session logs stored in ~/.turboshare_logs/ in descending order.
"""

import datetime
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea,
)

from src.ui.theme import Colors
from src.utils.session_logger import LOG_DIR


class LogsPage(QWidget):
    """Lists past transaction log files for the user to review."""

    back_clicked = Signal()
    log_selected = Signal(str)  # absolute path of the selected log file

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        back_btn = QPushButton("←  Back")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px; font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Title
        title_label = QLabel("📋 Session Logs")
        title_label.setStyleSheet(f"""
            font-size: 24px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Select a previous transfer session log below to view full details.")
        desc_label.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(desc_label)

        # Scroll Area for Logs
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

    def refresh_logs_list(self) -> None:
        """Scan the logs directory, clear previous widgets, and populate newest first."""
        # Clear previous layout widgets
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Check if logs directory exists
        if not LOG_DIR.is_dir():
            self._show_empty_label()
            return

        # Find all log files: LOGS_YYYYMMDD_HHMMSS.txt
        log_files = sorted(
            [f for f in LOG_DIR.glob("LOGS_*.txt") if f.is_file()],
            key=lambda x: x.name,
            reverse=True,
        )

        if not log_files:
            self._show_empty_label()
            return

        # Create interactive listing
        for lf in log_files:
            btn = QPushButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Format filename to a friendly date-time: LOGS_20260617_230327.txt
            friendly_name = self._parse_friendly_name(lf.name)

            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(16, 12, 16, 12)
            
            title = QLabel(friendly_name)
            title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Colors.TEXT_PRIMARY}; background: transparent;")
            
            fname = QLabel(lf.name)
            fname.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_MUTED}; background: transparent; font-family: monospace;")
            
            btn_layout.addWidget(title)
            btn_layout.addStretch()
            btn_layout.addWidget(fname)

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_SECONDARY};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 12px;
                    text-align: left;
                    min-height: 45px;
                }}
                QPushButton:hover {{
                    border-color: {Colors.ACCENT_PRIMARY};
                    background-color: {Colors.BG_HOVER};
                }}
            """)
            
            # Use a helper to avoid scoping index issues inside lambdas
            btn.clicked.connect(self._create_click_handler(str(lf)))
            self.scroll_layout.addWidget(btn)

    def _create_click_handler(self, file_path: str):
        return lambda: self.log_selected.emit(file_path)

    def _show_empty_label(self) -> None:
        empty = QLabel("No logs recorded yet.")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_MUTED}; padding: 40px;")
        self.scroll_layout.addWidget(empty)

    def _parse_friendly_name(self, filename: str) -> str:
        """Parse friendly log title from filename stamp: LOGS_20260617_230327.txt"""
        # Strip extension and "LOGS_" prefix
        base = filename.replace(".txt", "").replace("LOGS_", "")
        parts = base.split("_")
        if len(parts) == 2:
            date_str, time_str = parts[0], parts[1]
            try:
                dt = datetime.datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                return dt.strftime("Log - %d %b %Y, %H:%M:%S")
            except Exception:
                pass
        return filename.replace(".txt", "")
