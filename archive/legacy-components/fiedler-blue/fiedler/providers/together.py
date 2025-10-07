"""Together.AI provider implementation."""
from pathlib import Path
from typing import Dict, Any

from openai import OpenAI

from .base import BaseProvider
from ..utils.secrets import get_api_key


class TogetherProvider(BaseProvider):
    """Provider for Together.AI models (Llama, DeepSeek, Qwen, etc.)."""

    def __init__(self, model_id: str, config: Dict[str, Any], api_key_env: str, base_url: str):
        super().__init__(model_id, config)
        # Check keyring first, then env var
        api_key = get_api_key("together", api_key_env)
        if not api_key:
            raise ValueError(
                f"No API key found for Together.AI. Set via fiedler_set_key or environment variable {api_key_env}"
            )
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _send_impl(self, package: str, prompt: str, output_file: Path, logger) -> Dict[str, Any]:
        # Combine prompt and package
        full_input = f"{prompt}\n\n{package}" if package else prompt

        # Call Together.AI API (OpenAI-compatible)
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": full_input}],
            max_tokens=self.max_completion_tokens,  # Completion budget, not context window
            timeout=self.timeout,
        )

        # Extract content
        content = response.choices[0].message.content

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Extract token usage (Together.AI provides this)
        tokens = {
            "prompt": response.usage.prompt_tokens if response.usage else 0,
            "completion": response.usage.completion_tokens if response.usage else 0,
        }

        return {"tokens": tokens}
