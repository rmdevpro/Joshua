# src/mcp_server_v2.py
"""
Horace MCP Server v2 - Using iccm-network standard library

This version replaces custom WebSocket handling with the standardized
iccm-network library, eliminating network connectivity issues.

Migration from custom protocol to JSON-RPC 2.0 MCP standard.
"""

import asyncio
import signal

from iccm_network import MCPServer, MCPToolError

from .config import config, Config
from .database import Database
from .tools import Tools
from .utils.logger import logger, godot_info, godot_error
from .exceptions import HoraceError, DuplicateFileError

# Global instances
db = Database()
tools: Tools


# Tool Definitions (MCP Schema Format)
TOOL_DEFINITIONS = {
    "horace_register_file": {
        "description": "Register a file with metadata for version control and tracking",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to register"
                },
                "metadata": {
                    "type": "object",
                    "description": "File metadata",
                    "properties": {
                        "owner": {"type": "string", "description": "File owner"},
                        "purpose": {"type": "string", "description": "Purpose of the file"},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                        "collection": {"type": "string", "description": "Collection name"},
                        "correlation_id": {"type": "string", "description": "Optional correlation ID"}
                    }
                }
            },
            "required": ["file_path", "metadata"]
        }
    },

    "horace_search_files": {
        "description": "Search for files by various criteria",
        "inputSchema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Filter by owner"},
                "purpose": {"type": "string", "description": "Filter by purpose"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags"},
                "collection": {"type": "string", "description": "Filter by collection name"},
                "mime_type": {"type": "string", "description": "Filter by MIME type"},
                "limit": {"type": "integer", "default": 50, "description": "Maximum results"},
                "offset": {"type": "integer", "default": 0, "description": "Offset for pagination"}
            }
        }
    },

    "horace_get_file_info": {
        "description": "Get detailed information about a specific file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "UUID of the file"
                },
                "include_versions": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include version history"
                }
            },
            "required": ["file_id"]
        }
    },

    "horace_create_collection": {
        "description": "Create a new collection for organizing files",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Collection name"
                },
                "description": {
                    "type": "string",
                    "description": "Collection description"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata"
                },
                "file_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File IDs to add to collection"
                }
            },
            "required": ["name"]
        }
    },

    "horace_list_collections": {
        "description": "List all collections with pagination",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50, "description": "Maximum results"},
                "offset": {"type": "integer", "default": 0, "description": "Offset for pagination"}
            }
        }
    },

    "horace_update_file": {
        "description": "Update file metadata or check for content changes",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "UUID of the file"
                },
                "check_for_changes": {
                    "type": "boolean",
                    "default": False,
                    "description": "Check if file content has changed and create new version"
                },
                "metadata": {
                    "type": "object",
                    "description": "Metadata to update",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "purpose": {"type": "string"},
                        "status": {"type": "string"},
                        "collection": {"type": "string"}
                    }
                }
            },
            "required": ["file_id"]
        }
    },

    "horace_restore_version": {
        "description": "Restore a file to a previous version",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "UUID of the file"
                },
                "version": {
                    "type": "integer",
                    "description": "Version number to restore to"
                }
            },
            "required": ["file_id", "version"]
        }
    }
}


# Tool Handlers (Wrappers for Tools class methods)

