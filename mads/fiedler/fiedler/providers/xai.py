"""xAI (Grok) provider implementation via subprocess."""
import os
import subprocess
import asyncio
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
        # Store api_key_env for lazy loading in async context
        self.api_key_env = api_key_env
        self.api_key = None

    async def _send_impl(
        self,
        package: str,
        prompt: str,
        output_file: Path,
        logger,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        # Lazy-load API key on first use (async context)
        if not self.api_key:
            self.api_key = await get_api_key("xai", self.api_key_env)
            if not self.api_key:
                raise ValueError(
                    f"No API key found for xAI. Set via fiedler_set_key or environment variable {self.api_key_env}"
                )

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

            # FIXED: Use async subprocess for non-blocking execution
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout + 50
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("grok_client.py timed out")

            stderr = stderr_bytes.decode()
            if process.returncode != 0:
                raise RuntimeError(f"grok_client.py failed: {stderr}")

            result_stdout = stdout_bytes.decode()

            # Write output
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result_stdout)

            # Estimate tokens (Grok wrapper doesn't return usage)
            tokens = {
                "prompt": estimate_tokens(full_input, self.model_id),
                "completion": estimate_tokens(result_stdout, self.model_id),
            }

            return {"tokens": tokens}

        finally:
            # Cleanup temp file (if we created one)
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink()
