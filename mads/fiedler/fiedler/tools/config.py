"""Configuration management tools."""
import yaml
from pathlib import Path
from typing import Dict, Any, List

from ..utils import get_models, get_output_dir, set_models as save_models, set_output_dir as save_output_dir
from .models import build_alias_map


def fiedler_set_models(models: List[str]) -> Dict[str, Any]:
    """
    Configure default models for fiedler_send.

    Args:
        models: List of model IDs or aliases

    Returns:
        Dict with status, resolved models, message
    """
    # Load config for alias resolution
    from ..utils.paths import get_config_path
    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    alias_map = build_alias_map(config)

    # Resolve aliases to canonical model IDs
    resolved = []
    for model in models:
        if model in alias_map:
            resolved.append(alias_map[model])
        else:
            raise ValueError(f"Unknown model or alias: {model}")

    # Save to state
    save_models(resolved)

    return {
        "status": "configured",
        "models": resolved,
        "message": f"Default models updated ({len(resolved)} models configured)"
    }


def fiedler_set_output(output_dir: str) -> Dict[str, Any]:
    """
    Configure output directory for fiedler_send.

    Args:
        output_dir: Path to output directory

    Returns:
        Dict with status, output_dir, message
    """
    # Normalize path (expand ~, resolve relative paths)
    normalized_path = str(Path(output_dir).expanduser().resolve())
    save_output_dir(normalized_path)

    return {
        "status": "configured",
        "output_dir": normalized_path,
        "message": "Output directory updated"
    }


def fiedler_get_config() -> Dict[str, Any]:
    """
    Get current Fiedler configuration.

    Returns:
        Dict with models, output_dir, total_available_models
    """
    # Get current state
    current_models = get_models()
    current_output_dir = get_output_dir()

    # Count available models
    from ..utils.paths import get_config_path
    config_path = get_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    total_models = sum(
        len(provider_config["models"])
        for provider_config in config["providers"].values()
    )

    return {
        "models": current_models,
        "output_dir": current_output_dir,
        "total_available_models": total_models
    }
