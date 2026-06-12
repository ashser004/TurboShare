"""
TurboShare — File type → icon emoji mapping.

Maps file extensions to emoji icons for display in file lists.
Used by both the desktop UI and the mobile web UI.
"""

_ICON_MAP = {
    # Images
    ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
    ".bmp": "🖼️", ".webp": "🖼️", ".svg": "🖼️", ".ico": "🖼️",
    ".heic": "🖼️", ".heif": "🖼️", ".raw": "🖼️", ".tiff": "🖼️",

    # Videos
    ".mp4": "🎬", ".mkv": "🎬", ".avi": "🎬", ".mov": "🎬",
    ".wmv": "🎬", ".flv": "🎬", ".webm": "🎬", ".m4v": "🎬",

    # Audio
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".aac": "🎵",
    ".ogg": "🎵", ".wma": "🎵", ".m4a": "🎵",

    # Documents
    ".pdf": "📄", ".doc": "📝", ".docx": "📝", ".txt": "📃",
    ".rtf": "📝", ".odt": "📝",

    # Spreadsheets
    ".xls": "📊", ".xlsx": "📊", ".csv": "📊", ".ods": "📊",

    # Presentations
    ".ppt": "📽️", ".pptx": "📽️", ".odp": "📽️",

    # Archives
    ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦",
    ".gz": "📦", ".bz2": "📦", ".xz": "📦",

    # Code
    ".py": "🐍", ".js": "⚡", ".html": "🌐", ".css": "🎨",
    ".java": "☕", ".cpp": "⚙️", ".c": "⚙️", ".rs": "🦀",
    ".go": "🔵", ".ts": "⚡", ".json": "📋", ".xml": "📋",

    # Executables
    ".exe": "⚙️", ".msi": "⚙️", ".dmg": "⚙️", ".deb": "⚙️",
    ".apk": "📱", ".app": "📱",

    # Misc
    ".iso": "💿", ".img": "💿",
}

_DEFAULT_ICON = "📁"


def get_file_icon(filename: str) -> str:
    """Return an emoji icon for the given filename based on extension."""
    ext = ""
    dot_pos = filename.rfind(".")
    if dot_pos != -1:
        ext = filename[dot_pos:].lower()
    return _ICON_MAP.get(ext, _DEFAULT_ICON)


def get_file_icon_map() -> dict:
    """Return the full icon map (used by mobile UI via API)."""
    return dict(_ICON_MAP)
