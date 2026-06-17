"""
TurboShare — About Page.

Displays details about the application, the developer credit,
and a link to the developer's GitHub profile.
"""

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

from src.core.config import APP_VERSION
from src.ui.theme import Colors


class AboutPage(QWidget):
    """About page displaying developer credits and app overview."""

    back_clicked = Signal()

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

        layout.addStretch(1)

        # ── Card Container ──────────────────────────────────────────
        card = QFrame()
        card.setObjectName("about_card")
        card.setStyleSheet(f"""
            QFrame#about_card {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(16)

        # App Title & Version
        title_label = QLabel("⚡ TurboShare")
        title_label.setStyleSheet(f"""
            font-size: 28px; font-weight: bold;
            color: {Colors.ACCENT_PRIMARY};
        """)
        card_layout.addWidget(title_label)

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_SECONDARY};")
        card_layout.addWidget(version_label)

        # Description
        desc_label = QLabel(
            "TurboShare is a high-speed, local peer-to-peer file sharing application.\n"
            "By establishing dynamic client-negotiated chunk transfers and adaptive concurrency control, "
            "it squeezes the maximum bandwidth out of your local network or mobile hotspot safely and reliably."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_PRIMARY}; line-height: 1.6;")
        card_layout.addWidget(desc_label)

        # Divider
        divider = QFrame()
        divider.setStyleSheet(f"background-color: {Colors.BORDER}; max-height: 1px;")
        card_layout.addWidget(divider)

        # Developer Info
        dev_label = QLabel("Developer: <b>Ashmith Babu P S</b>")
        dev_label.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_PRIMARY};")
        card_layout.addWidget(dev_label)

        # Github button
        github_btn = QPushButton("🌐 Check GitHub Profile")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                padding: 12px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {Colors.ACCENT_PRIMARY};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        github_btn.clicked.connect(self._open_github)
        card_layout.addWidget(github_btn)

        layout.addWidget(card)
        layout.addStretch(2)

    def _open_github(self) -> None:
        """Open the developer's GitHub in the default system browser."""
        QDesktopServices.openUrl(QUrl("https://github.com/ashser"))
