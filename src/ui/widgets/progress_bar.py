"""
TurboShare — Custom animated progress bar.

A custom-painted progress bar with gradient fill, glow effect on the
leading edge, and smooth value interpolation.
"""

from typing import TYPE_CHECKING, Any
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QByteArray,
)

if TYPE_CHECKING:
    def Property(*args: Any, **kwargs: Any) -> Any: ...
else:
    from PySide6.QtCore import Property
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPen
from PySide6.QtWidgets import QWidget

from src.ui.theme import Colors


class AnimatedProgressBar(QWidget):
    """Smooth animated progress bar with gradient fill and glow."""

    def __init__(self, parent=None, height: int = 14):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setMinimumWidth(100)
        self.setStyleSheet("background: transparent;")

        self._value = 0.0       # 0.0 – 1.0
        self._display_value = 0.0  # interpolated for smooth animation

        self._anim = QPropertyAnimation(self, QByteArray(b"display_value"))
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Property for animation ──────────────────────────────────────

    def _get_display_value(self) -> float:
        return self._display_value

    def _set_display_value(self, val: float) -> None:
        self._display_value = val
        self.update()

    display_value = Property(float, fget=_get_display_value, fset=_set_display_value)

    # ── Public API ──────────────────────────────────────────────────

    def set_value(self, value: float) -> None:
        """Set the progress (0.0 – 1.0) with smooth animation."""
        self._value = max(0.0, min(1.0, value))
        self._anim.stop()
        self._anim.setStartValue(self._display_value)
        self._anim.setEndValue(self._value)
        self._anim.start()

    def set_value_instant(self, value: float) -> None:
        """Set without animation (e.g. on reset)."""
        self._value = max(0.0, min(1.0, value))
        self._display_value = self._value
        self.update()

    @property
    def value(self) -> float:
        return self._value

    # ── Painting ────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        radius = h / 2

        # Track background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Colors.BG_TERTIARY))
        painter.drawRoundedRect(0, 0, w, h, radius, radius)

        # Filled portion
        fill_w = int(w * self._display_value)
        if fill_w > 0:
            gradient = QLinearGradient(0, 0, fill_w, 0)
            gradient.setColorAt(0.0, QColor(Colors.ACCENT_PRIMARY))
            gradient.setColorAt(1.0, QColor(Colors.ACCENT_SECONDARY))
            painter.setBrush(gradient)
            painter.drawRoundedRect(0, 0, fill_w, h, radius, radius)

            # Glow on leading edge
            if fill_w > 4:
                glow_color = QColor(Colors.ACCENT_PRIMARY)
                glow_color.setAlpha(80)
                painter.setBrush(glow_color)
                glow_x = max(0, fill_w - 20)
                painter.drawRoundedRect(glow_x, 0, min(20, fill_w), h, radius, radius)

        # Percentage text
        if w > 80:
            pct = f"{self._display_value * 100:.0f}%"
            painter.setPen(QPen(QColor(Colors.TEXT_PRIMARY)))
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, pct)

        painter.end()
