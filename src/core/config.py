"""
TurboShare — Application-wide constants and configuration.

All tunable parameters, file paths, and defaults are centralised here
so nothing is scattered across modules.
"""

import os
import sys
from pathlib import Path

# ── Application identity ────────────────────────────────────────────
APP_NAME = "TurboShare"
APP_VERSION = "1.1.0"

# ── Transfer engine ─────────────────────────────────────────────────
CHUNK_SIZE = 2_097_152                      # 2 MB per chunk
PARALLEL_CONNECTIONS = 4                    # concurrent HTTP streams
MAX_TRANSFER_SIZE = 30 * (1024 ** 3)        # 30 GB hard cap
TEMP_EXT = ".turbotemp"                     # in-progress file extension

# ── Networking ──────────────────────────────────────────────────────
PORT_RANGE_START = 49152
PORT_RANGE_END = 65535
SOCKET_BUFFER_SIZE = 4 * (1024 ** 2)        # 4 MB send/recv buffers

# ── Security ────────────────────────────────────────────────────────
TOKEN_LENGTH = 12                           # alphanumeric session token
PIN_LENGTH = 6                              # numeric PIN
MAX_PIN_ATTEMPTS = 3
PIN_RATE_LIMIT_SECONDS = 2                  # minimum gap between attempts
PIN_EXPIRY_SECONDS = 300                    # 5 min inactivity timeout

# ── Real-time data ──────────────────────────────────────────────────
SPEED_WINDOW_SECONDS = 2                    # rolling-average window
SPEED_UPDATE_INTERVAL_S = 1                 # refresh rate for UI
PROGRESS_SSE_INTERVAL_MS = 500              # mobile poll / SSE cadence

# ── MMAP threshold ──────────────────────────────────────────────────
MMAP_THRESHOLD = 2 * (1024 ** 3)            # 2 GB — above this use seek+read

# ── Paths ───────────────────────────────────────────────────────────

def _base_dir() -> Path:
    """Return the project root whether running from source or frozen exe."""
    if getattr(sys, "frozen", False):
        # PyInstaller --onedir: exe lives inside dist/TurboShare/
        return Path(getattr(sys, "_MEIPASS"))
    # Running from source: src/ is one level below project root
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = _base_dir()
ASSETS_DIR = BASE_DIR / "assets"
ANIMATIONS_DIR = ASSETS_DIR / "animations"
FONTS_DIR = ASSETS_DIR / "fonts"
JS_DIR = ASSETS_DIR / "js"
IMAGES_DIR = ASSETS_DIR / "images"
MOBILE_DIR = BASE_DIR / "mobile"

# Logo (user supplies this; used by QR page and installer)
LOGO_PATH = IMAGES_DIR / "logo.png"

# Default download location for receive mode
DEFAULT_SAVE_DIR = Path.home() / "Downloads"

# ── Lottie animation file map ──────────────────────────────────────
LOTTIE_FILES = {
    "waiting":       ANIMATIONS_DIR / "waiting.json",
    "transferring":  ANIMATIONS_DIR / "transferring.json",
    "success":       ANIMATIONS_DIR / "success.json",
    "error":         ANIMATIONS_DIR / "error.json",
    "connecting":    ANIMATIONS_DIR / "connecting.json",
}

# ── URL construction helper ─────────────────────────────────────────
SESSION_PATH_PREFIX = "/ts"

def build_session_url(ip: str, port: int, token: str) -> str:
    """Construct the full HTTP session URL."""
    return f"http://{ip}:{port}{SESSION_PATH_PREFIX}/{token}/"
