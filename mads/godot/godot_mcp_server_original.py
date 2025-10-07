import asyncio
import json
import logging
import time
import redis.asyncio as redis
from mcp_tools.mcp_server import MCPServer
from mcp_tools.mcp_client import MCPClient
import src.config as config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [MCP_SERVER] %(message)s')

redis_client = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)
dewey_client = MCPClient(config.DEWEY_MCP_URL)

async def logger_log(component: str, level: str, message: str, trace_id: str = None, data: dict = None):
    """Facade tool to push a single log entry to the Redis queue"""
    log_entry = {
        "component": component,
        "level": level.upper(),
        "message": message,
        "trace_id": trace_id,
        "data": data,
        "created_at": time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime())
    }
    # REQ-GOD-001: Push to Redis queue
    await redis_client.lpush(config.LOG_QUEUE_NAME, json.dumps(log_entry))
    # REQ-GOD-005: Enforce queue size limit immediately
    await redis_client.ltrim(config.LOG_QUEUE_NAME, 0, config.MAX_QUEUE_SIZE - 1)
    return {"status": "ok", "message": "Log entry queued."}

async def logger_query(**kwargs):
    """Facade tool that calls dewey_query_logs"""
    logging.info(f"Forwarding query to Dewey: {kwargs}")
    return await dewey_client.call_tool("dewey_query_logs", kwargs)

async def logger_clear(**kwargs):
    """Facade tool that calls dewey_clear_logs"""
    logging.info(f"Forwarding clear command to Dewey: {kwargs}")
    return await dewey_client.call_tool("dewey_clear_logs", kwargs)

async def logger_set_level(component: str, level: str):
    """
    Sets the log level for a component.
    Stores config in Redis hash for central management.
    """
    valid_levels = {'ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE'}
    if level.upper() not in valid_levels:
        raise ValueError(f"Invalid log level '{level}'. Must be one of {valid_levels}")

    await redis_client.hset("logger_config:levels", component, level.upper())
    return {"status": "ok", "message": f"Log level for '{component}' set to '{level.upper()}'."}

async def main():
    logging.info("Starting Godot MCP Server...")
    logging.info(f"Connecting to Dewey at {config.DEWEY_MCP_URL}")
    await dewey_client.connect()
    logging.info("Connected to Dewey.")

    server = MCPServer()
    server.register_tool(logger_log)
    server.register_tool(logger_query)
    server.register_tool(logger_clear)
    server.register_tool(logger_set_level)

    logging.info(f"Godot MCP server listening on port {config.MCP_PORT}")
    await server.start(port=config.MCP_PORT)

if __name__ == "__main__":
    asyncio.run(main())