async def register_file_handler(file_path: str, metadata: dict) -> dict:
    """Handler for horace_register_file tool."""
    try:
        return await tools.horace_register_file({"file_path": file_path, "metadata": metadata})
    except DuplicateFileError as e:
        # Per spec, return existing ID as success
        await godot_info(f"Duplicate file: {e.message}", context={"file_id": e.file_id})
        return {"file_id": e.file_id, "duplicate": True, "message": e.message}
    except HoraceError as e:
        await godot_error(f"Horace Error in register_file: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except FileNotFoundError as e:
        raise MCPToolError(str(e), code=-32602)  # Invalid params
    except Exception as e:
        await godot_error(f"Unexpected error in register_file: {e}")
        raise


async def search_files_handler(**kwargs) -> dict:
    """Handler for horace_search_files tool."""
    try:
        return await tools.horace_search_files(kwargs)
    except HoraceError as e:
        await godot_error(f"Horace Error in search_files: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in search_files: {e}")
        raise


async def get_file_info_handler(file_id: str, include_versions: bool = False) -> dict:
    """Handler for horace_get_file_info tool."""
    try:
        return await tools.horace_get_file_info({"file_id": file_id, "include_versions": include_versions})
    except FileNotFoundError as e:
        raise MCPToolError(str(e), code=-32602)  # Invalid params
    except HoraceError as e:
        await godot_error(f"Horace Error in get_file_info: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in get_file_info: {e}")
        raise


async def create_collection_handler(name: str, description: str = None, metadata: dict = None, file_ids: list = None) -> dict:
    """Handler for horace_create_collection tool."""
    try:
        params = {"name": name}
        if description is not None:
            params["description"] = description
        if metadata is not None:
            params["metadata"] = metadata
        if file_ids is not None:
            params["file_ids"] = file_ids
        return await tools.horace_create_collection(params)
    except HoraceError as e:
        await godot_error(f"Horace Error in create_collection: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in create_collection: {e}")
        raise


async def list_collections_handler(limit: int = 50, offset: int = 0) -> dict:
    """Handler for horace_list_collections tool."""
    try:
        return await tools.horace_list_collections({"limit": limit, "offset": offset})
    except HoraceError as e:
        await godot_error(f"Horace Error in list_collections: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in list_collections: {e}")
        raise


async def update_file_handler(file_id: str, check_for_changes: bool = False, metadata: dict = None) -> dict:
    """Handler for horace_update_file tool."""
    try:
        params = {"file_id": file_id, "check_for_changes": check_for_changes}
        if metadata is not None:
            params["metadata"] = metadata
        return await tools.horace_update_file(params)
    except FileNotFoundError as e:
        raise MCPToolError(str(e), code=-32602)  # Invalid params
    except HoraceError as e:
        await godot_error(f"Horace Error in update_file: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in update_file: {e}")
        raise


async def restore_version_handler(file_id: str, version: int) -> dict:
    """Handler for horace_restore_version tool."""
    try:
        return await tools.horace_restore_version({"file_id": file_id, "version": version})
    except FileNotFoundError as e:
        raise MCPToolError(str(e), code=-32602)  # Invalid params
    except HoraceError as e:
        await godot_error(f"Horace Error in restore_version: {e.message}", context={"error_code": e.error_code})
        raise MCPToolError(e.message, code=-32000, data={"error_code": e.error_code})
    except Exception as e:
        await godot_error(f"Unexpected error in restore_version: {e}")
        raise


# Tool Handlers Map
TOOL_HANDLERS = {
    "horace_register_file": register_file_handler,
    "horace_search_files": search_files_handler,
    "horace_get_file_info": get_file_info_handler,
    "horace_create_collection": create_collection_handler,
    "horace_list_collections": list_collections_handler,
    "horace_update_file": update_file_handler,
    "horace_restore_version": restore_version_handler
}


async def main():
    """Main entry point for Horace MCP Server v2."""
    global tools

    # Initialize storage directories
    Config.initialize_storage_dirs()
    logger.info("Storage directories initialized.")

    # Initialize database connection
    await db.connect()
    tools = Tools(db)

    # Create MCP server using iccm-network library
    server = MCPServer(
        name="horace",
        version="2.0.0",  # v2 uses iccm-network
        port=config.MCP_PORT,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS,
        logger=logger  # Use Horace's existing logger
    )

    await godot_info("Horace MCP Server v2 starting (using iccm-network)")

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def signal_handler():
        if not stop.done():
            stop.set_result(None)

    loop.add_signal_handler(signal.SIGTERM, signal_handler)
    loop.add_signal_handler(signal.SIGINT, signal_handler)

    # Start server (runs forever until signal)
    server_task = asyncio.create_task(server.start())

    # Wait for shutdown signal
    await stop

    # Graceful shutdown
    logger.info("Horace MCP Server v2 shutting down...")
    await godot_info("Horace MCP Server v2 shutting down.")

    # Stop server
    await server.stop()

    # Disconnect database
    await db.disconnect()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received exit signal.")
    finally:
        logger.info("Horace MCP Server v2 stopped.")
