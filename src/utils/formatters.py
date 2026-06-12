"""
TurboShare — Human-readable formatters.

Utility functions for formatting file sizes, durations, and speeds
in a user-friendly way.
"""


def format_size(size_bytes: int) -> str:
    """Format bytes into a human-readable string (e.g. '4.2 MB')."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"


def format_speed(mbps: float) -> str:
    """Format speed in MB/s."""
    if mbps < 0.1:
        return "0 MB/s"
    if mbps < 1:
        return f"{mbps * 1024:.0f} KB/s"
    return f"{mbps:.1f} MB/s"


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration."""
    if seconds < 0:
        return "calculating..."
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}m {s}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def format_eta(seconds: float) -> str:
    """Format estimated time remaining."""
    if seconds < 0:
        return "estimating..."
    return f"~{format_duration(seconds)} remaining"


def estimate_transfer_time(total_bytes: int, estimated_speed_mbps: float = 50.0) -> str:
    """Rough estimate of transfer time at a given WiFi speed."""
    if estimated_speed_mbps <= 0:
        return "unknown"
    seconds = total_bytes / (estimated_speed_mbps * 1024 * 1024)
    return format_duration(seconds)
