"""
TurboShare — Firewall info dialog.

Shows manual firewall setup instructions when the user clicks the
info (ℹ️) icon.  Styled to match the dark theme.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QWidget,
)
from src.ui.theme import Colors


class InfoDialog(QDialog):
    """Modal dialog with manual firewall setup instructions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firewall Setup Help")
        self.setFixedSize(520, 420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("🛡️  Manual Firewall Setup")
        title.setStyleSheet(f"""
            font-size: 20px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY}; background: transparent;
        """)
        layout.addWidget(title)

        intro = QLabel(
            "If the automatic firewall rule wasn't added during installation, "
            "follow these steps to allow TurboShare through Windows Firewall:"
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        layout.addWidget(intro)

        steps = [
            "1. Open <b>Start Menu</b> and search <b>Windows Defender Firewall</b>",
            "2. Click <b>Advanced Settings</b> (left panel)",
            "3. Click <b>Inbound Rules</b> (left panel)",
            "4. Click <b>New Rule…</b> (right panel)",
            "5. Select <b>Port</b> → Next",
            "6. Select <b>TCP</b>, enter port range: <b>49152-65535</b> → Next",
            "7. Select <b>Allow the connection</b> → Next",
            "8. Check <b>Domain</b>, <b>Private</b>, and <b>Public</b> → Next",
            "9. Name it <b>TurboShare</b> → Finish",
        ]

        for step in steps:
            step_label = QLabel(step)
            step_label.setTextFormat(Qt.TextFormat.RichText)
            step_label.setWordWrap(True)
            step_label.setStyleSheet(
                f"color: {Colors.TEXT_PRIMARY}; font-size: 12px; "
                f"padding: 2px 0; background: transparent;"
            )
            layout.addWidget(step_label)

        layout.addStretch()

        close_btn = QPushButton("Got it")
        close_btn.setProperty("class", "primary")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class InfoButton(QPushButton):
    """Small ℹ️ icon button that opens the InfoDialog."""

    def __init__(self, parent=None):
        super().__init__("ℹ️", parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Firewall setup help")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Colors.BORDER};
                border-radius: 18px;
                font-size: 16px;
                color: {Colors.TEXT_SECONDARY};
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_PRIMARY};
                color: {Colors.ACCENT_PRIMARY};
            }}
        """)
        self.clicked.connect(self._show_dialog)

    def _show_dialog(self):
        dialog = InfoDialog(self.window())
        dialog.exec()
