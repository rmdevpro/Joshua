"""Fiedler MCP Server - joshua_network implementation."""
import asyncio
import json
import uuid
from typing import Any, Dict

from joshua_network import Server
from joshua_logger import Logger

# Import the actual tool functions to be wrapped or replaced
from .tools import (
    fiedler_list_models,
    fiedler_set_models,
    fiedler_set_output,
    fiedler_get_config,
    fiedler_send,
)
# Import the newly async secret management functions
from .utils.secrets import (
    set_api_key as set_api_key_async,
    delete_api_key as delete_api_key_async,
    list_stored_providers as list_stored_providers_async,
)

# Initialize joshua_logger for centralized logging
logger = Logger()


# Tool definitions for joshua_network
TOOL_DEFINITIONS = {
    "fiedler_list_models": {
        "description": "List all available LLM models with their properties (name, provider, aliases, max_tokens, capabilities).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "fiedler_set_models": {
        "description": "Configure default models for fiedler_send. Accepts list of model IDs or aliases.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of model IDs or aliases to use as defaults",
                },
            },
            "required": ["models"],
        },
    },
    "fiedler_set_output": {
        "description": "Configure output directory for fiedler_send results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output_dir": {
                    "type": "string",
                    "description": "Path to output directory",
                },
            },
            "required": ["output_dir"],
        },
    },
    "fiedler_get_config": {
        "description": "Get current Fiedler configuration (models, output_dir, total_available_models).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "fiedler_send": {
        "description": "Send prompt and optional package files to configured LLMs. Returns a correlation_id immediately.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "User prompt or question to send to models",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths to compile into package",
                },
                "models": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional override of default models (use model IDs or aliases)",
                },
            },
            "required": ["prompt"],
        },
    },
    "fiedler_set_key": {
        "description": "Store API key securely in system keyring (encrypted). Replaces need for environment variables.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider name: google, openai, together, or xai",
                },
                "api_key": {
                    "type": "string",
                    "description": "API key to store (will be encrypted by OS keyring)",
                },
            },
            "required": ["provider", "api_key"],
        },
    },
    "fiedler_delete_key": {
        "description": "Delete stored API key from system keyring.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Provider name: google, openai, together, or xai",
                },
            },
            "required": ["provider"],
        },
    },
    "fiedler_list_keys": {
        "description": "List providers that have API keys stored in system keyring.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


# Tool handlers - wrap the actual tool functions
async def handle_list_models() -> Dict[str, Any]:
    """Handle fiedler_list_models tool call."""
    result = fiedler_list_models()
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_set_models(models: list) -> Dict[str, Any]:
    """Handle fiedler_set_models tool call."""
    result = fiedler_set_models(models)
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_set_output(output_dir: str) -> Dict[str, Any]:
    """Handle fiedler_set_output tool call."""
    result = fiedler_set_output(output_dir)
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_get_config() -> Dict[str, Any]:
    """Handle fiedler_get_config tool call."""
    result = fiedler_get_config()
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_send(prompt: str, files: list = None, models: list = None) -> Dict[str, Any]:
    """
    Handle fiedler_send tool call.
    FIXED: Returns immediately and runs the LLM calls in the background.
    """
    correlation_id = str(uuid.uuid4())[:8]
    await logger.log(
        "INFO",
        f"Received fiedler_send request, creating background task.",
        "fiedler-mcp",
        data={"correlation_id": correlation_id, "prompt_len": len(prompt)}
    )

    # Run fiedler_send in the background, don't await it here.
    asyncio.create_task(fiedler_send(
        prompt=prompt,
        files=files,
        models=models,
        correlation_id=correlation_id  # Pass the generated ID
    ))

    # Return immediately with the correlation_id
    response_data = {
        "status": "pending",
        "correlation_id": correlation_id,
        "message": "Fiedler 'send' task started. Results will be saved to the configured output directory."
    }
    return {"content": [{"type": "text", "text": json.dumps(response_data, indent=2)}]}


async def handle_set_key(provider: str, api_key: str) -> Dict[str, Any]:
    """
    Handle fiedler_set_key tool call.
    FIXED: Calls the async version of the function.
    """
    try:
        await set_api_key_async(provider, api_key)
        result = {"status": "success", "message": f"API key for '{provider}' was stored successfully."}
    except Exception as e:
        await logger.log("ERROR", f"Failed to set API key for {provider}: {e}", "fiedler-mcp")
        result = {"status": "error", "message": str(e)}
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_delete_key(provider: str) -> Dict[str, Any]:
    """
    Handle fiedler_delete_key tool call.
    FIXED: Calls the async version of the function.
    """
    try:
        deleted = await delete_api_key_async(provider)
        if deleted:
            message = f"API key for '{provider}' was deleted."
        else:
            message = f"No API key found for '{provider}' to delete."
        result = {"status": "success", "message": message}
    except Exception as e:
        await logger.log("ERROR", f"Failed to delete API key for {provider}: {e}", "fiedler-mcp")
        result = {"status": "error", "message": str(e)}
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


async def handle_list_keys() -> Dict[str, Any]:
    """
    Handle fiedler_list_keys tool call.
    FIXED: Calls the async version of the function.
    """
    try:
        providers = await list_stored_providers_async()
        result = {"status": "success", "providers_with_keys": providers}
    except Exception as e:
        await logger.log("ERROR", f"Failed to list stored keys: {e}", "fiedler-mcp")
        result = {"status": "error", "message": str(e)}
    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


# Tool handlers mapping
TOOL_HANDLERS = {
    "fiedler_list_models": handle_list_models,
    "fiedler_set_models": handle_set_models,
    "fiedler_set_output": handle_set_output,
    "fiedler_get_config": handle_get_config,
    "fiedler_send": handle_send,
    "fiedler_set_key": handle_set_key,
    "fiedler_delete_key": handle_delete_key,
    "fiedler_list_keys": handle_list_keys,
}


async def _amain():
    """Main entry point for Fiedler MCP server using joshua_network."""
    await logger.log("INFO", "Fiedler MCP server starting with joshua_network", "fiedler-mcp", data={"version": "1.0.0"})

    # Create joshua_network server
    server = Server(
        name="fiedler",
        version="1.0.0",
        port=8080,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    # Start HTTP streaming proxy in parallel
    from .proxy_server import start_proxy_server
    proxy_task = asyncio.create_task(start_proxy_server())

    # Start joshua_network WebSocket server
    await logger.log("INFO", "Fiedler WebSocket server operational", "fiedler-mcp", data={"host": "0.0.0.0", "port": 8080})
    await server.start()


def main():
    """Entry point for the module."""
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
