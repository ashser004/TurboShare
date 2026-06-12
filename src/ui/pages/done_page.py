"""
TurboShare — Done / Transfer Complete page.

Shows a success Lottie animation, transfer stats (files, size, speed,
time), and navigation buttons (Send More, Go Home, Open Folder).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)

from src.ui.theme import Colors
from src.ui.animations import LottieWidget
from src.utils.formatters import format_size, format_duration


class DonePage(QWidget):
    """Transfer complete page with stats and navigation."""

    send_more_clicked = Signal()
    go_home_clicked = Signal()
    open_folder_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.BG_PRIMARY};")
        self._is_receive = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        # Lottie success animation
        self._lottie = LottieWidget("success", width=120, height=120, loop=False)
        layout.addWidget(self._lottie, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        self._title_label = QLabel("Transfer Complete! 🎉")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setStyleSheet(f"""
            font-size: 28px; font-weight: bold;
            color: {Colors.ACCENT_SUCCESS}; background: transparent;
        """)
        layout.addWidget(self._title_label)

        layout.addSpacing(8)

        # Stats card
        stats_card = QFrame()
        stats_card.setObjectName("stats_card_frame")
        stats_card.setMaximumWidth(400)
        stats_card.setStyleSheet(f"""
            QFrame#stats_card_frame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 20, 24, 20)
        stats_layout.setSpacing(10)

        self._stats_labels: dict[str, QLabel] = {}
        for key, label_text in [
            ("files", "📁 Files transferred"),
            ("size", "💾 Total size"),
            ("speed", "⚡ Average speed"),
            ("time", "⏱️ Time taken"),
        ]:
            row = QHBoxLayout()
            name = QLabel(label_text)
            name.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 14px; background: transparent;")
            row.addWidget(name)

            value = QLabel("—")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            value.setStyleSheet(f"""
                color: {Colors.TEXT_PRIMARY}; font-size: 14px;
                font-weight: bold; background: transparent;
            """)
            row.addWidget(value)

            self._stats_labels[key] = value
            stats_layout.addLayout(row)

        layout.addWidget(stats_card, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch(1)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._open_folder_btn = QPushButton("📂 Open Folder")
        self._open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER};
                border-radius: 12px; padding: 12px 24px; font-size: 14px;
            }}
            QPushButton:hover {{ border-color: {Colors.ACCENT_PRIMARY}; }}
        """)
        self._open_folder_btn.clicked.connect(self.open_folder_clicked.emit)
        self._open_folder_btn.hide()
        btn_layout.addWidget(self._open_folder_btn)

        send_more_btn = QPushButton("📤 Send More")
        send_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_more_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_PRIMARY}; border: 1px solid {Colors.BORDER};
                border-radius: 12px; padding: 12px 24px; font-size: 14px;
            }}
            QPushButton:hover {{ border-color: {Colors.ACCENT_SECONDARY}; }}
        """)
        send_more_btn.clicked.connect(self.send_more_clicked.emit)
        btn_layout.addWidget(send_more_btn)

        home_btn = QPushButton("🏠 Go Home")
        home_btn.setProperty("class", "primary")
        home_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        home_btn.clicked.connect(self.go_home_clicked.emit)
        btn_layout.addWidget(home_btn)

        layout.addLayout(btn_layout)

        layout.addStretch(1)

    # ── Public API ──────────────────────────────────────────────────

    def show_stats(self, stats: dict, is_receive: bool = False) -> None:
        """Display transfer completion stats."""
        self._is_receive = is_receive
        self._open_folder_btn.setVisible(is_receive)

        self._stats_labels["files"].setText(str(stats.get("total_files", 0)))
        self._stats_labels["size"].setText(format_size(stats.get("total_size", 0)))
        self._stats_labels["speed"].setText(f"{stats.get('average_speed_mbps', 0):.1f} MB/s")
        self._stats_labels["time"].setText(format_duration(stats.get("elapsed_seconds", 0)))

        self._lottie.load_animation("success")
