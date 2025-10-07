# src/utils/logger.py
import logging
import sys
import json
import asyncio
import websockets
from ..config import config

# Standard Python Logger Setup
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("horace")

# Godot MCP Logger Integration
async def log_to_godot(level: str, message: str, context: dict = None):
    """
    Sends a log message to the Godot MCP server.
    This is a mock implementation; a real implementation might use a persistent
    client or a more robust connection handling mechanism.
    """
    log_entry = {
        "tool": "godot_log",
        "params": {
            "source": "horace",
            "level": level.upper(),
            "message": message,
            "context": context or {}
        }
    }
    try:
        async with websockets.connect(config.GODOT_MCP_URL) as websocket:
            await websocket.send(json.dumps(log_entry))
            # In a real scenario, you might want to await a confirmation
    except Exception as e:
        logger.error(f"Failed to send log to Godot: {e}")

# Wrapper functions for different log levels
async def godot_info(message, context=None):
    await log_to_godot("info", message, context)
    logger.info(message)

async def godot_warn(message, context=None):
    await log_to_godot("warning", message, context)
    logger.warning(message)

async def godot_error(message, context=None):
    await log_to_godot("error", message, context)
    logger.error(message)
