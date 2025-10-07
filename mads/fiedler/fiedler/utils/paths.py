"""Path resolution utilities."""
import os
from pathlib import Path


def get_config_path() -> Path:
    """
    Get path to config/models.yaml.

    Supports:
    1. FIEDLER_CONFIG environment variable override
    2. Installed package (via importlib.resources)
    3. Development repo layout (fallback)

    Returns:
        Path to models.yaml config file
    """
    # Priority 1: Environment variable override
    override = os.getenv("FIEDLER_CONFIG")
    if override:
        config_path = Path(override).expanduser().resolve()
        if config_path.exists():
            return config_path
        raise FileNotFoundError(f"FIEDLER_CONFIG points to non-existent file: {config_path}")

    # Priority 2: Installed package resources
    try:
        from importlib.resources import files
        config_path = Path(str(files("fiedler").joinpath("config/models.yaml")))
        if config_path.exists():
            return config_path
    except Exception:
        pass  # Fall through to development layout

    # Priority 3: Development repo layout (fallback)
    dev_config = Path(__file__).resolve().parents[2] / "config" / "models.yaml"
    if dev_config.exists():
        return dev_config

    raise FileNotFoundError(
        "Could not find models.yaml. Set FIEDLER_CONFIG environment variable or "
        "ensure fiedler is properly installed."
    )
