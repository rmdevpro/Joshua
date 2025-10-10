"""OpenAI provider implementation."""
from pathlib import Path
from typing import Dict, Any, Optional, List

from openai import OpenAI

from .base import BaseProvider
from ..utils.secrets import get_api_key


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models (GPT-4o, GPT-5, etc.)."""

    def __init__(self, model_id: str, config: Dict[str, Any], api_key_env: str):
        super().__init__(model_id, config)
        # Check keyring first, then env var
        api_key = get_api_key("openai", api_key_env)
        if not api_key:
            raise ValueError(
                f"No API key found for OpenAI. Set via fiedler_set_key or environment variable {api_key_env}"
            )
        self.client = OpenAI(api_key=api_key)

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

        # Call OpenAI API
        # Note: GPT-5 and o-series models use max_completion_tokens parameter name
        # Other models still use max_tokens, so we check the model name
        if "gpt-5" in self.model_id or self.model_id.startswith("o-") or self.model_id.startswith("o1-"):
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": full_input}],
                max_completion_tokens=self.max_completion_tokens,  # GPT-5/o-series parameter name
                timeout=self.timeout,
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": full_input}],
                max_tokens=self.max_completion_tokens,  # Legacy parameter name for GPT-4o, etc.
                timeout=self.timeout,
            )

        # Extract content
        content = response.choices[0].message.content

        # Debug: Log content info
        await logger.log("DEBUG", f"Content type: {type(content)}, length: {len(content) if content else 0}", "fiedler-providers", data={"model": self.model_id})
        if not content:
            await logger.log("WARN", f"Empty content! Response: {response}", "fiedler-providers", data={"model": self.model_id})

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            if content:
                f.write(content)
            else:
                await logger.log("ERROR", "Content is None or empty, writing empty file", "fiedler-providers", data={"model": self.model_id})

        # Extract token usage
        tokens = {
            "prompt": response.usage.prompt_tokens if response.usage else 0,
            "completion": response.usage.completion_tokens if response.usage else 0,
        }

        return {"tokens": tokens}
