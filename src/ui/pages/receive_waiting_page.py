"""
TurboShare — Receive Waiting page.

Shows QR code, URL, PIN, and a folder picker for the save location.
Waits for the phone sender to connect, verify, and complete the
three-stage handshake.
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog,
)

from src.core.config import DEFAULT_SAVE_DIR
from src.ui.theme import Colors
from src.ui.widgets.qr_widget import QRWidget
from src.ui.widgets.pin_display import PinDisplay
from src.ui.animations import LottieWidget


class ReceiveWaitingPage(QWidget):
    """Receive mode waiting page."""

    confirm_clicked = Signal()
    reject_clicked = Signal()
    cancel_clicked = Signal()
    save_dir_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        self._save_dir = DEFAULT_SAVE_DIR

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("📥 Receive Mode")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 24px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY}; background: transparent;
        """)
        layout.addWidget(title)

        layout.addSpacing(8)

        # Card container
        card = QFrame()
        card.setObjectName("receive_card_frame")
        card.setStyleSheet(f"""
            QFrame#receive_card_frame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        card.setMaximumWidth(480)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # QR Code
        self._qr_widget = QRWidget(size=180)
        card_layout.addWidget(self._qr_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # URL
        self._url_label = QLabel("")
        self._url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._url_label.setWordWrap(True)
        self._url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._url_label.setStyleSheet(f"""
            font-size: 10px; color: {Colors.TEXT_MUTED};
            font-family: "Consolas", monospace; background: transparent;
        """)
        card_layout.addWidget(self._url_label)

        # HTTPS hint
        https_hint = QLabel("📱 On phone: tap Advanced → Proceed if warned about certificate")
        https_hint.setWordWrap(True)
        https_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        https_hint.setStyleSheet(f"font-size: 10px; color: {Colors.ACCENT_WARNING}; background: transparent;")
        card_layout.addWidget(https_hint)

        # PIN
        pin_title = QLabel("PIN")
        pin_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_title.setStyleSheet(f"""
            font-size: 12px; color: {Colors.TEXT_SECONDARY};
            font-weight: bold; background: transparent; letter-spacing: 3px;
        """)
        card_layout.addWidget(pin_title)

        self._pin_display = PinDisplay()
        card_layout.addWidget(self._pin_display, alignment=Qt.AlignmentFlag.AlignCenter)

        card_layout.addSpacing(4)

        # Status
        self._status_label = QLabel("Waiting for sender to connect…")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.TEXT_SECONDARY};
            background: transparent;
        """)
        card_layout.addWidget(self._status_label)

        # Lottie
        self._lottie = LottieWidget("waiting", width=80, height=80)
        card_layout.addWidget(self._lottie, alignment=Qt.AlignmentFlag.AlignCenter)

        # Device info (hidden)
        self._device_info_label = QLabel("")
        self._device_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._device_info_label.setWordWrap(True)
        self._device_info_label.setStyleSheet(f"""
            font-size: 13px; color: {Colors.ACCENT_PRIMARY};
            background: transparent; padding: 8px;
        """)
        self._device_info_label.hide()
        card_layout.addWidget(self._device_info_label)

        # Confirm / Reject
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._reject_btn = QPushButton("✕ Reject")
        self._reject_btn.setProperty("class", "danger")
        self._reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reject_btn.hide()
        self._reject_btn.clicked.connect(self.reject_clicked.emit)
        btn_layout.addWidget(self._reject_btn)

        self._confirm_btn = QPushButton("✓ Confirm & Receive")
        self._confirm_btn.setProperty("class", "primary")
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.clicked.connect(self.confirm_clicked.emit)
        btn_layout.addWidget(self._confirm_btn)

        card_layout.addLayout(btn_layout)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

        # ── Save To ─────────────────────────────────────────────────
        save_layout = QHBoxLayout()
        save_layout.setSpacing(8)
        save_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        save_label = QLabel("Save to:")
        save_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        save_layout.addWidget(save_label)

        self._save_path_label = QLabel(str(self._save_dir))
        self._save_path_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY}; font-size: 12px;
            font-family: "Consolas", monospace; background: transparent;
        """)
        save_layout.addWidget(self._save_path_label)

        browse_btn = QPushButton("📂 Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.ACCENT_PRIMARY};
                border: 1px solid {Colors.BORDER}; border-radius: 6px;
                padding: 4px 10px; font-size: 11px;
            }}
            QPushButton:hover {{ border-color: {Colors.ACCENT_PRIMARY}; }}
        """)
        browse_btn.clicked.connect(self._browse_folder)
        save_layout.addWidget(browse_btn)

        layout.addLayout(save_layout)

        # Cancel
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {Colors.TEXT_MUTED};
                border: none; font-size: 12px; padding: 6px;
            }}
            QPushButton:hover {{ color: {Colors.ACCENT_DANGER}; }}
        """)
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Public API ──────────────────────────────────────────────────

    def setup(self, url: str, pin: str) -> None:
        self._qr_widget.set_url(url)
        self._url_label.setText(url)
        self._pin_display.set_pin(pin)
        self._status_label.setText("Waiting for sender to connect…")
        self._device_info_label.hide()
        self._confirm_btn.setEnabled(False)
        self._reject_btn.hide()
        self._lottie.load_animation("waiting")

    def show_sender_info(self, browser: str, os_name: str, ip: str) -> None:
        self._status_label.setText("Sender found — verify the device below")
        self._status_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.ACCENT_SUCCESS};
            background: transparent; font-weight: bold;
        """)
        self._device_info_label.setText(
            f"🌐 Browser: {browser}\n💻 OS: {os_name}\n📡 IP: {ip}"
        )
        self._device_info_label.show()
        self._confirm_btn.setEnabled(True)
        self._reject_btn.show()
        self._lottie.load_animation("connecting")

    def refresh_session(self, url: str, pin: str) -> None:
        self.setup(url, pin)

    @property
    def save_dir(self) -> Path:
        return self._save_dir

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(
            self, "Select Save Folder", str(self._save_dir)
        )
        if folder:
            self._save_dir = Path(folder)
            self._save_path_label.setText(folder)
            self.save_dir_changed.emit(folder)
