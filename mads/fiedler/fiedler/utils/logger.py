"""Thread-safe progress logger for Fiedler."""
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional


class ProgressLogger:
    """Thread-safe logger writing to stderr and optional file."""

    def __init__(self, correlation_id: Optional[str] = None, log_file: Optional[Path] = None):
        self.lock = threading.Lock()
        self.correlation_id = correlation_id or "-"
        self.log_file = log_file

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"=== Fiedler Run {datetime.now().isoformat()} (cid={self.correlation_id}) ===\n\n")

    def log(self, message: str, model: Optional[str] = None) -> None:
        """Log a message to stderr and file."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [cid:{self.correlation_id[:8]}]"
        if model:
            prefix += f" [{model}]"

        full_message = f"{prefix} {message}\n"

        with self.lock:
            # Always write to stderr for real-time progress
            sys.stderr.write(full_message)
            sys.stderr.flush()

            # Optionally write to file
            if self.log_file:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(full_message)
