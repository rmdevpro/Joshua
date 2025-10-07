"""State management for Fiedler configuration."""
import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from .paths import get_config_path


STATE_FILE = Path.home() / ".fiedler" / "state.yaml"


def load_state(config_path: Path) -> Dict:
    """
    Load state from ~/.fiedler/state.yaml or initialize from defaults.

    Args:
        config_path: Path to models.yaml config file

    Returns:
        Dict with 'models' and 'output_dir' keys
    """
    # Try to load existing state
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}
                if "models" in state and "output_dir" in state:
                    return state
        except Exception:
            pass  # Fall through to defaults

    # Load defaults from config
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    defaults = config.get("defaults", {})
    # Check environment variable first, then fall back to config
    default_output = os.getenv("FIEDLER_OUTPUT_DIR") or defaults.get("output_dir", "./fiedler_output")
    # Normalize default output path
    normalized_output = str(Path(default_output).expanduser().resolve())

    return {
        "models": defaults.get("models", ["gemini-2.5-pro", "gpt-5", "grok-4-0709"]),
        "output_dir": normalized_output
    }


def save_state(models: List[str], output_dir: str) -> None:
    """
    Save state to ~/.fiedler/state.yaml.

    Args:
        models: List of model IDs
        output_dir: Output directory path
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump({
            "models": models,
            "output_dir": output_dir
        }, f)


def get_models() -> List[str]:
    """Get current configured models."""
    config_path = get_config_path()
    state = load_state(config_path)
    return state["models"]


def get_output_dir() -> str:
    """Get current configured output directory."""
    config_path = get_config_path()
    state = load_state(config_path)
    return state["output_dir"]


def set_models(models: List[str]) -> None:
    """Set configured models."""
    output_dir = get_output_dir()
    save_state(models, output_dir)


def set_output_dir(output_dir: str) -> None:
    """Set configured output directory."""
    models = get_models()
    save_state(models, output_dir)
