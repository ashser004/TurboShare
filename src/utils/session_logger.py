import logging
import time
from pathlib import Path

LOG_DIR = Path.home() / ".turboshare_logs"

class SessionLoggingManager:
    """Manages dedicated logging handlers for active file transfer sessions."""

    def __init__(self):
        self.current_handler = None
        self.current_log_path = None

    def start_session_logging(self) -> None:
        """Create a new file handler and attach it to the root logger."""
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            # Filename: LOGS_YYYYMMDD_HHMMSS.txt
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"LOGS_{timestamp}.txt"
            self.current_log_path = LOG_DIR / filename

            # Configure and add the new file handler
            self.current_handler = logging.FileHandler(self.current_log_path, encoding="utf-8")
            self.current_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s  %(levelname)-7s  %(name)-28s  %(message)s",
                datefmt="%H:%M:%S",
            )
            self.current_handler.setFormatter(formatter)
            logging.getLogger().addHandler(self.current_handler)
            logging.info("Session log file created: %s", filename)
        except Exception as e:
            logging.error("Failed to start session logging: %s", e)

    def stop_session_logging(self) -> None:
        """Detach the current file handler from the root logger and close it."""
        if self.current_handler:
            try:
                logging.info("Session logging stopped.")
                logging.getLogger().removeHandler(self.current_handler)
                self.current_handler.close()
            except Exception as e:
                logging.error("Error closing session logging handler: %s", e)
            finally:
                self.current_handler = None
                self.current_log_path = None
