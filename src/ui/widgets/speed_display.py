"""
TurboShare — Animated speed display widget.

Shows transfer speed in MB/s with color coding based on speed:
  Green = fast (>= 30 MB/s)
  Yellow-Orange = medium (10–30 MB/s)
  Red-ish = slow (< 10 MB/s)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from src.ui.theme import Colors


class SpeedDisplay(QLabel):
    """Large animated speed counter (e.g. '45.2 MB/s')."""

    def __init__(self, parent=None):
        super().__init__("0 MB/s", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_style(0)

    def set_speed(self, mbps: float) -> None:
        """Update the displayed speed."""
        if mbps < 0.1:
            self.setText("0 MB/s")
        elif mbps < 1:
            self.setText(f"{mbps * 1024:.0f} KB/s")
        else:
            self.setText(f"{mbps:.1f} MB/s")
        self._update_style(mbps)

    def _update_style(self, mbps: float) -> None:
        if mbps >= 30:
            color = Colors.ACCENT_SUCCESS
        elif mbps >= 10:
            color = Colors.ACCENT_WARNING
        elif mbps > 0:
            color = Colors.ACCENT_DANGER
        else:
            color = Colors.TEXT_MUTED

        self.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 28px;
                font-weight: bold;
                background: transparent;
                padding: 4px 0;
            }}
        """)
