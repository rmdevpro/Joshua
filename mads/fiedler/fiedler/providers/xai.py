"""xAI (Grok) provider implementation via subprocess."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import BaseProvider
from ..utils.tokens import estimate_tokens
from ..utils.secrets import get_api_key


class XAIProvider(BaseProvider):
    """Provider for xAI Grok models via grok_client.py wrapper."""

    def __init__(self, model_id: str, config: Dict[str, Any], api_key_env: str):
        super().__init__(model_id, config)
        # Check keyring first, then env var
        self.api_key = get_api_key("xai", api_key_env)
        if not self.api_key:
            raise ValueError(
                f"No API key found for xAI. Set via fiedler_set_key or environment variable {api_key_env}"
            )

    async def _send_impl(
        self,
        package: str,
        prompt: str,
        output_file: Path,
        logger,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}" if package else prompt

        # Get required client paths from environment (no defaults for portability)
        grok_client = os.getenv("FIEDLER_GROK_CLIENT")
        python_bin = os.getenv("FIEDLER_GROK_PYTHON")

        if not grok_client:
            raise RuntimeError(
                "FIEDLER_GROK_CLIENT environment variable not set. "
                "Set it to the path of grok_client.py (e.g., /path/to/grok_client.py)"
            )
        if not python_bin:
            raise RuntimeError(
                "FIEDLER_GROK_PYTHON environment variable not set. "
                "Set it to the path of Python interpreter (e.g., /path/to/venv/bin/python)"
            )

        # Validate paths exist
        if not Path(grok_client).exists():
            raise RuntimeError(f"Grok client not found at {grok_client}")
        if not Path(python_bin).exists():
            raise RuntimeError(f"Python interpreter not found at {python_bin}")

        try:
            # Call grok_client.py via subprocess
            # If we have a package, use --file with prompt as analysis instructions
            # Otherwise, just pass the prompt directly
            if package:
                # Write package to temp file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as temp_file:
                    temp_file.write(package)
                    temp_path = temp_file.name

                cmd = [
                    python_bin,
                    grok_client,
                    "--file", temp_path,
                    "--model", self.model_id,
                    "--max-tokens", str(self.max_completion_tokens),
                    prompt  # Analysis instructions for the file
                ]
            else:
                # No package, pass prompt directly
                temp_path = None
                cmd = [
                    python_bin,
                    grok_client,
                    "--model", self.model_id,
                    "--max-tokens", str(self.max_completion_tokens),
                    prompt  # Direct prompt
                ]

            env = os.environ.copy()
            env["XAI_API_KEY"] = self.api_key

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=self.timeout + 50
            )

            if result.returncode != 0:
                raise RuntimeError(f"grok_client.py failed: {result.stderr}")

            # Write output
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)

            # Estimate tokens (Grok wrapper doesn't return usage)
            tokens = {
                "prompt": estimate_tokens(full_input, self.model_id),
                "completion": estimate_tokens(result.stdout, self.model_id),
            }

            return {"tokens": tokens}

        finally:
            # Cleanup temp file (if we created one)
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink()
