"""
TurboShare — Native PySide6 animation widget.

Replaces the QWebEngineView Lottie widget with high-performance, native
QPainter animations to eliminate external browser engine dependencies.
"""

import math
import time
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget

from src.ui.theme import Colors


class LottieWidget(QWidget):
    """A high-performance QWidget that paints premium animations natively."""

    def __init__(
        self,
        animation_name: str = "",
        width: int = 200,
        height: int = 200,
        loop: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._loop = loop
        self._animation_name = animation_name
        self._is_playing = True

        # Animation state
        self._start_time = time.time()
        self._anim_progress = 0.0  # For non-looping animations (e.g. success)

        # Timer for 60 FPS update
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)  # ~60 FPS

        # Make background transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

    def _on_tick(self) -> None:
        if not self._is_playing:
            return

        if not self._loop:
            # Advance progress over ~1.0 second
            self._anim_progress = min(1.0, self._anim_progress + 0.02)
            if self._anim_progress >= 1.0:
                self._is_playing = False
                self._timer.stop()
        
        self.update()

    def load_animation(self, animation_name: str) -> None:
        """Load and play a native animation by name."""
        self._animation_name = animation_name
        self._start_time = time.time()
        self._anim_progress = 0.0
        self._is_playing = True
        if not self._timer.isActive():
            self._timer.start(16)
        self.update()

    def set_animation(self, animation_name: str) -> None:
        """Switch to a different animation."""
        self.load_animation(animation_name)

    def play(self) -> None:
        if not self._is_playing:
            self._is_playing = True
            if not self._timer.isActive():
                self._timer.start(16)

    def stop(self) -> None:
        self._is_playing = False
        self._timer.stop()
        self._anim_progress = 0.0
        self.update()

    def pause(self) -> None:
        self._is_playing = False
        self._timer.stop()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        W = self.width()
        H = self.height()
        cx = W / 2.0
        cy = H / 2.0
        t = time.time() - self._start_time

        if self._animation_name == "waiting":
            self._draw_waiting(painter, cx, cy, W, H, t)
        elif self._animation_name == "connecting":
            self._draw_connecting(painter, cx, cy, W, H, t)
        elif self._animation_name == "transferring":
            self._draw_transferring(painter, cx, cy, W, H, t)
        elif self._animation_name == "success":
            self._draw_success(painter, cx, cy, W, H, self._anim_progress)
        elif self._animation_name == "error":
            self._draw_error(painter, cx, cy, W, H, self._anim_progress)
        else:
            # Draw placeholder / simple pulsing circle
            self._draw_waiting(painter, cx, cy, W, H, t)

    # ── Painters for Specific Animations ───────────────────────────────

    def _draw_waiting(self, painter: QPainter, cx: float, cy: float, W: int, H: int, t: float) -> None:
        max_r = min(W, H) * 0.45
        min_r = min(W, H) * 0.15

        # Draw 3 pulsing concentric ripples
        for i in range(3):
            p = (t / 2.0 + i / 3.0) % 1.0
            r = min_r + p * (max_r - min_r)
            
            alpha = int((1.0 - p) * 180)
            color = QColor(Colors.ACCENT_PRIMARY)
            color.setAlpha(alpha)

            pen = QPen(color, 2.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Draw center pulse circle
        pulse = 1.0 + 0.08 * math.sin(t * 4.0)
        center_r = min_r * pulse

        # Inner gradient for premium glow
        grad = QRadialGradient(cx, cy, center_r)
        c_inner = QColor(Colors.ACCENT_PRIMARY)
        c_inner.setAlpha(220)
        c_outer = QColor(Colors.ACCENT_PRIMARY)
        c_outer.setAlpha(40)
        grad.setColorAt(0.0, c_inner)
        grad.setColorAt(0.8, c_inner)
        grad.setColorAt(1.0, c_outer)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), center_r, center_r)

        # Subtle thin sharp border around center
        border_color = QColor(Colors.ACCENT_PRIMARY)
        border_color.setAlpha(255)
        painter.setPen(QPen(border_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), center_r - 1.0, center_r - 1.0)

    def _draw_connecting(self, painter: QPainter, cx: float, cy: float, W: int, H: int, t: float) -> None:
        left_x = W * 0.25
        right_x = W * 0.75
        node_y = H * 0.5
        node_r = 10.0

        # Draw connection background link
        line_pen = QPen(QColor(Colors.BORDER_LIGHT), 2, Qt.PenStyle.DashLine)
        painter.setPen(line_pen)
        painter.drawLine(QPointF(left_x, node_y), QPointF(right_x, node_y))

        # Draw pulsing waves between the two nodes
        pulse_p = (t / 1.5) % 1.0
        
        # Left-to-right pulse
        pt1_x = left_x + pulse_p * (right_x - left_x)
        c_pulse1 = QColor(Colors.ACCENT_PRIMARY)
        c_pulse1.setAlpha(int((1.0 - pulse_p) * 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(c_pulse1))
        painter.drawEllipse(QPointF(pt1_x, node_y), 4.5, 4.5)

        # Right-to-left pulse (offset by 0.5s)
        pulse_p2 = (t / 1.5 + 0.5) % 1.0
        pt2_x = right_x - pulse_p2 * (right_x - left_x)
        c_pulse2 = QColor(Colors.ACCENT_SECONDARY)
        c_pulse2.setAlpha(int((1.0 - pulse_p2) * 255))
        painter.setBrush(QBrush(c_pulse2))
        painter.drawEllipse(QPointF(pt2_x, node_y), 4.5, 4.5)

        # Draw left and right central nodes
        for base_x, color_hex in [(left_x, Colors.ACCENT_PRIMARY), (right_x, Colors.ACCENT_SECONDARY)]:
            wave_p = (t / 1.2) % 1.0
            wave_r = node_r + wave_p * 20.0
            wave_color = QColor(color_hex)
            wave_color.setAlpha(int((1.0 - wave_p) * 150))
            painter.setPen(QPen(wave_color, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(base_x, node_y), wave_r, wave_r)

            n_color = QColor(color_hex)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(n_color))
            painter.drawEllipse(QPointF(base_x, node_y), node_r, node_r)

    def _draw_transferring(self, painter: QPainter, cx: float, cy: float, W: int, H: int, t: float) -> None:
        start_x = 15.0
        end_x = W - 15.0
        mid_y = H * 0.5

        # Path: Quadratic Bezier curve arching upwards
        ctrl_x = cx
        ctrl_y = mid_y - 25.0

        path = QPainterPath()
        path.moveTo(start_x, mid_y)
        path.quadTo(ctrl_x, ctrl_y, end_x, mid_y)

        # Draw path shadow / guide
        path_pen = QPen(QColor(Colors.BORDER), 1.5, Qt.PenStyle.SolidLine)
        painter.setPen(path_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Source and destination endpoints
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(Colors.ACCENT_PRIMARY)))
        painter.drawEllipse(QPointF(start_x, mid_y), 5.0, 5.0)

        painter.setBrush(QBrush(QColor(Colors.ACCENT_SECONDARY)))
        painter.drawEllipse(QPointF(end_x, mid_y), 5.0, 5.0)

        # Draw 5 flowing particles along the bezier curve
        for i in range(5):
            p = (t / 1.6 + i / 5.0) % 1.0
            
            x = (1 - p)**2 * start_x + 2 * (1 - p) * p * ctrl_x + p**2 * end_x
            y = (1 - p)**2 * mid_y + 2 * (1 - p) * p * ctrl_y + p**2 * mid_y

            r = 3.0 + 1.5 * math.sin(p * math.pi)

            # Gradient color mix
            mix_color = QColor(
                int((1.0 - p) * 0 + p * 123),
                int((1.0 - p) * 212 + p * 97),
                int((1.0 - p) * 170 + p * 255)
            )
            alpha = 255
            if p < 0.15:
                alpha = int((p / 0.15) * 255)
            elif p > 0.85:
                alpha = int(((1.0 - p) / 0.15) * 255)
            mix_color.setAlpha(alpha)

            trail_color = QColor(mix_color)
            trail_color.setAlpha(int(alpha * 0.3))
            painter.setBrush(QBrush(trail_color))
            painter.drawEllipse(QPointF(x, y), r * 1.8, r * 1.8)

            painter.setBrush(QBrush(mix_color))
            painter.drawEllipse(QPointF(x, y), r, r)

    def _draw_success(self, painter: QPainter, cx: float, cy: float, W: int, H: int, p: float) -> None:
        max_r = min(W, H) * 0.35
        
        # 1. Draw outer circle
        p_circle = min(1.0, p * 2.0)
        circle_pen = QPen(QColor(Colors.ACCENT_SUCCESS), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(circle_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if p_circle > 0.0:
            angle = int(360.0 * p_circle * 16.0)
            rect = QRectF(cx - max_r, cy - max_r, max_r * 2, max_r * 2)
            painter.drawArc(rect, 90 * 16, -angle)

        # 2. Draw checkmark
        p_check = max(0.0, (p - 0.5) * 2.0)
        if p_check > 0.0:
            p0 = QPointF(cx - max_r * 0.4, cy)
            p1 = QPointF(cx - max_r * 0.08, cy + max_r * 0.3)
            p2 = QPointF(cx + max_r * 0.42, cy - max_r * 0.32)

            check_pen = QPen(QColor(Colors.ACCENT_SUCCESS), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(check_pen)

            p_seg1 = min(1.0, p_check * 2.0)
            pt_mid = p0 + (p1 - p0) * p_seg1
            painter.drawLine(p0, pt_mid)

            if p_check > 0.5:
                p_seg2 = (p_check - 0.5) * 2.0
                pt_end = p1 + (p2 - p1) * p_seg2
                painter.drawLine(p1, pt_end)

    def _draw_error(self, painter: QPainter, cx: float, cy: float, W: int, H: int, p: float) -> None:
        max_r = min(W, H) * 0.35
        
        # 1. Draw outer circle
        p_circle = min(1.0, p * 2.0)
        circle_pen = QPen(QColor(Colors.ACCENT_DANGER), 4.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(circle_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if p_circle > 0.0:
            angle = int(360.0 * p_circle * 16.0)
            rect = QRectF(cx - max_r, cy - max_r, max_r * 2, max_r * 2)
            painter.drawArc(rect, 90 * 16, -angle)

        # 2. Draw 'X' cross
        p_cross = max(0.0, (p - 0.5) * 2.0)
        if p_cross > 0.0:
            cross_pen = QPen(QColor(Colors.ACCENT_DANGER), 5.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(cross_pen)

            sz = max_r * 0.32

            p_line1 = min(1.0, p_cross * 2.0)
            tl = QPointF(cx - sz, cy - sz)
            br = QPointF(cx + sz, cy + sz)
            pt1 = tl + (br - tl) * p_line1
            painter.drawLine(tl, pt1)

            if p_cross > 0.5:
                p_line2 = (p_cross - 0.5) * 2.0
                tr = QPointF(cx + sz, cy - sz)
                bl = QPointF(cx - sz, cy + sz)
                pt2 = tr + (bl - tr) * p_line2
                painter.drawLine(tr, pt2)
