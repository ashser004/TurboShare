"""
TurboShare — Large spaced PIN digit display widget.

Shows the 6-digit PIN in large, individually-boxed digits with a
subtle glow border animation.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from src.ui.theme import Colors


class PinDisplay(QWidget):
    """Displays a 6-digit PIN in large boxed digits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._digits: list[QLabel] = []
        for _ in range(6):
            digit = QLabel("–")
            digit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            digit.setFixedSize(56, 72)
            digit.setStyleSheet(f"""
                QLabel {{
                    background-color: {Colors.BG_TERTIARY};
                    color: {Colors.ACCENT_PRIMARY};
                    border: 2px solid {Colors.BORDER_LIGHT};
                    border-radius: 12px;
                    font-size: 32px;
                    font-weight: bold;
                    font-family: "Consolas", "Courier New", monospace;
                }}
            """)
            self._digits.append(digit)
            self._layout.addWidget(digit)

    def set_pin(self, pin: str) -> None:
        """Update the displayed PIN digits."""
        for i, digit_label in enumerate(self._digits):
            if i < len(pin):
                digit_label.setText(pin[i])
            else:
                digit_label.setText("–")

    def clear_pin(self) -> None:
        for d in self._digits:
            d.setText("–")
