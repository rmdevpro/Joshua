# src/config.py
import os
from pathlib import Path

class Config:
    # Database Configuration
    DB_HOST = os.getenv("HORACE_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("HORACE_DB_PORT", 5432))
    DB_NAME = os.getenv("HORACE_DB_NAME", "winni")
    DB_USER = os.getenv("HORACE_DB_USER", "horace")
    DB_PASSWORD = os.getenv("HORACE_DB_PASSWORD", "password")

    # Storage Configuration
    STORAGE_PATH = Path(os.getenv("HORACE_STORAGE_PATH", "/mnt/irina_storage"))
    FILES_DIR = STORAGE_PATH / "files"
    VERSIONS_DIR = STORAGE_PATH / ".horace_versions"
    
    VERSION_COUNT = int(os.getenv("HORACE_VERSION_COUNT", 5))

    # MCP Server Configuration
    MCP_HOST = os.getenv("HORACE_MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("HORACE_MCP_PORT", 8070))
    LOG_LEVEL = os.getenv("HORACE_LOG_LEVEL", "INFO").upper()

    # Godot Logging Integration
    GODOT_MCP_URL = os.getenv("GODOT_MCP_URL", "ws://godot-mcp:9060")

    # Ensure required directories exist
    @staticmethod
    def initialize_storage_dirs():
        Config.FILES_DIR.mkdir(parents=True, exist_ok=True)
        Config.VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
        (Config.STORAGE_PATH / ".horace_metadata").mkdir(exist_ok=True)
        # Create component subdirectories for convenience
        for component in ["gates", "playfair", "fiedler", "user", "shared"]:
            (Config.FILES_DIR / component).mkdir(exist_ok=True)

config = Config()
