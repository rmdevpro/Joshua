"""fiedler_list_models tool implementation."""
import yaml
from pathlib import Path
from typing import Dict, List, Any


def build_alias_map(config: Dict) -> Dict[str, str]:
    """Build map of alias -> canonical model ID."""
    alias_map = {}
    for provider_name, provider_config in config["providers"].items():
        for model_id, model_config in provider_config["models"].items():
            # Model ID maps to itself
            if model_id in alias_map:
                raise ValueError(
                    f"Duplicate model ID '{model_id}': already defined as {alias_map[model_id]}"
                )
            alias_map[model_id] = model_id

            # Each alias maps to model ID
            for alias in model_config.get("aliases", []):
                if alias in alias_map:
                    raise ValueError(
                        f"Duplicate alias '{alias}' for model '{model_id}': "
                        f"already maps to {alias_map[alias]}"
                    )
                alias_map[alias] = model_id
    return alias_map


def fiedler_list_models() -> Dict[str, Any]:
    """
    List all available models with their properties.

    Returns:
        Dict with 'models' key containing list of model info dicts
    """
    from ..utils.paths import get_config_path
    config_path = get_config_path()

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    models = []
    for provider_name, provider_config in config["providers"].items():
        for model_id, model_config in provider_config["models"].items():
            models.append({
                "name": model_id,
                "provider": provider_name,
                "aliases": model_config.get("aliases", []),
                "max_tokens": model_config.get("max_tokens", 8192),
                "capabilities": model_config.get("capabilities", ["text"]),
            })

    return {"models": models}
