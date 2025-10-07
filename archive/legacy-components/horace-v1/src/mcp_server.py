# src/mcp_server.py
import asyncio
import json
import signal
from http import HTTPStatus

import websockets
from websockets.server import serve
from websockets.http import Headers

from .config import config, Config
from .database import Database
from .tools import Tools
from .utils.logger import logger, godot_info, godot_error
from .exceptions import HoraceError, DuplicateFileError

db = Database()
tools: Tools

async def health_check(path: str, request_headers: Headers):
    if path == "/health":
        return HTTPStatus.OK, [], b"OK\n"

async def mcp_handler(websocket):
    client_addr = websocket.remote_address
    logger.info(f"Client connected: {client_addr}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                tool_name = data.get("tool")
                params = data.get("params", {})

                if not tool_name or not hasattr(tools, tool_name):
                    raise HoraceError(f"Tool '{tool_name}' not found.", "TOOL_NOT_FOUND")

                logger.info(f"Executing tool: {tool_name}")
                tool_func = getattr(tools, tool_name)
                result = await tool_func(params)

                response = {"status": "success", "data": result}

            except DuplicateFileError as e:
                response = {
                    "status": "success", # Per spec, return existing ID
                    "message": e.message,
                    "data": {"file_id": e.file_id}
                }
            except HoraceError as e:
                await godot_error(f"Horace Error in tool {data.get('tool', 'unknown')}: {e.message}", context={"error_code": e.error_code, "params": data.get('params')})
                response = {"status": "error", "error": {"code": e.error_code, "message": e.message}}
            except Exception as e:
                await godot_error(f"Unhandled exception in tool {data.get('tool', 'unknown')}: {e}", context={"params": data.get('params')})
                response = {"status": "error", "error": {"code": "INTERNAL_SERVER_ERROR", "message": str(e)}}

            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client disconnected: {client_addr} - {e.code} {e.reason}")
    except Exception as e:
        logger.error(f"An error occurred in the handler for {client_addr}: {e}")
        
async def main():
    global tools
    
    # Initialize storage directories
    Config.initialize_storage_dirs()
    logger.info("Storage directories initialized.")

    # Initialize database connection
    await db.connect()
    tools = Tools(db)
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    async with serve(
        mcp_handler, 
        config.MCP_HOST, 
        config.MCP_PORT, 
        process_request=health_check
    ):
        logger.info(f"Horace MCP Server started at ws://{config.MCP_HOST}:{config.MCP_PORT}")
        await godot_info("Horace MCP Server started.")
        await stop

async def shutdown():
    logger.info("Horace MCP Server shutting down...")
    await godot_info("Horace MCP Server shutting down.")
    await db.disconnect()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received exit signal.")
    finally:
        asyncio.run(shutdown())
