import json
from pathlib import Path

PREFS_PATH = Path.home() / ".turboshare_prefs.json"

def load_safe_transfer_setting() -> bool:
    """Load the safe transfer preference from the configuration file.

    Defaults to True if the file does not exist or fails to parse.
    """
    if PREFS_PATH.is_file():
        try:
            with open(PREFS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("safe_transfer", True))
        except Exception:
            pass
    return True

def save_safe_transfer_setting(enabled: bool) -> None:
    """Save the safe transfer preference to the configuration file."""
    try:
        PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PREFS_PATH, "w", encoding="utf-8") as f:
            json.dump({"safe_transfer": enabled}, f)
    except Exception:
        pass
