"""Thread-safe progress logger for Fiedler."""
import sys
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from joshua_logger import Logger


class ProgressLogger:
    """Thread-safe logger writing to joshua_logger and optional file."""

    def __init__(self, correlation_id: Optional[str] = None, log_file: Optional[Path] = None):
        self.lock = threading.Lock()
        self.correlation_id = correlation_id or "-"
        self.log_file = log_file
        self.logger = Logger()

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"=== Fiedler Run {datetime.now().isoformat()} (cid={self.correlation_id}) ===\n\n")

    async def log(self, level: str, message: str, component: str, data: Optional[dict] = None) -> None:
        """Log a message to joshua_logger and file."""
        # Build data dict with correlation_id
        log_data = {"correlation_id": self.correlation_id}
        if data:
            log_data.update(data)

        # Log to joshua_logger
        await self.logger.log(level, message, component, data=log_data)

        # Also write to local file for backward compatibility
        if self.log_file:
            timestamp = datetime.now().strftime("%H:%M:%S")
            model = data.get("model", "") if data else ""
            prefix = f"[{timestamp}] [cid:{self.correlation_id[:8]}]"
            if model:
                prefix += f" [{model}]"
            full_message = f"{prefix} {message}\n"

            with self.lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(full_message)
