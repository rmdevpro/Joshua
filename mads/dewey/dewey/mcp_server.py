# dewey/mcp_server.py
"""
WebSocket MCP server for Dewey using joshua_network.Server.
Migrated to standardized libraries for MCP protocol compliance.
"""
import asyncio
import json
import sys
from typing import Any, Dict

# Add joshua libraries to path
sys.path.insert(0, '/mnt/projects/Joshua/lib')
from joshua_network import Server
from joshua_logger import Logger

from dewey import config
from dewey.database import db_pool
from dewey import tools

# Initialize joshua_logger for centralized logging
logger = Logger()

# MCP tool definitions
TOOL_DEFINITIONS = {
    "dewey_get_conversation": {
        "description": "Retrieve all messages from a conversation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string", "description": "UUID of the conversation"}
            },
            "required": ["conversation_id"]
        }
    },
    "dewey_list_conversations": {
        "description": "List conversations with pagination and filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Optional session ID filter"},
                "limit": {"type": "integer", "description": "Maximum results (default 20)"},
                "offset": {"type": "integer", "description": "Number to skip (default 0)"},
                "sort_by": {"type": "string", "description": "Sort field: created_at or updated_at"}
            }
        }
    },
    "dewey_search": {
        "description": "Full-text search across all messages",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "session_id": {"type": "string", "description": "Optional session ID filter"},
                "start_date": {"type": "string", "description": "Optional start date (ISO format)"},
                "end_date": {"type": "string", "description": "Optional end date (ISO format)"},
                "limit": {"type": "integer", "description": "Maximum results (default 20)"},
                "offset": {"type": "integer", "description": "Number to skip (default 0)"}
            },
            "required": ["query"]
        }
    },
    "dewey_get_startup_context": {
        "description": "Get the active startup context or a specific one by name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Optional context name (defaults to active)"}
            }
        }
    },
    "dewey_list_startup_contexts": {
        "description": "List all available startup contexts",
        "inputSchema": {
            "type": "object",
            "properties": {
                "include_content": {"type": "boolean", "description": "Include full content (default false)"}
            }
        }
    },
    "dewey_query_logs": {
        "description": "Query logs with various filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trace_id": {"type": "string", "description": "Filter by trace ID"},
                "component": {"type": "string", "description": "Filter by component name"},
                "level": {"type": "string", "description": "Minimum log level (TRACE, DEBUG, INFO, WARN, ERROR)"},
                "start_time": {"type": "string", "description": "Start time filter (ISO format)"},
                "end_time": {"type": "string", "description": "End time filter (ISO format)"},
                "search": {"type": "string", "description": "Full-text search in message"},
                "limit": {"type": "integer", "description": "Maximum results (1-1000, default 100)"}
            }
        }
    },
    "dewey_get_log_stats": {
        "description": "Get statistics about the logs table",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
}


# Wrapper functions to adapt tools to joshua_network handler format
async def wrap_tool_handler(tool_name: str, **arguments):
    """
    Wrapper to call Dewey tools and format responses for MCP protocol.
    Logs tool calls and handles errors appropriately.
    """
    await logger.log('TRACE', f'Tool call: {tool_name}', 'dewey-mcp', data={'arguments': arguments})

    try:
        # Get the tool function from tools module
        tool_func = getattr(tools, tool_name, None)
        if not tool_func or not callable(tool_func):
            raise tools.ToolError(f"Tool not found: {tool_name}", code=-32601)

        # Execute the tool
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)

        await logger.log('TRACE', f'Tool completed: {tool_name}', 'dewey-mcp', data={'success': True})

        # Format result for MCP protocol
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    except tools.ToolError as e:
        await logger.log('ERROR', f'Tool error: {tool_name}', 'dewey-mcp', data={'error': str(e), 'code': e.code})
        raise

    except Exception as e:
        await logger.log('ERROR', f'Tool execution failed: {tool_name}', 'dewey-mcp', data={'error': str(e), 'type': type(e).__name__})
        raise tools.ToolError(f"Tool execution failed: {str(e)}", code=-32603)


# Create tool handlers dictionary
# Note: We need to use a factory function to capture tool_name correctly in closure
def make_handler(tn):
    async def handler(**args):
        return await wrap_tool_handler(tn, **args)
    return handler

TOOL_HANDLERS = {
    tool_name: make_handler(tool_name)
    for tool_name in TOOL_DEFINITIONS.keys()
}


async def main():
    """Main entry point for Dewey MCP Server."""
    # Initialize async database
    await db_pool.initialize()

    await logger.log('INFO', 'Dewey MCP server starting', 'dewey-mcp', data={'version': '1.0.0'})

    # Create joshua_network.Server instance
    server = Server(
        name="dewey-mcp-server",
        version="1.0.0",
        port=config.MCP_PORT,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    # Start the server
    await server.start()

    await logger.log('INFO', 'Dewey MCP server operational', 'dewey-mcp', data={'host': config.MCP_HOST, 'port': config.MCP_PORT})

    # Run forever
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        await logger.log('INFO', 'Dewey MCP server shutting down', 'dewey-mcp')
    finally:
        await server.stop()
        await db_pool.close()
        await logger.log('INFO', 'Dewey MCP server stopped', 'dewey-mcp')


if __name__ == "__main__":
    asyncio.run(main())
