"""
TurboShare — QR code display widget.

Generates a QR code from the session URL using the qrcode library
with custom dark-theme colors and displays it as a QLabel.
"""

import io
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

import qrcode
from qrcode.image.pil import PilImage


class QRWidget(QLabel):
    """Displays a QR code scaled to fit the available space."""

    def __init__(self, size: int = 280, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent; border: none;")
        self._current_url = ""

    def set_url(self, url: str) -> None:
        """Generate and display the QR code for the given URL."""
        self._current_url = url

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Custom colors: white modules on dark background
        img = qr.make_image(
            image_factory=PilImage,
            fill_color="#F0F0F5",
            back_color="#16161A",
        )

        # Convert PIL → QPixmap via bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())
        pixmap = pixmap.scaled(
            self._size, self._size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(pixmap)

    def clear_qr(self) -> None:
        self.clear()
        self._current_url = ""
