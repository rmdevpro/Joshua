"""Anthropic provider implementation."""
from pathlib import Path
from typing import Dict, Any

from anthropic import Anthropic

from .base import BaseProvider
from ..utils.secrets import get_api_key


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic models (Claude Opus, Sonnet, etc.)."""

    def __init__(self, model_id: str, config: Dict[str, Any], api_key_env: str):
        super().__init__(model_id, config)
        # Check keyring first, then env var
        api_key = get_api_key("anthropic", api_key_env)
        if not api_key:
            raise ValueError(
                f"No API key found for Anthropic. Set via fiedler_set_key or environment variable {api_key_env}"
            )
        self.client = Anthropic(api_key=api_key)

    def _send_impl(self, package: str, prompt: str, output_file: Path, logger) -> Dict[str, Any]:
        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}" if package else prompt

        # Call Anthropic API
        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=self.max_completion_tokens,
            messages=[{"role": "user", "content": full_input}],
            timeout=self.timeout,
        )

        # Extract content
        content = response.content[0].text if response.content else None

        # Debug: Log content info
        logger.log(f"Content type: {type(content)}, length: {len(content) if content else 0}", self.model_id)
        if not content:
            logger.log(f"WARNING: Empty content! Response: {response}", self.model_id)

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            if content:
                f.write(content)
            else:
                logger.log(f"ERROR: Content is None or empty, writing empty file", self.model_id)

        # Extract token usage
        tokens = {
            "prompt": response.usage.input_tokens if response.usage else 0,
            "completion": response.usage.output_tokens if response.usage else 0,
        }

        return {"tokens": tokens}
