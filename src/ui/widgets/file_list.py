"""
TurboShare — File list widget.

Scrollable list of files with type icons, sizes, status indicators,
and remove buttons.  Used on the Send Preview and Transfer pages.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)

from src.ui.theme import Colors
from src.utils.file_icons import get_file_icon
from src.utils.formatters import format_size


class FileListItem(QFrame):
    """A single row in the file list."""

    remove_clicked = Signal(int)  # file_id

    def __init__(self, file_id: int, name: str, size: int,
                 removable: bool = True, parent=None):
        super().__init__(parent)
        self.file_id = file_id
        self.setObjectName("file_item_card")
        self.setStyleSheet(f"""
            QFrame#file_item_card {{
                background-color: {Colors.BG_TERTIARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 10px;
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        self.setFixedHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Icon
        icon_label = QLabel(get_file_icon(name))
        icon_label.setFixedWidth(28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(icon_label)

        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; background: transparent;")
        name_label.setToolTip(name)
        layout.addWidget(name_label, 1)

        # Size
        size_label = QLabel(format_size(size))
        size_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(size_label)

        # Status indicator (hidden by default)
        self._status_label = QLabel("")
        self._status_label.setFixedWidth(24)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 16px; background: transparent;")
        self._status_label.hide()
        layout.addWidget(self._status_label)

        # Remove button
        if removable:
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_MUTED};
                    border: none;
                    font-size: 14px;
                    border-radius: 14px;
                    padding: 0px;
                    min-height: 0px;
                    min-width: 0px;
                }}
                QPushButton:hover {{
                    color: {Colors.ACCENT_DANGER};
                    background: {Colors.GLOW_DANGER};
                }}
            """)
            remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.file_id))
            layout.addWidget(remove_btn)

    def set_status(self, status: str) -> None:
        """Update the status indicator: 'done', 'transferring', 'waiting', 'error'."""
        self._status_label.show()
        if status == "done":
            self._status_label.setText("✅")
        elif status == "transferring":
            self._status_label.setText("🔄")
            self._status_label.setStyleSheet(
                "font-size: 16px; background: transparent;"
            )
        elif status == "error":
            self._status_label.setText("❌")
        elif status == "waiting":
            self._status_label.setText("⏳")
            self.setStyleSheet(f"""
                QFrame#file_item_card {{
                    background-color: rgba(22, 22, 26, 0.5);
                    border: 1px solid rgba(42, 42, 53, 0.5);
                    border-radius: 10px;
                }}
            """)
        else:
            self._status_label.hide()


class FileListWidget(QWidget):
    """Scrollable file list with add/remove support."""

    file_removed = Signal(int)  # file_id

    def __init__(self, removable: bool = True, show_footer: bool = True, parent=None):
        super().__init__(parent)
        self._removable = removable
        self._items: dict[int, FileListItem] = {}

        self.setStyleSheet("background: transparent;")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._container)
        outer_layout.addWidget(scroll)

        # Footer: total count + size
        self._footer = QLabel("")
        self._footer.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-size: 12px; "
            f"padding: 8px 0; background: transparent;"
        )
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(self._footer)
        if not show_footer:
            self._footer.hide()

    def add_file(self, file_id: int, name: str, size: int) -> None:
        item = FileListItem(file_id, name, size, self._removable)
        item.remove_clicked.connect(self._on_remove)
        self._items[file_id] = item
        self._list_layout.addWidget(item)
        self._update_footer()

    def remove_file(self, file_id: int) -> None:
        item = self._items.pop(file_id, None)
        if item:
            self._list_layout.removeWidget(item)
            item.deleteLater()
            self._update_footer()

    def clear_files(self) -> None:
        for item in self._items.values():
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._items.clear()
        self._update_footer()

    def update_status(self, file_id: int, status: str) -> None:
        item = self._items.get(file_id)
        if item:
            item.set_status(status)

    def _on_remove(self, file_id: int) -> None:
        self.remove_file(file_id)
        self.file_removed.emit(file_id)

    def _update_footer(self) -> None:
        count = len(self._items)
        # Total size would need the file sizes — for now show count
        self._footer.setText(f"{count} file{'s' if count != 1 else ''}")

    def set_footer(self, text: str) -> None:
        self._footer.setText(text)
