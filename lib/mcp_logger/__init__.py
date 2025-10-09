"""
Joshua MCP Logger Package.

Exposes the primary `log_to_godot` function for easy import.
"""
from .mcp_logger import log_to_godot
from .version import __version__

__all__ = ["log_to_godot", "__version__"]
