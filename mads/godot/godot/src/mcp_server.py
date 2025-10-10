#!/usr/bin/env python3
"""
Godot MCP Server using joshua_network library
Provides logging and conversation storage tools
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as redis
from joshua_logger import Logger

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')
from joshua_network import Server as MCPServer
import config
from mcp_client import MCPClient
from database import db_pool

logger = Logger()

# Global instances
redis_client = None
dewey_client = None


# Tool implementations
async def logger_log_impl(component: str, level: str, message: str, trace_id: str = None, data: dict = None):
    """Push a log entry to the Redis queue"""
    log_entry = {
        "component": component,
        "level": level.upper(),
        "message": message,
        "trace_id": trace_id,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await redis_client.lpush(config.LOG_QUEUE_NAME, json.dumps(log_entry))
    await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)
    return {"status": "ok", "message": "Log entry queued."}


async def logger_query_impl(trace_id: str = None, component: str = None, level: str = None,
                            start_time: str = None, end_time: str = None, limit: int = 100):
    """Proxy to dewey_query_logs"""
    args = {}
    if trace_id: args['trace_id'] = trace_id
    if component: args['component'] = component
    if level: args['level'] = level
    if start_time: args['start_time'] = start_time
    if end_time: args['end_time'] = end_time
    args['limit'] = limit
    return await dewey_client.call_tool("dewey_query_logs", args)


async def logger_clear_impl(component: str = None, before_time: str = None):
    """Proxy to dewey_clear_logs"""
    args = {}
    if component: args['component'] = component
    if before_time: args['before_time'] = before_time
    return await dewey_client.call_tool("dewey_clear_logs", args)


async def logger_set_level_impl(component: str, level: str):
    """Set log level for a component"""
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    level_upper = level.upper()
    if level_upper not in valid_levels:
        raise ValueError(f"Invalid log level '{level}'. Must be one of {valid_levels}")
    await redis_client.hset("logger_config:levels", component, level_upper)
    return {"status": "ok", "component": component, "level": level_upper}


async def conversation_begin_impl(session_id: str = None, metadata: dict = None):
    """Start a new conversation and return its ID"""
    sql = """
        INSERT INTO conversations (session_id, metadata)
        VALUES ($1, $2)
        RETURNING id, session_id, created_at;
    """
    try:
        async with db_pool.transaction() as conn:
            result = await conn.fetchrow(sql, session_id, json.dumps(metadata) if metadata else None)
        return {
            "conversation_id": str(result['id']),
            "session_id": result['session_id'],
            "created_at": result['created_at'].isoformat()
        }
    except Exception as e:
        await logger.log("ERROR", f"Error in conversation_begin: {e}", "godot-mcp-server")
        raise ValueError("Failed to begin conversation")


async def conversation_store_message_impl(conversation_id: str, role: str, content: str, turn_number: int = None, metadata: dict = None):
    """Store a single message in a conversation"""
    try:
        conv_id = UUID(conversation_id)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid UUID format for conversation_id: {conversation_id}")

    if role not in ('user', 'assistant', 'system', 'tool'):
        raise ValueError("Invalid role. Must be one of 'user', 'assistant', 'system', 'tool'")

    try:
        async with db_pool.transaction() as conn:
            check = await conn.fetchval("SELECT 1 FROM conversations WHERE id = $1 FOR UPDATE;", conv_id)
            if check is None:
                raise ValueError(f"Conversation with id '{conversation_id}' not found")

            if turn_number is None:
                turn_number = await conn.fetchval(
                    "SELECT COALESCE(MAX(turn_number), 0) + 1 FROM messages WHERE conversation_id = $1;",
                    conv_id
                )

            sql = """
                INSERT INTO messages (conversation_id, turn_number, role, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, turn_number, created_at;
            """
            result = await conn.fetchrow(sql, conv_id, turn_number, role, content, json.dumps(metadata) if metadata else None)
            await conn.execute("UPDATE conversations SET updated_at = NOW() WHERE id = $1;", conv_id)

        return {
            "message_id": str(result['id']),
            "conversation_id": conversation_id,
            "turn_number": result['turn_number'],
            "created_at": result['created_at'].isoformat()
        }
    except Exception as e:
        await logger.log("ERROR", f"Error in conversation_store_message: {e}", "godot-mcp-server")
        raise ValueError(f"Failed to store message: {e}")


async def conversation_store_messages_bulk_impl(messages: list = None, messages_file: str = None, conversation_id: str = None, session_id: str = None, metadata: dict = None):
    """Store multiple messages in a single transaction"""
    if messages_file:
        import os
        if not os.path.exists(messages_file):
            raise ValueError(f"File not found: {messages_file}")
        try:
            with open(messages_file, 'r') as f:
                first_char = f.read(1)
                f.seek(0)
                if first_char == '[':
                    messages = json.load(f)
                elif first_char == '{':
                    messages = []
                    for line in f:
                        line = line.strip()
                        if line:
                            messages.append(json.loads(line))
                else:
                    raise ValueError(f"Unrecognized file format (must start with '[' or '{{')")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in messages_file: {e}")

    if not isinstance(messages, list) or not messages:
        raise ValueError("Parameter 'messages' (or messages_file content) must be a non-empty list.")

    # Extract session_id from messages if not provided
    if not session_id and messages:
        for msg in messages:
            if 'sessionId' in msg and msg['sessionId']:
                session_id = msg['sessionId']
                await logger.log("INFO", f"Extracted session_id from message: {session_id}", "godot-mcp-server")
                break
            elif isinstance(msg.get('metadata'), dict) and 'sessionId' in msg['metadata']:
                session_id = msg['metadata']['sessionId']
                await logger.log("INFO", f"Extracted session_id from metadata: {session_id}", "godot-mcp-server")
                break
        if not session_id:
            await logger.log("WARN", "Could not extract session_id from messages", "godot-mcp-server")

    # Normalize messages
    for i, msg in enumerate(messages):
        if 'message' in msg and isinstance(msg['message'], dict):
            role = msg['message'].get('role', 'NA')
            content = msg['message'].get('content', 'NA')
            messages[i] = {
                'role': role,
                'content': json.dumps(content) if isinstance(content, (list, dict)) else str(content),
                'metadata': msg
            }
        elif 'role' in msg and 'content' in msg:
            content = msg.get('content')
            if isinstance(content, (list, dict)):
                messages[i]['content'] = json.dumps(content)
        else:
            messages[i] = {
                'role': 'system',
                'content': msg.get('type', 'unknown'),
                'metadata': msg
            }

    try:
        async with db_pool.transaction() as conn:
            if conversation_id:
                conv_id = UUID(conversation_id)
                check = await conn.fetchval("SELECT 1 FROM conversations WHERE id = $1 FOR UPDATE;", conv_id)
                if check is None:
                    raise ValueError(f"Conversation with id '{conversation_id}' not found.")
            else:
                conv_id = await conn.fetchval(
                    "INSERT INTO conversations (session_id, metadata) VALUES ($1, $2) RETURNING id;",
                    session_id, json.dumps(metadata) if metadata else None
                )

            base_turn_number = await conn.fetchval(
                "SELECT COALESCE(MAX(turn_number), 0) FROM messages WHERE conversation_id = $1;",
                conv_id
            ) or 0

            insert_values = []
            for idx, msg in enumerate(messages, start=1):
                insert_values.append((
                    conv_id,
                    base_turn_number + idx,
                    msg.get('role', 'user'),
                    msg.get('content', ''),
                    json.dumps(msg.get('metadata')) if msg.get('metadata') else None
                ))

            await conn.executemany(
                "INSERT INTO messages (conversation_id, turn_number, role, content, metadata) VALUES ($1, $2, $3, $4, $5);",
                insert_values
            )
            await conn.execute("UPDATE conversations SET updated_at = NOW() WHERE id = $1;", conv_id)
            stored_count = len(insert_values)

        await logger.log("INFO", f"Stored {stored_count} messages in conversation {conv_id}", "godot-mcp-server")
        return {
            "conversation_id": str(conv_id),
            "messages_stored": stored_count,
            "status": "success"
        }
    except Exception as e:
        await logger.log("ERROR", f"Error in conversation_store_messages_bulk: {e}", "godot-mcp-server")
        raise ValueError(f"Failed to store messages in bulk: {e}")


# Tool definitions
TOOL_DEFINITIONS = {
    "godot_logger_log": {
        "description": "Push a log entry to the logging queue",
        "inputSchema": {
            "type": "object",
            "properties": {
                "component": {"type": "string"},
                "level": {"type": "string", "enum": ["ERROR", "WARN", "INFO", "DEBUG", "TRACE"]},
                "message": {"type": "string"},
                "trace_id": {"type": "string"},
                "data": {"type": "object"}
            },
            "required": ["component", "level", "message"]
        }
    },
    "godot_logger_query": {
        "description": "Query logs from storage (proxies to Dewey)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trace_id": {"type": "string"},
                "component": {"type": "string"},
                "level": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "limit": {"type": "integer", "default": 100}
            }
        }
    },
    "godot_logger_clear": {
        "description": "Clear logs from storage (proxies to Dewey)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "component": {"type": "string"},
                "before_time": {"type": "string"}
            }
        }
    },
    "godot_logger_set_level": {
        "description": "Set log level for a component",
        "inputSchema": {
            "type": "object",
            "properties": {
                "component": {"type": "string"},
                "level": {"type": "string", "enum": ["ERROR", "WARN", "INFO", "DEBUG", "TRACE"]}
            },
            "required": ["component", "level"]
        }
    },
    "godot_conversation_begin": {
        "description": "Start a new conversation and return its ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
    },
    "godot_conversation_store_message": {
        "description": "Store a single message in a conversation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string"},
                "role": {"type": "string"},
                "content": {"type": "string"},
                "turn_number": {"type": "integer"},
                "metadata": {"type": "object"}
            },
            "required": ["conversation_id", "role", "content"]
        }
    },
    "godot_conversation_store_messages_bulk": {
        "description": "Store multiple messages at once",
        "inputSchema": {
            "type": "object",
            "properties": {
                "messages": {"type": "array"},
                "messages_file": {"type": "string"},
                "conversation_id": {"type": "string"},
                "session_id": {"type": "string"},
                "metadata": {"type": "object"}
            }
        }
    }
}

# Tool handlers
TOOL_HANDLERS = {
    "godot_logger_log": lambda **kwargs: logger_log_impl(**kwargs),
    "godot_logger_query": lambda **kwargs: logger_query_impl(**kwargs),
    "godot_logger_clear": lambda **kwargs: logger_clear_impl(**kwargs),
    "godot_logger_set_level": lambda **kwargs: logger_set_level_impl(**kwargs),
    "godot_conversation_begin": lambda **kwargs: conversation_begin_impl(**kwargs),
    "godot_conversation_store_message": lambda **kwargs: conversation_store_message_impl(**kwargs),
    "godot_conversation_store_messages_bulk": lambda **kwargs: conversation_store_messages_bulk_impl(**kwargs)
}


async def main():
    """Main entry point for Godot MCP Server"""
    global redis_client, dewey_client

    # Initialize database pool
    await db_pool.initialize()
    await logger.log("INFO", "Database pool initialized", "godot-mcp-server")

    # Initialize Redis client
    redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
    await logger.log("INFO", "Redis client initialized", "godot-mcp-server")

    # Initialize Dewey MCP client
    dewey_client = MCPClient(config.DEWEY_MCP_URL, timeout=config.DEWEY_CONNECT_TIMEOUT)
    await logger.log("INFO", "Dewey MCP client initialized", "godot-mcp-server")

    # Create and start MCP server using iccm-network library
    server = MCPServer(
        name="godot-mcp-server",
        version="1.0.0",
        port=config.MCP_PORT,
        tool_definitions=TOOL_DEFINITIONS,
        tool_handlers=TOOL_HANDLERS
    )

    await logger.log("INFO", f"Godot MCP Server starting on port {config.MCP_PORT}", "godot-mcp-server")
    await logger.log("INFO", f"Tools available: {list(TOOL_DEFINITIONS.keys())}", "godot-mcp-server")

    try:
        await server.start()
    except KeyboardInterrupt:
        await logger.log("INFO", "Shutting down...", "godot-mcp-server")
    finally:
        if redis_client:
            await redis_client.close()
        await db_pool.close()
        await logger.log("INFO", "Godot MCP server stopped", "godot-mcp-server")


if __name__ == "__main__":
    asyncio.run(main())
