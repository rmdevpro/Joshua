"""Gemini provider implementation via subprocess."""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any

from .base import BaseProvider
from ..utils.tokens import estimate_tokens
from ..utils.secrets import get_api_key


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models via gemini_client.py wrapper."""

    def __init__(self, model_id: str, config: Dict[str, Any], api_key_env: str):
        super().__init__(model_id, config)
        # Check keyring first, then env var
        self.api_key = get_api_key("google", api_key_env)
        if not self.api_key:
            raise ValueError(
                f"No API key found for Google. Set via fiedler_set_key or environment variable {api_key_env}"
            )

    def _send_impl(self, package: str, prompt: str, output_file: Path, logger) -> Dict[str, Any]:
        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}" if package else prompt

        # Get required client paths from environment (no defaults for portability)
        gemini_client = os.getenv("FIEDLER_GEMINI_CLIENT")
        python_bin = os.getenv("FIEDLER_GEMINI_PYTHON")

        if not gemini_client:
            raise RuntimeError(
                "FIEDLER_GEMINI_CLIENT environment variable not set. "
                "Set it to the path of gemini_client.py (e.g., /path/to/gemini_client.py)"
            )
        if not python_bin:
            raise RuntimeError(
                "FIEDLER_GEMINI_PYTHON environment variable not set. "
                "Set it to the path of Python interpreter (e.g., /path/to/venv/bin/python)"
            )

        # Validate paths exist
        if not Path(gemini_client).exists():
            raise RuntimeError(f"Gemini client not found at {gemini_client}")
        if not Path(python_bin).exists():
            raise RuntimeError(f"Python interpreter not found at {python_bin}")

        # Call gemini_client.py via subprocess
        cmd = [
            python_bin,
            gemini_client,
            "--model", self.model_id,
            "--stdin"
        ]

        env = os.environ.copy()
        env["GEMINI_API_KEY"] = self.api_key

        # Get working directory from client path
        client_dir = Path(gemini_client).parent

        result = subprocess.run(
            cmd,
            input=full_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(client_dir),
            timeout=self.timeout + 50  # Give it a bit more time
        )

        if result.returncode != 0:
            raise RuntimeError(f"gemini_client.py failed: {result.stderr}")

        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)

        # Estimate tokens (Gemini wrapper doesn't return usage)
        tokens = {
            "prompt": estimate_tokens(full_input, self.model_id),
            "completion": estimate_tokens(result.stdout, self.model_id),
        }

        return {"tokens": tokens}
