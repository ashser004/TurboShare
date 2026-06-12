"""
TurboShare — Send Preview page.

Left panel:  File list with remove/add-more, total count + size + ETA
Right panel: QR code, URL, PIN, status message, Lottie animation, Confirm button
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame,
    QFileDialog,
)

from src.ui.theme import Colors
from src.ui.widgets.qr_widget import QRWidget
from src.ui.widgets.pin_display import PinDisplay
from src.ui.widgets.file_list import FileListWidget
from src.ui.animations import LottieWidget
from src.utils.formatters import format_size, estimate_transfer_time


class SendPreviewPage(QWidget):
    """Send Preview: file list on left, QR + PIN + status on right."""

    confirm_clicked = Signal()
    reject_clicked = Signal()
    cancel_clicked = Signal()
    files_changed = Signal(list)    # updated file list

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files_data: list[dict] = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(20)

        # ── LEFT PANEL: File list ───────────────────────────────────
        left_panel = QFrame()
        left_panel.setObjectName("left_panel_frame")
        left_panel.setStyleSheet(f"""
            QFrame#left_panel_frame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        files_title = QLabel("📁 Selected Files")
        files_title.setStyleSheet(f"""
            font-size: 18px; font-weight: bold;
            color: {Colors.TEXT_PRIMARY}; background: transparent;
        """)
        left_layout.addWidget(files_title)

        self._file_list = FileListWidget(removable=True, show_footer=False)
        self._file_list.file_removed.connect(self._on_file_removed)
        left_layout.addWidget(self._file_list, 1)

        # Add More button
        add_more_btn = QPushButton("+ Add More Files")
        add_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_more_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.ACCENT_PRIMARY};
                border: 1px dashed {Colors.ACCENT_PRIMARY};
                border-radius: 10px;
                padding: 10px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {Colors.GLOW_PRIMARY};
            }}
        """)
        add_more_btn.clicked.connect(self._add_more_files)
        left_layout.addWidget(add_more_btn)

        # Summary footer
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY}; font-size: 12px;
            background: transparent; padding: 4px 0;
        """)
        self._summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self._summary_label)

        main_layout.addWidget(left_panel, 1)

        # ── RIGHT PANEL: QR + PIN + Status ──────────────────────────
        right_panel = QFrame()
        right_panel.setObjectName("right_panel_frame")
        right_panel.setStyleSheet(f"""
            QFrame#right_panel_frame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(8)
        right_layout.addStretch(1)

        # QR Code
        self._qr_widget = QRWidget(size=180)
        right_layout.addWidget(self._qr_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # URL text
        self._url_label = QLabel("")
        self._url_label.setProperty("class", "url-text")
        self._url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._url_label.setWordWrap(True)
        self._url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._url_label.setStyleSheet(f"""
            font-size: 10px; color: {Colors.TEXT_MUTED};
            font-family: "Consolas", monospace; background: transparent;
        """)
        right_layout.addWidget(self._url_label)

        # HTTPS warning hint
        self._https_hint = QLabel("📱 On phone: tap Advanced → Proceed if warned about certificate")
        self._https_hint.setWordWrap(True)
        self._https_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._https_hint.setStyleSheet(f"""
            font-size: 10px; color: {Colors.ACCENT_WARNING};
            background: transparent; padding: 2px;
        """)
        right_layout.addWidget(self._https_hint)

        # PIN display
        pin_title = QLabel("PIN")
        pin_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_title.setStyleSheet(f"""
            font-size: 12px; color: {Colors.TEXT_SECONDARY};
            font-weight: bold; background: transparent; letter-spacing: 3px;
        """)
        right_layout.addWidget(pin_title, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._pin_display = PinDisplay()
        right_layout.addWidget(self._pin_display, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout.addSpacing(8)

        # Status message
        self._status_label = QLabel("Waiting for receiver to scan…")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        self._status_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.TEXT_SECONDARY};
            background: transparent;
        """)
        right_layout.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Lottie animation
        self._lottie = LottieWidget("waiting", width=80, height=80)
        right_layout.addWidget(self._lottie, alignment=Qt.AlignmentFlag.AlignCenter)
        self._lottie.hide()

        # Device info (hidden initially)
        self._device_info_label = QLabel("")
        self._device_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._device_info_label.setWordWrap(True)
        self._device_info_label.setStyleSheet(f"""
            font-size: 13px; color: {Colors.ACCENT_PRIMARY};
            background: transparent; padding: 8px;
        """)
        self._device_info_label.hide()
        right_layout.addWidget(self._device_info_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Confirm / Reject buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._reject_btn = QPushButton("✕ Reject")
        self._reject_btn.setProperty("class", "danger")
        self._reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reject_btn.hide()
        self._reject_btn.clicked.connect(self.reject_clicked.emit)
        btn_layout.addWidget(self._reject_btn)

        self._confirm_btn = QPushButton("✓ Confirm & Send")
        self._confirm_btn.setProperty("class", "primary")
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT_PRIMARY};
                color: {Colors.BG_PRIMARY};
                border: none;
                border-radius: 12px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00E8BB;
            }}
            QPushButton:disabled {{
                background-color: rgba(0, 212, 170, 0.08);
                color: rgba(0, 212, 170, 0.35);
                border: 1px solid rgba(0, 212, 170, 0.18);
            }}
        """)
        self._confirm_btn.clicked.connect(self.confirm_clicked.emit)
        self._confirm_btn.hide()
        btn_layout.addWidget(self._confirm_btn)

        right_layout.addLayout(btn_layout)
        right_layout.addStretch(1)

        # Cancel button
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
        right_layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(right_panel, 1)

    # ── Public API ──────────────────────────────────────────────────

    def setup(self, files: list[dict], url: str, pin: str) -> None:
        """Populate the page with files and session info."""
        self._files_data = list(files)

        self._file_list.clear_files()
        for f in files:
            self._file_list.add_file(f["id"], f["name"], f["size"])

        self._update_summary()
        self._qr_widget.set_url(url)
        self._url_label.setText(url)
        self._pin_display.set_pin(pin)

        # Reset state
        self._status_label.setText("Waiting for receiver to scan…")
        self._device_info_label.hide()
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.hide()
        self._reject_btn.hide()
        self._lottie.hide()
        
        # Show QR code elements
        self._qr_widget.show()
        self._url_label.show()
        self._https_hint.show()

    def show_receiver_info(self, browser: str, os_name: str, ip: str) -> None:
        """Called when Stage 1 completes — show device info and enable Confirm."""
        self._status_label.setText("Receiver found — verify the device below")
        self._status_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.ACCENT_SUCCESS};
            background: transparent; font-weight: bold;
        """)
        self._device_info_label.setText(
            f"🌐 Browser: {browser}\n"
            f"💻 OS: {os_name}\n"
            f"📡 IP: {ip}"
        )
        self._device_info_label.show()
        self._confirm_btn.setEnabled(True)
        self._confirm_btn.show()
        self._reject_btn.show()
        self._lottie.load_animation("connecting")
        self._lottie.show()
        
        # Hide QR code elements to prevent layout overlapping
        self._qr_widget.hide()
        self._url_label.hide()
        self._https_hint.hide()

    def refresh_session(self, url: str, pin: str) -> None:
        """Refresh QR + PIN after session regeneration."""
        self._qr_widget.set_url(url)
        self._url_label.setText(url)
        self._pin_display.set_pin(pin)
        self._status_label.setText("Waiting for receiver to scan…")
        self._status_label.setStyleSheet(f"""
            font-size: 14px; color: {Colors.TEXT_SECONDARY};
            background: transparent;
        """)
        self._device_info_label.hide()
        self._confirm_btn.setEnabled(False)
        self._update_button_style(self._confirm_btn)
        self._confirm_btn.hide()
        self._reject_btn.hide()
        self._lottie.hide()
        
        # Show QR code elements
        self._qr_widget.show()
        self._url_label.show()
        self._https_hint.show()

    # ── Private ─────────────────────────────────────────────────────

    def _on_file_removed(self, file_id: int) -> None:
        self._files_data = [f for f in self._files_data if f["id"] != file_id]
        self._update_summary()
        self.files_changed.emit(self._files_data)

    def _add_more_files(self) -> None:
        from PySide6.QtCore import QStandardPaths
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Add Files", default_dir, "All Files (*)"
        )
        if not paths:
            return

        from pathlib import Path
        existing_paths = {str(Path(f["path"]).resolve()) for f in self._files_data}

        next_id = max((f["id"] for f in self._files_data), default=-1) + 1
        for p in paths:
            p = Path(p)
            abs_path = str(p.resolve())
            if abs_path in existing_paths:
                continue
            entry = {
                "id": next_id,
                "name": p.name,
                "path": str(p),
                "size": p.stat().st_size,
            }
            self._files_data.append(entry)
            self._file_list.add_file(entry["id"], entry["name"], entry["size"])
            next_id += 1
            existing_paths.add(abs_path)

        self._update_summary()
        self.files_changed.emit(self._files_data)

    def _update_summary(self) -> None:
        count = len(self._files_data)
        total = sum(f["size"] for f in self._files_data)
        eta = estimate_transfer_time(total)
        self._summary_label.setText(
            f"{count} file{'s' if count != 1 else ''} • "
            f"{format_size(total)} • "
            f"Est. {eta}"
        )
        self._file_list.set_footer(
            f"{count} file{'s' if count != 1 else ''} • {format_size(total)}"
        )

    def _update_button_style(self, button: QPushButton) -> None:
        button.style().unpolish(button)
        button.style().polish(button)
