"""
TurboShare — Log View Page.

Displays the full plain-text contents of a selected log file.
Provides a button to copy the logs to the clipboard.
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QApplication,
)

from src.ui.theme import Colors


class LogViewPage(QWidget):
    """Displays plain-text transaction logs with copy-to-clipboard functionality."""

    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_path = None
        self._parent_window = None

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
        
        self.copy_btn = QPushButton("📋  Copy Logs")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px; font-weight: bold;
                min-height: 15px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_PRIMARY};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        self.copy_btn.clicked.connect(self._copy_logs)
        header_layout.addWidget(self.copy_btn)
        
        layout.addLayout(header_layout)

        # Title
        self.title_label = QLabel("Log Details")
        self.title_label.setStyleSheet(f"""
            font-size: 22px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(self.title_label)

        # Text View viewport
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.text_edit.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                color: #C0C0C8;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 12px;
                padding: 16px;
            }}
        """)
        layout.addWidget(self.text_edit, 1)

    def load_log_file(self, file_path: str, parent_window=None) -> None:
        """Load text contents from the log file path and reference parent for alerts."""
        self._log_path = Path(file_path)
        self._parent_window = parent_window

        self.title_label.setText(self._log_path.name.replace(".txt", ""))

        if self._log_path.is_file():
            try:
                with open(self._log_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_edit.setPlainText(content)
            except Exception as e:
                self.text_edit.setPlainText(f"Error reading log file: {e}")
        else:
            self.text_edit.setPlainText("Log file not found.")

    def _copy_logs(self) -> None:
        """Copy the current viewport plain-text to the clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            # Notify the user using the parent MainWindow's toast notification
            if self._parent_window and hasattr(self._parent_window, "show_toast"):
                self._parent_window.show_toast("Logs copied to clipboard!")
