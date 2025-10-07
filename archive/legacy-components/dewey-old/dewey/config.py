# dewey/config.py
"""
Configuration management for the Dewey MCP Server.

Loads settings from environment variables with sensible defaults.
"""
import os
import logging
import sys

# --- Database Configuration ---
DB_HOST = os.getenv("DEWEY_DB_HOST", "irina")
DB_PORT = int(os.getenv("DEWEY_DB_PORT", "5432"))
DB_NAME = os.getenv("DEWEY_DB_NAME", "winni")
DB_USER = os.getenv("DEWEY_DB_USER", "dewey")
DB_PASSWORD = os.getenv("DEWEY_DB_PASSWORD")

if not DB_PASSWORD:
    print("FATAL: DEWEY_DB_PASSWORD environment variable is not set.", file=sys.stderr)
    sys.exit(1)

# --- MCP Server Configuration ---
MCP_HOST = os.getenv("DEWEY_MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("DEWEY_MCP_PORT", "9020"))

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("DEWEY_LOG_LEVEL", "INFO").upper()

def setup_logging():
    """Configures the root logger for the application."""
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    # Silence noisy libraries
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

# --- Connection Pool Configuration ---
DB_POOL_MIN_CONN = int(os.getenv("DEWEY_DB_MIN_CONNECTIONS", "2"))
DB_POOL_MAX_CONN = int(os.getenv("DEWEY_DB_MAX_CONNECTIONS", "10"))

# Initialize logging when the module is imported
setup_logging()
