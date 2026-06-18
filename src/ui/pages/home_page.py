"""
TurboShare — Home page.

Shows the TurboShare logo with two large buttons: Send and Receive.
Includes the info (ℹ️) button for firewall help and version in the corner.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem,
    QSizePolicy, QFrame,
)

from src.core.config import APP_VERSION, LOGO_PATH
from src.ui.theme import Colors
from src.ui.widgets.info_dialog import InfoButton


class HomePage(QWidget):
    """Home page with Send and Receive buttons."""

    send_clicked = Signal()
    receive_clicked = Signal()
    hamburger_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(0)

        # ── Top bar: hamburger & info button ────────────────────────
        top_bar = QHBoxLayout()

        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hamburger_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_PRIMARY};
                font-size: 24px;
                padding: 4px;
                min-width: 36px;
                max-width: 36px;
                min-height: 36px;
                max-height: 36px;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_PRIMARY};
            }}
        """)
        self.hamburger_btn.clicked.connect(self.hamburger_clicked.emit)
        top_bar.addWidget(self.hamburger_btn)

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

        subtitle = QLabel("Fast • Secure • Reliable")
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

        layout.addSpacing(24)

        # ── Drag and Drop Label ─────────────────────────────────────
        drag_label = QLabel("Drag and Drop File(s) to share")
        drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drag_label.setStyleSheet(f"""
            font-size: 14px; font-weight: 500;
            color: {Colors.TEXT_SECONDARY};
            background: transparent;
        """)
        layout.addWidget(drag_label)

        layout.addStretch(3)

        # ── Version footer ──────────────────────────────────────────
        version = QLabel(f"v{APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"""
            font-size: 11px; color: {Colors.TEXT_MUTED};
            background: transparent;
        """)
        layout.addWidget(version)

        # Instantiate overlay
        self.drag_overlay = DragOverlay(self)

    def show_drag_overlay(self, visible: bool) -> None:
        """Toggle visual drag overlay highlight."""
        if visible:
            self.drag_overlay.show()
            self.drag_overlay.raise_()
        else:
            self.drag_overlay.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "drag_overlay"):
            self.drag_overlay.setGeometry(self.rect())


class DragOverlay(QWidget):
    """Semi-transparent overlay with a dashed border shown during drag-and-drop."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        self.border_frame = QFrame()
        self.border_frame.setStyleSheet(f"""
            QFrame {{
                border: 3px dashed {Colors.ACCENT_PRIMARY};
                border-radius: 24px;
                background-color: {Colors.GLOW_PRIMARY};
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)

        frame_layout = QVBoxLayout(self.border_frame)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("📥\n\nDrop Files Here to Share!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            color: {Colors.ACCENT_PRIMARY};
            font-size: 22px;
            font-weight: bold;
        """)

        frame_layout.addWidget(label)
        layout.addWidget(self.border_frame)
