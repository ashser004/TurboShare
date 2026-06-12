"""
TurboShare — Home page.

Shows the TurboShare logo with two large buttons: Send and Receive.
Includes the info (ℹ️) button for firewall help and version in the corner.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem,
    QSizePolicy,
)

from src.core.config import APP_VERSION, LOGO_PATH
from src.ui.theme import Colors
from src.ui.widgets.info_dialog import InfoButton


class HomePage(QWidget):
    """Home page with Send and Receive buttons."""

    send_clicked = Signal()
    receive_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)

        # ── Top bar: info button ────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        info_btn = InfoButton()
        top_bar.addWidget(info_btn)
        layout.addLayout(top_bar)

        layout.addStretch(2)

        # ── Logo ────────────────────────────────────────────────────
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")
        if LOGO_PATH.is_file():
            pixmap = QPixmap(str(LOGO_PATH))
            pixmap = pixmap.scaled(
                120, 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("⚡")
            logo_label.setStyleSheet(
                f"font-size: 72px; background: transparent; color: {Colors.ACCENT_PRIMARY};"
            )
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(12)

        # ── Title ───────────────────────────────────────────────────
        title = QLabel("TurboShare")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 36px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY}; background: transparent;
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Fast • Secure • Local")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: 14px; color: {Colors.TEXT_SECONDARY};
            background: transparent; letter-spacing: 4px;
        """)
        layout.addWidget(subtitle)

        layout.addStretch(2)

        # ── Buttons ─────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        send_btn = QPushButton("📤  Send")
        send_btn.setProperty("class", "big")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 16px;
                font-size: 20px; font-weight: bold;
                padding: 28px 48px; min-width: 200px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_PRIMARY};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        send_btn.clicked.connect(self.send_clicked.emit)
        btn_layout.addWidget(send_btn)

        recv_btn = QPushButton("📥  Receive")
        recv_btn.setProperty("class", "big")
        recv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        recv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 16px;
                font-size: 20px; font-weight: bold;
                padding: 28px 48px; min-width: 200px;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_SECONDARY};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        recv_btn.clicked.connect(self.receive_clicked.emit)
        btn_layout.addWidget(recv_btn)

        layout.addLayout(btn_layout)

        layout.addStretch(3)

        # ── Version footer ──────────────────────────────────────────
        version = QLabel(f"v{APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"""
            font-size: 11px; color: {Colors.TEXT_MUTED};
            background: transparent;
        """)
        layout.addWidget(version)
