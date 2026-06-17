"""
TurboShare — Security Preferences Page.

Allows configuring "Safe Transfer" bypass mode with warning verification.
"""

from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QDialog, QLineEdit, QAbstractButton,
)

from src.ui.theme import Colors
from src.core.preferences import save_safe_transfer_setting, load_safe_transfer_setting


class SecurityPage(QWidget):
    """Security settings panel with Safe Transfer configuration."""

    back_clicked = Signal()

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session

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
        card.setObjectName("security_card")
        card.setStyleSheet(f"""
            QFrame#security_card {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)

        # Title
        title_label = QLabel("🔒 Security Options")
        title_label.setStyleSheet(f"""
            font-size: 24px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY};
        """)
        card_layout.addWidget(title_label)

        # Toggle Row
        toggle_layout = QHBoxLayout()
        
        info_layout = QVBoxLayout()
        setting_title = QLabel("Safe Transfer (Recommended)")
        setting_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        setting_desc = QLabel("Enforces a 6-digit PIN handshake and double-check desktop confirmations.")
        setting_desc.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_SECONDARY};")
        setting_desc.setWordWrap(True)
        info_layout.addWidget(setting_title)
        info_layout.addWidget(setting_desc)
        
        toggle_layout.addLayout(info_layout, 1)

        self.toggle = SwitchToggle()
        self.toggle.setChecked(load_safe_transfer_setting())
        self.toggle.update_style()
        self.toggle.clicked.connect(self._on_toggle_clicked)
        toggle_layout.addWidget(self.toggle, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        card_layout.addLayout(toggle_layout)

        layout.addWidget(card)
        layout.addStretch(2)

    def _on_toggle_clicked(self) -> None:
        """Handle toggling of Safe Transfer settings."""
        currently_enabled = self.toggle.isChecked()
        
        if currently_enabled:
            # User is trying to turn it OFF — show warning dialog
            dialog = SecurityWarningDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Typecheck passed — disable Safe Transfer
                save_safe_transfer_setting(False)
                self.session.safe_transfer = False
                self.toggle.setChecked(False)
        else:
            # User is turning it back ON — allow instantly
            save_safe_transfer_setting(True)
            self.session.safe_transfer = True
            self.toggle.setChecked(True)


class SwitchToggle(QAbstractButton):
    """Custom styled modern toggle switch with smooth sliding knob animation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(58, 28)

        # Colors
        self._active_color = QColor(Colors.ACCENT_SUCCESS)
        self._bg_color = QColor(Colors.BG_HOVER)
        self._knob_color = QColor("#FFFFFF")
        self._border_color = QColor(Colors.BORDER)

        # Knob offset animation (from 4px margin to width - knob_size - 4px margin)
        self._knob_x = 4
        self._knob_size = 20
        self.anim = QPropertyAnimation(self, b"knob_x")
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @Property(int)
    def knob_x(self) -> int:
        return self._knob_x

    @knob_x.setter
    def knob_x(self, pos: int) -> None:
        self._knob_x = pos
        self.update()

    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        if self.isVisible():
            self._animate(checked)
        else:
            self.anim.stop()
            margin = 4
            target = self.width() - self._knob_size - margin if checked else margin
            self._knob_x = target
            self.update()

    def nextCheckState(self) -> None:
        # Do not automatically change state on click.
        # We will handle state changes manually in _on_toggle_clicked.
        pass

    def _animate(self, checked: bool) -> None:
        self.anim.stop()
        margin = 4
        start = self._knob_x
        end = self.width() - self._knob_size - margin if checked else margin
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background pill
        rect = self.rect()
        radius = rect.height() / 2

        if self.isChecked():
            painter.setBrush(QBrush(self._active_color))
            painter.setPen(Qt.PenStyle.NoPen)
        else:
            painter.setBrush(QBrush(self._bg_color))
            painter.setPen(QPen(self._border_color, 1.5))

        painter.drawRoundedRect(rect, radius, radius)

        # Draw slider knob
        margin = (rect.height() - self._knob_size) / 2
        knob_rect = QRect(int(self._knob_x), int(margin), self._knob_size, self._knob_size)

        painter.setBrush(QBrush(self._knob_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(knob_rect)
        painter.end()

    def update_style(self) -> None:
        """Compatibility wrapper for programmatically setting state."""
        pass



class SecurityWarningDialog(QDialog):
    """Warning modal validating the safe transfer bypass verification phrase."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Security Warning")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setStyleSheet(f"background-color: {Colors.BG_SECONDARY}; border-radius: 16px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Warning Header
        warn_title = QLabel("⚠️ CRITICAL SECURITY WARNING")
        warn_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.ACCENT_DANGER};")
        layout.addWidget(warn_title)

        # Warning Details
        warn_desc = QLabel(
            "Turning OFF Safe Transfer bypasses the PIN handshake and manual laptop confirmation.\n\n"
            "This allows anyone on the same local network who scans or guesses your session URL to "
            "freely receive files from or upload files to your laptop!\n\n"
            "Only disable this on trusted networks (such as your private Mobile Hotspot)."
        )
        warn_desc.setWordWrap(True)
        warn_desc.setStyleSheet(f"font-size: 13px; color: {Colors.TEXT_PRIMARY}; line-height: 1.5;")
        layout.addWidget(warn_desc)

        # Validation instruction
        val_instruction = QLabel("To confirm, type the exact phrase below:")
        val_instruction.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY}; font-weight: bold;")
        layout.addWidget(val_instruction)

        phrase_label = QLabel("I am turning OFF SAFE transfer")
        phrase_label.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; font-family: monospace;
            color: {Colors.TEXT_PRIMARY}; background-color: {Colors.BG_PRIMARY};
            padding: 10px; border-radius: 6px; border: 1px solid {Colors.BORDER};
        """)
        phrase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(phrase_label)

        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type the phrase here...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT_DANGER};
            }}
        """)
        self.input_field.textChanged.connect(self._validate)
        layout.addWidget(self.input_field)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {Colors.ACCENT_DANGER}; font-size: 12px;")
        layout.addWidget(self.error_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.TEXT_SECONDARY};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.confirm_btn = QPushButton("Turn OFF")
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 77, 106, 0.1);
                color: {Colors.ACCENT_DANGER};
                border: 1px solid {Colors.ACCENT_DANGER};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px; font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_DANGER};
                color: {Colors.BG_PRIMARY};
            }}
            QPushButton:disabled {{
                background-color: transparent;
                border-color: {Colors.BORDER};
                color: {Colors.TEXT_MUTED};
            }}
        """)
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)

        layout.addLayout(btn_layout)

    def _validate(self, text: str) -> None:
        """Enable the confirmation button only if the phrase matches exactly."""
        target_phrase = "I am turning OFF SAFE transfer"
        is_match = text.strip() == target_phrase
        self.confirm_btn.setEnabled(is_match)
        if text and not target_phrase.startswith(text):
            self.error_label.setText("Phrase does not match target phrase.")
        else:
            self.error_label.setText("")
