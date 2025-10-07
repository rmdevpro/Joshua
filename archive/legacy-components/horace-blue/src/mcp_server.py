#!/usr/bin/env python3
# src/mcp_server.py
"""Horace MCP Server using iccm-network library."""

import asyncio
import sys
sys.path.insert(0, '/app')

from iccm_network import MCPServer

from .config import config, Config
from .database import Database
from .tools import Tools
from .utils.logger import logger
from .godot.mcp_logger import log_to_godot


# Global instances
db = Database()
tools_instance = None


# Tool definitions for MCP
TOOL_DEFINITIONS = {
    "horace_register_file": {
        "description": "Register a file with Horace catalog",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to file in /mnt/irina_storage/"
                },
                "metadata": {
                    "type": "object",
                    "description": "File metadata",
                    "properties": {
                        "owner": {"type": "string"},
                        "purpose": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "collection": {"type": "string"},
                        "correlation_id": {"type": "string"}
                    }
                }
            },
            "required": ["file_path", "metadata"]
        }
    },
    "horace_search_files": {
        "description": "Search file catalog by metadata",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tags": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "created_after": {"type": "string"},
                "created_before": {"type": "string"},
                "file_type": {"type": "string"},
                "min_size": {"type": "integer"},
                "max_size": {"type": "integer"},
                "collection": {"type": "string"},
                "status": {"type": "string"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            }
        }
    },
    "horace_get_file_info": {
        "description": "Get detailed metadata for specific file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "include_versions": {"type": "boolean"}
            },
            "required": ["file_id"]
        }
    },
    "horace_create_collection": {
        "description": "Create or update a file collection",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "file_ids": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"}
            },
            "required": ["name"]
        }
    },
    "horace_list_collections": {
        "description": "List all collections",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            }
        }
    },
    "horace_update_file": {
        "description": "Update file metadata or trigger re-versioning",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "metadata": {"type": "object"},
                "check_for_changes": {"type": "boolean"}
            },
            "required": ["file_id"]
        }
    },
    "horace_restore_version": {
        "description": "Restore a file to a previous version",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {"type": "string"},
                "version": {"type": "integer"}
            },
            "required": ["file_id", "version"]
        }
    }
}


# Tool handlers - just pass through to Tools methods
TOOL_HANDLERS = {
    "horace_register_file": lambda **kwargs: tools_instance.horace_register_file(kwargs),
    "horace_search_files": lambda **kwargs: tools_instance.horace_search_files(kwargs),
    "horace_get_file_info": lambda **kwargs: tools_instance.horace_get_file_info(kwargs),
    "horace_create_collection": lambda **kwargs: tools_instance.horace_create_collection(kwargs),
    "horace_list_collections": lambda **kwargs: tools_instance.horace_list_collections(kwargs),
    "horace_update_file": lambda **kwargs: tools_instance.horace_update_file(kwargs),
    "horace_restore_version": lambda **kwargs: tools_instance.horace_restore_version(kwargs)
}


async def main():
    """Main entry point for Horace MCP Server."""
    global tools_instance

    # Initialize storage directories
    Config.initialize_storage_dirs()
    logger.info("Storage directories initialized.")

    # Initialize database connection
    await db.connect()
    tools_instance = Tools(db)

    await log_to_godot('INFO', 'Horace MCP server starting', component='horace', data={'status': 'initializing'})

    # Create and start MCP server using iccm-network library
    server = MCPServer(
        name="horace-mcp-server",
        version="1.0.0",
        port=config.MCP_PORT,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    logger.info(f"Horace MCP Server starting on port {config.MCP_PORT}")
    await log_to_godot('INFO', 'Horace MCP server operational', component='horace', data={'port': config.MCP_PORT, 'tools': len(TOOL_DEFINITIONS)})

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await db.disconnect()
        await log_to_godot('INFO', 'Horace MCP server stopped', component='horace', data={'status': 'shutdown'})


if __name__ == "__main__":
    asyncio.run(main())
