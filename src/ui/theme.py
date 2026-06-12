"""
TurboShare — Dark premium theme engine.

Defines the color palette, typography, and generates a global QSS
stylesheet that is applied to the entire application.
"""

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication

from src.core.config import FONTS_DIR


# ── Color Palette ───────────────────────────────────────────────────

class Colors:
    BG_PRIMARY      = "#0D0D0F"
    BG_SECONDARY    = "#16161A"
    BG_TERTIARY     = "#1E1E24"
    BG_HOVER        = "#252530"

    ACCENT_PRIMARY  = "#00D4AA"       # Teal-green
    ACCENT_SECONDARY = "#7B61FF"      # Purple
    ACCENT_DANGER   = "#FF4D6A"       # Red
    ACCENT_SUCCESS  = "#00E676"       # Green
    ACCENT_WARNING  = "#FFB74D"       # Orange

    TEXT_PRIMARY    = "#F0F0F5"
    TEXT_SECONDARY  = "#8A8A9A"
    TEXT_MUTED      = "#4A4A5A"

    BORDER          = "#2A2A35"
    BORDER_LIGHT    = "#3A3A48"

    # Transparent variants
    GLOW_PRIMARY    = "rgba(0, 212, 170, 0.15)"
    GLOW_SUCCESS    = "rgba(0, 230, 118, 0.15)"
    GLOW_DANGER     = "rgba(255, 77, 106, 0.15)"


# ── Typography ──────────────────────────────────────────────────────

FONT_FAMILY = "Inter"
FONT_FALLBACK = "Segoe UI, Arial, sans-serif"

def load_fonts() -> None:
    """Load bundled Inter font files into the Qt font database."""
    fonts_dir = FONTS_DIR
    if not fonts_dir.is_dir():
        return
    for font_file in fonts_dir.glob("*.woff2"):
        QFontDatabase.addApplicationFont(str(font_file))
    for font_file in fonts_dir.glob("*.ttf"):
        QFontDatabase.addApplicationFont(str(font_file))


def get_font(size: int = 14, weight: str = "normal") -> QFont:
    """Create a QFont with the app's typeface."""
    font = QFont(FONT_FAMILY)
    font.setPointSize(size)
    if weight == "bold":
        font.setBold(True)
    elif weight == "semibold":
        font.setWeight(QFont.Weight.DemiBold)
    elif weight == "medium":
        font.setWeight(QFont.Weight.Medium)
    return font


# ── Global Stylesheet ──────────────────────────────────────────────

def get_stylesheet() -> str:
    """Return the complete QSS stylesheet for the application."""
    return f"""
    /* ── Global ─────────────────────────────────────────── */
    QWidget {{
        background-color: {Colors.BG_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        font-family: "{FONT_FAMILY}", {FONT_FALLBACK};
        font-size: 14px;
    }}

    /* ── Labels ─────────────────────────────────────────── */
    QLabel {{
        background: transparent;
        padding: 0;
    }}

    QLabel[class="heading"] {{
        font-size: 28px;
        font-weight: bold;
        color: {Colors.TEXT_PRIMARY};
    }}

    QLabel[class="subheading"] {{
        font-size: 16px;
        color: {Colors.TEXT_SECONDARY};
    }}

    QLabel[class="muted"] {{
        font-size: 12px;
        color: {Colors.TEXT_MUTED};
    }}

    QLabel[class="accent"] {{
        color: {Colors.ACCENT_PRIMARY};
        font-weight: bold;
    }}

    QLabel[class="url-text"] {{
        font-size: 11px;
        color: {Colors.TEXT_MUTED};
        font-family: "Consolas", "Courier New", monospace;
    }}

    /* ── Buttons ────────────────────────────────────────── */
    QPushButton {{
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 12px;
        padding: 14px 28px;
        font-size: 15px;
        font-weight: bold;
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {Colors.BG_HOVER};
        border-color: {Colors.ACCENT_PRIMARY};
    }}

    QPushButton:pressed {{
        background-color: {Colors.BG_SECONDARY};
    }}

    QPushButton:disabled {{
        background-color: {Colors.BG_SECONDARY};
        color: {Colors.TEXT_MUTED};
        border-color: {Colors.BORDER};
    }}

    QPushButton[class="primary"] {{
        background-color: {Colors.ACCENT_PRIMARY};
        color: {Colors.BG_PRIMARY};
        border: none;
    }}

    QPushButton[class="primary"]:hover {{
        background-color: #00E8BB;
    }}

    QPushButton[class="primary"]:disabled {{
        background-color: #1A3A32;
        color: {Colors.TEXT_MUTED};
    }}

    QPushButton[class="danger"] {{
        background-color: transparent;
        color: {Colors.ACCENT_DANGER};
        border: 1px solid {Colors.ACCENT_DANGER};
    }}

    QPushButton[class="danger"]:hover {{
        background-color: {Colors.GLOW_DANGER};
    }}

    QPushButton[class="success"] {{
        background-color: {Colors.ACCENT_SUCCESS};
        color: {Colors.BG_PRIMARY};
        border: none;
    }}

    QPushButton[class="big"] {{
        font-size: 20px;
        padding: 24px 48px;
        border-radius: 16px;
        min-width: 200px;
    }}

    /* ── Scroll Areas ───────────────────────────────────── */
    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: {Colors.BG_SECONDARY};
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.BORDER_LIGHT};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.TEXT_MUTED};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    /* ── Line Edits ─────────────────────────────────────── */
    QLineEdit {{
        background-color: {Colors.BG_TERTIARY};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
    }}

    QLineEdit:focus {{
        border-color: {Colors.ACCENT_PRIMARY};
    }}

    /* ── Frames / Cards ─────────────────────────────────── */
    QFrame[class="card"] {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 16px;
        padding: 20px;
    }}

    QFrame[class="divider"] {{
        background-color: {Colors.BORDER};
        max-height: 1px;
        min-height: 1px;
    }}

    /* ── Dialog ──────────────────────────────────────────── */
    QDialog {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER};
        border-radius: 16px;
    }}

    /* ── Message Box ────────────────────────────────────── */
    QMessageBox {{
        background-color: {Colors.BG_SECONDARY};
    }}

    QMessageBox QLabel {{
        color: {Colors.TEXT_PRIMARY};
        font-size: 14px;
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    """
