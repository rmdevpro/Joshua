"""Gemini provider implementation via subprocess."""
import os
import subprocess
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import BaseProvider
from ..utils.tokens import estimate_tokens
from ..utils.secrets import get_api_key


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models via gemini_client.py wrapper."""

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
            self.api_key = await get_api_key("google", self.api_key_env)
            if not self.api_key:
                raise ValueError(
                    f"No API key found for Google. Set via fiedler_set_key or environment variable {self.api_key_env}"
                )

        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}" if package else prompt

        # Get required client paths from environment (no defaults for portability)
        gemini_client_path = os.getenv("FIEDLER_GEMINI_CLIENT")
        python_bin = os.getenv("FIEDLER_GEMINI_PYTHON")

        if not gemini_client_path:
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
        if not Path(gemini_client_path).exists():
            raise RuntimeError(f"Gemini client not found at {gemini_client_path}")
        if not Path(python_bin).exists():
            raise RuntimeError(f"Python interpreter not found at {python_bin}")

        # If attachments present, use direct API call via imported module
        if attachments:
            return await self._send_with_attachments(
                full_input, output_file, logger, gemini_client_path, attachments
            )

        # Otherwise use subprocess (backward compatibility, simpler for text-only)
        cmd = [
            python_bin,
            gemini_client_path,
            "--model", self.model_id,
            "--stdin"
        ]

        env = os.environ.copy()
        env["GEMINI_API_KEY"] = self.api_key

        # Get working directory from client path
        client_dir = Path(gemini_client_path).parent

        # FIXED: Use async subprocess for non-blocking execution
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=str(client_dir)
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=full_input.encode()),
                timeout=self.timeout + 50
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise RuntimeError("gemini_client.py timed out")

        stderr = stderr_bytes.decode()
        if process.returncode != 0:
            raise RuntimeError(f"gemini_client.py failed: {stderr}")

        result_stdout = stdout_bytes.decode()

        # Write output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result_stdout)

        # Estimate tokens (Gemini wrapper doesn't return usage)
        tokens = {
            "prompt": estimate_tokens(full_input, self.model_id),
            "completion": estimate_tokens(result_stdout, self.model_id),
        }

        return {"tokens": tokens}

    async def _send_with_attachments(
        self,
        prompt: str,
        output_file: Path,
        logger,
        gemini_client_path: str,
        attachments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send with multimodal attachments using direct API call."""
        # Import gemini_client module dynamically
        client_dir = Path(gemini_client_path).parent
        client_module = Path(gemini_client_path).stem

        # Add to sys.path if not already present
        if str(client_dir) not in sys.path:
            sys.path.insert(0, str(client_dir))

        try:
            # Dynamic import
            import importlib.util
            spec = importlib.util.spec_from_file_location(client_module, gemini_client_path)
            if not spec or not spec.loader:
                raise RuntimeError(f"Failed to load module spec from {gemini_client_path}")

            gemini_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gemini_module)

            # Create client instance
            client = gemini_module.GeminiClient(api_key=self.api_key)

            # Prepare attachments (extract only mime_type and data)
            gemini_attachments = [
                {"mime_type": att["mime_type"], "data": att["data"]}
                for att in attachments
            ]

            await logger.log("INFO", f"Sending {len(gemini_attachments)} attachment(s) natively to {self.model_id}", "fiedler-providers", data={"model": self.model_id})

            # Call API
            result = client.generate_content(
                prompt=prompt,
                model=self.model_id,
                attachments=gemini_attachments
            )

            if "error" in result:
                raise RuntimeError(f"Gemini API error: {result['error']}")

            # Write output
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.get("text", ""))

            # Use actual token counts if available, otherwise estimate
            usage = result.get("usage", {})
            tokens = {
                "prompt": usage.get("promptTokenCount", estimate_tokens(prompt, self.model_id)),
                "completion": usage.get("candidatesTokenCount", estimate_tokens(result.get("text", ""), self.model_id)),
            }

            return {"tokens": tokens}

        finally:
            # Clean up sys.path
            if str(client_dir) in sys.path:
                sys.path.remove(str(client_dir))
