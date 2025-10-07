"""Base provider abstraction with retry logic."""
import time
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model_id: str, config: Dict[str, Any]):
        """
        Initialize provider.

        Args:
            model_id: Canonical model ID
            config: Model configuration dict (timeout, retry_attempts, max_tokens, max_completion_tokens, etc.)
        """
        self.model_id = model_id
        self.timeout = config.get("timeout", 600)
        self.retry_attempts = config.get("retry_attempts", 3)
        # Context window (total tokens: input + completion)
        self.context_window = config.get("max_tokens", 8192)
        # Max completion tokens (output budget)
        self.max_completion_tokens = config.get("max_completion_tokens", 4096)

    def send(self, package: str, prompt: str, output_file: Path, logger) -> Dict[str, Any]:
        """
        Send request to model with retry logic.

        Args:
            package: Compiled document package
            prompt: User prompt
            output_file: Path to write response
            logger: ProgressLogger instance

        Returns:
            Dict with success, duration, output_file, output_size, tokens, error (if failed)
        """
        start_time = time.time()

        for attempt in range(self.retry_attempts):
            try:
                logger.log(f"Attempt {attempt + 1}/{self.retry_attempts}", self.model_id)
                result = self._send_impl(package, prompt, output_file, logger)
                duration = time.time() - start_time
                return {
                    "success": True,
                    "duration": round(duration, 2),
                    "output_file": str(output_file),
                    "output_size": output_file.stat().st_size if output_file.exists() else 0,
                    "tokens": result.get("tokens", {"prompt": 0, "completion": 0}),
                }
            except Exception as e:
                error_msg = str(e)
                logger.log(f"❌ Error: {error_msg}", self.model_id)

                if attempt < self.retry_attempts - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.log(f"Retrying in {wait_time}s...", self.model_id)
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    duration = time.time() - start_time
                    return {
                        "success": False,
                        "duration": round(duration, 2),
                        "output_file": None,
                        "output_size": 0,
                        "tokens": {"prompt": 0, "completion": 0},
                        "error": error_msg,
                    }

    @abstractmethod
    def _send_impl(self, package: str, prompt: str, output_file: Path, logger) -> Dict[str, Any]:
        """
        Concrete implementation of send logic.

        Must write response to output_file and return dict with optional 'tokens' key.

        Args:
            package: Compiled document package
            prompt: User prompt
            output_file: Path to write response
            logger: ProgressLogger instance

        Returns:
            Dict with optional 'tokens' key: {"tokens": {"prompt": int, "completion": int}}

        Raises:
            Exception: On any error (will trigger retry)
        """
        pass
